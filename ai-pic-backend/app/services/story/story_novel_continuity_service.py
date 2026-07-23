"""Layered local-window and global continuity review for long novels."""

from __future__ import annotations

import json
from typing import Awaitable, Callable

from app.utils.json_utils import extract_json_block
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_domain import active_chapters
from .story_novel_generation_context import revision_local_candidates

GenerateText = Callable[..., Awaitable[str]]
GLOBAL_REVIEW_MAX_TOKENS = 16_000


def _prompt(label: str, payload: dict, *, issue_limit: int) -> str:
    return f"""你是中文长篇小说连续性审校员。检查时间、地点、角色知识、关系、能力、
世界规则、因果、伏笔、重复情节、角色弧与节奏。{label}
输入：{json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)}
issues 最多 {issue_limit} 条，只保留可执行且不重复的问题；summary、message、suggestion
都必须简洁，每项 message 和 suggestion 各不超过 160 个中文字符。
只输出严格 JSON：
{{"summary":"结论","issues":[{{"id":"stable-id","severity":"blocking|warning","chapter_business_ids":["id"],"message":"问题","suggestion":"修复建议"}}]}}
只有破坏叙事或后续改编的矛盾才标 blocking。"""


def _normalize_report(text: str, prefix: str) -> dict:
    report = extract_json_block(text)
    if not report or not isinstance(report.get("issues"), list):
        raise HTTPException(status_code=500, detail="连续性检查返回格式无效")
    issues = []
    for index, raw in enumerate(report["issues"], start=1):
        item = dict(raw) if isinstance(raw, dict) else {"message": str(raw)}
        source_id = str(item.get("id") or index)
        item["id"] = f"{prefix}-{source_id}"
        item["severity"] = (
            "blocking" if item.get("severity") == "blocking" else "warning"
        )
        item["chapter_business_ids"] = list(item.get("chapter_business_ids") or [])
        issues.append(item)
    return {"summary": str(report.get("summary") or ""), "issues": issues}


def _windows(chapters: list) -> list[list]:
    if len(chapters) <= 3:
        return [chapters]
    return [chapters[index : index + 3] for index in range(0, len(chapters), 2)]


async def run_layered_continuity(service, revision, task, generate_text: GenerateText):
    if revision.lifecycle_status != "draft":
        raise HTTPException(status_code=409, detail="仅草稿可执行连续性检查")
    chapters = active_chapters(revision)
    if len(chapters) != int(revision.chapter_count or 0):
        raise HTTPException(status_code=409, detail="章节尚未全部生成")
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    if any(
        (ledger_rows.get(str(row.position)) or {}).get("extraction_status") != "ready"
        or (ledger_rows.get(str(row.position)) or {}).get("source_hash")
        != novel_chapter_source_hash(row)
        for row in chapters
    ):
        raise HTTPException(status_code=409, detail="章节事实或记忆提取尚未完成")
    revision.continuity_status = "checking"
    service.db.commit()
    window_reports = []
    for index, rows in enumerate(_windows(chapters), start=1):
        task.description = f"正在检查相邻章节窗口 {index}/{len(_windows(chapters))}…"
        service.db.commit()
        payload = {
            "story_contract": revision.story_snapshot or {},
            "chapters": [
                {
                    "business_id": row.business_id,
                    "content_hash": row.content_hash,
                    "position": row.position,
                    "title": row.title,
                    "content": row.content_text,
                }
                for row in rows
            ],
        }
        report = _normalize_report(
            await generate_text(
                revision,
                _prompt("这是相邻章节全文窗口检查。", payload, issue_limit=12),
                max_tokens=5000,
            ),
            f"window-{index}",
        )
        window_reports.append(
            {
                "chapter_business_ids": [row.business_id for row in rows],
                **report,
            }
        )

    events, memories = revision_local_candidates(
        service.db, revision, len(chapters) + 1
    )
    global_payload = {
        "story_contract": revision.story_snapshot or {},
        "generation_plan": revision.generation_plan or {},
        "chapters": [
            {
                "business_id": row.business_id,
                "content_hash": row.content_hash,
                "position": row.position,
                "title": row.title,
                "summary": row.summary,
                "cliffhanger": row.cliffhanger,
                "plot_delta": (ledger_rows.get(str(row.position)) or {}).get(
                    "plot_delta"
                ),
            }
            for row in chapters
        ],
        "facts": events,
        "character_memories": memories,
        "rolling_state": (revision.continuity_ledger or {}).get("current_state"),
        "window_findings": window_reports,
    }
    task.description = "正在综合全书摘要、事实、角色状态与未闭合线索…"
    service.db.commit()
    global_report = _normalize_report(
        await generate_text(
            revision,
            _prompt("这是覆盖全书的综合检查。", global_payload, issue_limit=40),
            max_tokens=GLOBAL_REVIEW_MAX_TOKENS,
        ),
        "global",
    )
    issues = [
        item for report in window_reports for item in report["issues"]
    ] + global_report["issues"]
    coverage = [
        {
            "business_id": row.business_id,
            "content_hash": row.content_hash,
            "position": row.position,
        }
        for row in chapters
    ]
    revision.continuity_report = {
        "schema": "story_novel_continuity_review.v2",
        "summary": global_report["summary"],
        "coverage": coverage,
        "window_reports": window_reports,
        "issues": issues,
    }
    revision.continuity_status = (
        "failed" if any(item["severity"] == "blocking" for item in issues) else "passed"
    )
    if revision.continuity_status == "passed":
        for row in chapters:
            row.review_status = "ready"
    service.db.commit()
    return revision.continuity_report
