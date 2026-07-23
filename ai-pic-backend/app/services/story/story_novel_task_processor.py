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
)
from .story_novel_chapter_service import generate_or_resume_chapter
from .story_novel_continuity_service import run_layered_continuity
from .story_novel_domain import active_chapters
from .story_novel_export_ai import generate_story_novel_text
from .story_novel_legacy_task import run_legacy_export
from .story_novel_memory_context import mark_revision_ledger_stale
from .story_novel_planning_service import ensure_generation_plan
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


async def _generate_missing_chapters(service, revision, task, *, only_position=None):
    plan = await ensure_generation_plan(service, revision, task, _generate_text)
    plan_rows = plan["chapters"]
    if only_position is not None:
        mark_revision_ledger_stale(revision, from_position=only_position)
        for row in service.repo.chapters_from_position(revision.id, only_position + 1):
            row.review_status = "review_required"
        revision.continuity_status = "review_required"
        if revision.adaptation_plan_status != "empty":
            revision.adaptation_plan_status = "stale"
        service.db.commit()
    for row_plan in plan_rows:
        position = int(row_plan["position"])
        if only_position is not None and position != only_position:
            continue
        await generate_or_resume_chapter(
            service,
            revision,
            task,
            row_plan,
            _generate_text,
            force=only_position is not None,
        )
    ledger = dict(revision.continuity_ledger or {})
    ledger["state_status"] = "ready"
    revision.continuity_ledger = ledger
    service.db.commit()


async def _run_continuity(service, revision, task):
    await run_layered_continuity(service, revision, task, _generate_text)


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
