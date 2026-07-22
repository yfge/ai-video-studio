from __future__ import annotations

from functools import partial
from typing import Any

import anyio
from app.core.database import SessionLocal
from app.models.task import TaskStatus
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.story_novel_export import AdaptationPlanEpisode
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException

from .story_novel_ai_prompts import (
    SYSTEM_PROMPT,
    adaptation_prompt,
    chapter_prompt,
    continuity_prompt,
)
from .story_novel_domain import active_chapters, compact_chapter_context
from .story_novel_export_ai import generate_story_novel_text
from .story_novel_legacy_task import run_legacy_export
from .story_novel_revision_service import StoryNovelRevisionService


def _split_model(model_id: str | None) -> tuple[str | None, str | None]:
    if model_id and ":" in model_id:
        return tuple(model_id.split(":", 1))  # type: ignore[return-value]
    return None, model_id


async def _generate_text(revision, prompt: str, *, max_tokens: int | None) -> str:
    provider, model = _split_model(revision.model)
    return await generate_story_novel_text(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        model=model,
        prefer_provider=provider,
        temperature=revision.temperature or 0.7,
        max_tokens=max_tokens,
    )


def _chapter_result(text: str, fallback_title: str) -> dict[str, str | None]:
    parsed = extract_json_block(text) or {}
    content = str(parsed.get("content_text") or parsed.get("content") or text).strip()
    if not content:
        raise HTTPException(status_code=500, detail="章节生成结果为空")
    return {
        "title": str(parsed.get("title") or fallback_title),
        "content_text": content,
        "summary": str(parsed.get("summary") or content[:300]),
        "cliffhanger": (
            str(parsed.get("cliffhanger")) if parsed.get("cliffhanger") else None
        ),
    }


async def _generate_missing_chapters(service, revision, task, *, only_position=None):
    plan = revision.generation_plan or {}
    plan_rows = plan.get("chapters") or []
    existing = {row.position: row for row in active_chapters(revision)}
    target = int(revision.chapter_count or len(plan_rows) or 3)
    per_chapter = max(800, int(revision.target_words / target))
    for position in range(1, target + 1):
        if only_position is None and position in existing:
            continue
        if only_position is not None and position != only_position:
            continue
        row_plan = next(
            (row for row in plan_rows if int(row.get("position") or 0) == position),
            {"position": position, "title": f"第{position}章"},
        )
        task.description = f"正在生成第 {position}/{target} 章…"
        service.db.commit()
        text = await _generate_text(
            revision,
            chapter_prompt(
                snapshot=revision.story_snapshot or {},
                chapter_plan=row_plan,
                previous=compact_chapter_context(revision, position),
                target_words=per_chapter,
            ),
            max_tokens=min(16000, max(2500, per_chapter * 2)),
        )
        result = _chapter_result(text, str(row_plan.get("title") or f"第{position}章"))
        service.checkpoint_chapter(revision, position=position, **result)
    if only_position is not None:
        for row in service.repo.chapters_from_position(revision.id, only_position + 1):
            row.review_status = "review_required"
        revision.continuity_status = "review_required"
        if revision.adaptation_plan_status != "empty":
            revision.adaptation_plan_status = "stale"
        service.db.commit()


async def _run_continuity(service, revision, task):
    if revision.lifecycle_status != "draft":
        raise HTTPException(status_code=409, detail="仅草稿可执行连续性检查")
    chapters = [
        {
            "business_id": row.business_id,
            "position": row.position,
            "title": row.title,
            "content": row.content_text,
        }
        for row in active_chapters(revision)
    ]
    revision.continuity_status = "checking"
    service.db.commit()
    text = await _generate_text(
        revision,
        continuity_prompt(snapshot=revision.story_snapshot or {}, chapters=chapters),
        max_tokens=5000,
    )
    report = extract_json_block(text)
    if not report or not isinstance(report.get("issues", []), list):
        raise HTTPException(status_code=500, detail="连续性检查返回格式无效")
    issues = []
    for index, raw in enumerate(report.get("issues") or [], start=1):
        item = dict(raw) if isinstance(raw, dict) else {"message": str(raw)}
        item["id"] = str(item.get("id") or f"issue-{index}")
        item["severity"] = (
            "blocking" if item.get("severity") == "blocking" else "warning"
        )
        issues.append(item)
    report["issues"] = issues
    revision.continuity_report = report
    revision.continuity_status = (
        "failed" if any(row["severity"] == "blocking" for row in issues) else "passed"
    )
    if revision.continuity_status == "passed":
        for row in active_chapters(revision):
            row.review_status = "ready"
    service.db.commit()


async def _generate_adaptation(service, revision):
    if (
        revision.lifecycle_status != "approved"
        or revision.story.canonical_novel_export_id != revision.id
    ):
        raise HTTPException(status_code=409, detail="仅当前已审批小说可生成改编计划")
    if revision.adaptation_plan_status in {"approved", "applied"}:
        raise HTTPException(status_code=409, detail="已审批或已应用计划不可重新生成")
    chapters = [
        {
            "business_id": row.business_id,
            "position": row.position,
            "title": row.title,
            "summary": row.summary or row.content_text[:600],
            "cliffhanger": row.cliffhanger,
        }
        for row in active_chapters(revision)
    ]
    text = await _generate_text(
        revision,
        adaptation_prompt(snapshot=revision.story_snapshot or {}, chapters=chapters),
        max_tokens=8000,
    )
    parsed = extract_json_block(text) or {}
    rows = [
        AdaptationPlanEpisode.model_validate(row).model_dump()
        for row in parsed.get("episodes") or []
    ]
    if not rows:
        raise HTTPException(status_code=500, detail="改编计划返回格式无效")
    valid_ids = {row["business_id"] for row in chapters}
    if any(
        not set(row["source_chapter_business_ids"]).issubset(valid_ids) for row in rows
    ):
        raise HTTPException(status_code=500, detail="改编计划引用了不存在的章节")
    revision.adaptation_plan = {
        "version": int((revision.adaptation_plan or {}).get("version") or 0) + 1,
        "novel_content_hash": revision.content_hash,
        "episodes": rows,
    }
    revision.adaptation_plan_status = "draft"
    service.db.commit()


def process_story_novel_task(
    task_id: int, payload: dict[str, Any], user_id: int
) -> None:
    db = SessionLocal()
    repo = StoryNovelRepository(db)
    task = repo.task(task_id)
    try:
        if not task:
            return
        task.status = TaskStatus.PROCESSING
        db.commit()
        user = repo.user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        operation = str(payload.get("operation") or "legacy_export")
        if operation == "legacy_export":
            anyio.run(run_legacy_export, db, task, payload, user)
        else:
            service = StoryNovelRevisionService(db, user)
            revision = service.revision(str(payload.get("revision_business_id") or ""))
            task.target_business_id = revision.business_id
            if operation in {"generate_revision", "resume_revision"}:
                anyio.run(_generate_missing_chapters, service, revision, task)
            elif operation == "regenerate_chapter":
                anyio.run(
                    partial(
                        _generate_missing_chapters,
                        service,
                        revision,
                        task,
                        only_position=int(payload["position"]),
                    )
                )
            elif operation == "continuity_check":
                anyio.run(_run_continuity, service, revision, task)
            elif operation == "generate_adaptation_plan":
                anyio.run(_generate_adaptation, service, revision)
            else:
                raise HTTPException(status_code=400, detail="未知小说任务类型")
            task.result_file_path = f"novel_revision:{revision.business_id}"
        task.status = TaskStatus.COMPLETED
        task.description = "处理完成"
        db.commit()
    except Exception as exc:
        db.rollback()
        error_message = str(getattr(exc, "detail", None) or exc or repr(exc))
        if payload.get("operation") == "continuity_check" and "user" in locals():
            revision = repo.accessible_revision(
                str(payload.get("revision_business_id") or ""), user
            )
            if revision:
                revision.continuity_status = "failed"
                revision.continuity_report = {
                    "summary": "连续性检查执行失败",
                    "issues": [],
                    "error": error_message,
                }
        task = repo.task(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.description = "处理失败；已完成章节已保留"
            db.commit()
    finally:
        db.close()
