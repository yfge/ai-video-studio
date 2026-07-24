from functools import partial
from types import SimpleNamespace
from typing import Any

import anyio
from app.core.database import SessionLocal
from app.models.task import TaskStatus
from app.repositories.story_novel_repository import StoryNovelRepository
from app.services.providers.deepseek_models import DEEPSEEK_DEFAULT_MODEL
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException

from . import story_novel_task_guard as task_guard
from .story_novel_ai_prompts import SYSTEM_PROMPT, adaptation_prompt
from .story_novel_chapter_service import generate_or_resume_chapter
from .story_novel_continuity_service import run_layered_continuity
from .story_novel_downstream_gate import (
    chapter_source_evidence,
    freeze_adaptation_plan,
    require_canonical_revision,
)
from .story_novel_export_ai import generate_story_novel_text
from .story_novel_legacy_task import run_legacy_export
from .story_novel_memory_context import mark_revision_ledger_stale
from .story_novel_planning_service import ensure_generation_plan
from .story_novel_revision_service import StoryNovelRevisionService
from .story_seed_structure_service import structure_story_seed


def _split_model(model_id: str | None) -> tuple[str | None, str | None]:
    if model_id and ":" in model_id:
        return tuple(model_id.split(":", 1))  # type: ignore[return-value]
    return None, model_id


async def _generate_text(
    revision,
    prompt: str,
    *,
    max_tokens: int | None,
    temperature: float | None = None,
) -> str:
    provider, model = _split_model(revision.model)
    chosen_temperature = (
        temperature if temperature is not None else revision.temperature or 0.7
    )
    return await generate_story_novel_text(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        model=model,
        prefer_provider=provider,
        temperature=chosen_temperature,
        max_tokens=max_tokens,
    )


async def _generate_missing_chapters(service, revision, task, *, only_position=None):
    task_guard.ensure_task_not_cancelled(service.db, task)
    generate = partial(
        task_guard.generate_text_unless_cancelled, service.db, task, _generate_text
    )
    plan = await ensure_generation_plan(service, revision, task, generate)
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
        task_guard.ensure_task_not_cancelled(service.db, task)
        position = int(row_plan["position"])
        if only_position is not None and position != only_position:
            continue
        await generate_or_resume_chapter(
            service,
            revision,
            task,
            row_plan,
            generate,
            force=only_position is not None,
        )
    task_guard.ensure_task_not_cancelled(service.db, task)
    ledger = dict(revision.continuity_ledger or {})
    entries = ledger.get("chapters") or {}
    all_ready = all(
        (entries.get(str(row["position"])) or {}).get("status") == "ready"
        for row in plan_rows
    )
    ledger["state_status"] = "ready" if all_ready else "stale"
    if all_ready:
        ledger.pop("stale_from_position", None)
    revision.continuity_ledger = ledger
    service.db.commit()


async def _run_continuity(service, revision, task):
    generate = partial(
        task_guard.generate_text_unless_cancelled, service.db, task, _generate_text
    )
    await run_layered_continuity(service, revision, task, generate)


async def _generate_adaptation(service, revision):
    generation_plan, chapter_rows = require_canonical_revision(revision)
    if revision.adaptation_plan_status in {"approved", "applied"}:
        raise HTTPException(status_code=409, detail="已审批或已应用计划不可重新生成")
    chapters = [
        {
            **chapter_source_evidence(row),
            "content_text": row.content_text,
            "cliffhanger": row.cliffhanger,
        }
        for row in chapter_rows
    ]
    text = await _generate_text(
        revision,
        adaptation_prompt(
            snapshot={
                "source_type": "approved_canonical_novel",
                "novel_revision_business_id": revision.business_id,
                "novel_content_hash": revision.content_hash,
                "generation_plan_version": generation_plan["version"],
                "generation_plan_hash": generation_plan["plan_hash"],
            },
            chapters=chapters,
        ),
        max_tokens=8000,
    )
    parsed = extract_json_block(text) or {}
    rows = parsed.get("episodes") or [] if isinstance(parsed, dict) else []
    revision.adaptation_plan = freeze_adaptation_plan(
        revision,
        version=int((revision.adaptation_plan or {}).get("version") or 0) + 1,
        rows=rows,
    )
    revision.adaptation_plan_status = "draft"
    service.db.commit()


def process_story_novel_task(
    task_id: int, payload: dict[str, Any], user_id: int
) -> None:
    db = SessionLocal()
    repo = StoryNovelRepository(db)
    task = None
    user = None
    try:
        task = repo.claim_pending_task(task_id)
        if not task:
            return
        user = repo.user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        _execute_operation(db, repo, task, payload, user)
        db.refresh(task)
        if task.status == TaskStatus.CANCELLED:
            return
        task.status = TaskStatus.COMPLETED
        task.description = "处理完成"
        db.commit()
    except task_guard.NovelTaskCancelled:
        db.rollback()
    except Exception as exc:
        db.rollback()
        error_message = str(getattr(exc, "detail", None) or exc or repr(exc))
        _record_failure(db, repo, task_id, payload, user, error_message)
    finally:
        db.close()


def _execute_operation(db, repo, task, payload, user) -> None:
    operation = str(payload.get("operation") or "legacy_export")
    if operation == "legacy_export":
        anyio.run(run_legacy_export, db, task, payload, user)
        return
    if operation == "structure_story_seed":
        _structure_seed(repo, db, task, payload, user)
        return
    service = StoryNovelRevisionService(db, user)
    revision = service.revision(str(payload.get("revision_business_id") or ""))
    task.target_business_id = revision.business_id
    _run_revision_operation(operation, service, revision, task, payload)
    task.result_file_path = f"novel_revision:{revision.business_id}"


def _structure_seed(repo, db, task, payload, user) -> None:
    story = repo.accessible_story(str(payload.get("story_business_id") or ""), user)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    model = story.ai_model or f"deepseek:{DEEPSEEK_DEFAULT_MODEL}"
    carrier = SimpleNamespace(model=model, temperature=0.7)
    anyio.run(
        partial(
            structure_story_seed,
            db,
            story,
            task,
            carrier,
            _generate_text,
            expected_version=int(payload["story_seed_version"]),
        )
    )


def _run_revision_operation(operation, service, revision, task, payload) -> None:
    if operation in {"generate_revision", "resume_revision"}:
        anyio.run(_generate_missing_chapters, service, revision, task)
    elif operation == "regenerate_chapter":
        runner = partial(
            _generate_missing_chapters,
            service,
            revision,
            task,
            only_position=int(payload["position"]),
        )
        anyio.run(runner)
    elif operation == "continuity_check":
        anyio.run(_run_continuity, service, revision, task)
    elif operation == "generate_adaptation_plan":
        anyio.run(_generate_adaptation, service, revision)
    else:
        raise HTTPException(status_code=400, detail="未知小说任务类型")


def _record_failure(db, repo, task_id, payload, user, error_message) -> None:
    if payload.get("operation") == "continuity_check" and user:
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
    if not task:
        return
    db.refresh(task)
    if task.status == TaskStatus.CANCELLED:
        return
    task.status = TaskStatus.FAILED
    task.error_message = error_message
    task.description = "处理失败；已完成章节已保留"
    db.commit()
