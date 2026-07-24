"""Layered local-window and global continuity review for long novels."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException

from .story_novel_continuity_contract import continuity_prompt as _prompt
from .story_novel_continuity_contract import (
    normalize_continuity_report as _normalize_report,
)
from .story_novel_continuity_review import (
    compile_report,
    global_payload,
    review_ready,
    window_payload,
)
from .story_novel_domain import active_chapters
from .story_novel_generation_context import revision_local_candidates
from .story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
    quality_metrics,
    state_hash,
)
from .story_novel_task_guard import ensure_task_not_cancelled

GenerateText = Callable[..., Awaitable[str]]
GLOBAL_REVIEW_MAX_TOKENS = 16_000
REVIEW_BATCH_SIZE = 6


def _windows(chapters: list) -> list[list]:
    return [
        chapters[index : index + REVIEW_BATCH_SIZE]
        for index in range(0, len(chapters), REVIEW_BATCH_SIZE)
    ]


def _require_review_ready(revision, chapters: list, ledger_rows: dict) -> None:
    if revision.lifecycle_status != "draft":
        raise HTTPException(status_code=409, detail="仅草稿可执行连续性检查")
    if len(chapters) != int(revision.chapter_count or 0):
        raise HTTPException(status_code=409, detail="章节尚未全部生成")
    if not review_ready(chapters, ledger_rows):
        raise HTTPException(status_code=409, detail="章节事实或记忆提取尚未完成")
    if (revision.generation_plan or {}).get(
        "schema"
    ) == "story_novel_generation_plan.v2":
        require_valid_state_chain(revision, chapters, ledger_rows)


async def _review_windows(
    service,
    revision,
    task,
    chapters: list,
    generate_text: GenerateText,
) -> list:
    windows = _windows(chapters)
    reports = []
    for index, rows in enumerate(windows, start=1):
        task.description = f"正在审读章节批次 {index}/{len(windows)}…"
        service.db.commit()
        text = await generate_text(
            revision,
            _prompt(
                "这是相邻章节全文窗口检查。",
                window_payload(revision, rows),
                issue_limit=12,
            ),
            max_tokens=5000,
        )
        ensure_task_not_cancelled(service.db, task)
        reports.append(
            {
                "batch_index": index,
                "chapter_business_ids": [row.business_id for row in rows],
                "chapter_refs": [
                    {
                        "business_id": row.business_id,
                        "content_hash": row.content_hash,
                        "position": row.position,
                    }
                    for row in rows
                ],
                **_normalize_report(text, f"window-{index}"),
            }
        )
    return reports


async def _review_global(
    service,
    revision,
    task,
    payload: dict,
    generate_text: GenerateText,
) -> dict:
    task.description = "正在综合全书摘要、事实、角色状态与未闭合线索…"
    service.db.commit()
    text = await generate_text(
        revision,
        _prompt(
            "这是覆盖全书的综合检查。",
            payload,
            issue_limit=40,
            include_editorial=True,
        ),
        max_tokens=GLOBAL_REVIEW_MAX_TOKENS,
    )
    ensure_task_not_cancelled(service.db, task)
    return _normalize_report(text, "global", include_editorial=True)


def _save_report(service, revision, chapters: list, report: dict) -> None:
    revision.continuity_report = report
    hard_failed = any(
        value
        for key, value in report["hard_metrics"].items()
        if key != "chapter_repair_rate"
    )
    model_failed = any(item["severity"] == "blocking" for item in report["issues"])
    revision.continuity_status = "failed" if hard_failed or model_failed else "passed"
    if revision.continuity_status == "passed":
        for row in chapters:
            row.review_status = "ready"
    service.db.commit()


async def run_layered_continuity(service, revision, task, generate_text: GenerateText):
    ensure_task_not_cancelled(service.db, task)
    chapters = active_chapters(revision)
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    _require_review_ready(revision, chapters, ledger_rows)
    revision.continuity_status = "checking"
    service.db.commit()
    window_reports = await _review_windows(
        service, revision, task, chapters, generate_text
    )
    events, memories = revision_local_candidates(
        service.db, revision, len(chapters) + 1
    )
    payload = global_payload(
        revision, chapters, ledger_rows, events, memories, window_reports
    )
    global_report = await _review_global(
        service, revision, task, payload, generate_text
    )
    metrics = quality_metrics(revision)
    report = compile_report(revision, chapters, window_reports, global_report, metrics)
    ensure_task_not_cancelled(service.db, task)
    _save_report(service, revision, chapters, report)
    return revision.continuity_report


def require_valid_state_chain(revision, chapters, ledger_rows) -> None:
    canon = (revision.generation_plan or {}).get("canon") or {}
    canon_hash = canon.get("canon_hash")
    state = initial_story_state(canon)
    for chapter in chapters:
        entry = ledger_rows.get(str(chapter.position)) or {}
        if (
            entry.get("status") != "ready"
            or entry.get("canon_hash") != canon_hash
            or (entry.get("state_validation") or {}).get("status") != "passed"
            or entry.get("state_before_hash") != state_hash(state)
            or not entry.get("state_delta")
        ):
            raise HTTPException(
                status_code=409, detail=f"第 {chapter.position} 章状态校验不完整"
            )
        state = apply_state_delta(state, entry["state_delta"])
        if entry.get("state_after_hash") != state_hash(state):
            raise HTTPException(
                status_code=409, detail=f"第 {chapter.position} 章状态 hash 不匹配"
            )
    current_state = (revision.continuity_ledger or {}).get("current_state")
    if not current_state or state_hash(current_state) != state_hash(state):
        raise HTTPException(status_code=409, detail="全书 current_state 与状态链不匹配")
