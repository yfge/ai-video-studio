from functools import partial
from types import SimpleNamespace

import anyio
from app.core.database import SessionLocal
from app.models.task import TaskStatus
from app.repositories.story_novel_repository import StoryNovelRepository
from app.services.providers.deepseek_models import DEEPSEEK_DEFAULT_MODEL
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException

from . import story_novel_task_guard as task_guard
from .story_novel_ai_prompts import adaptation_prompt
from .story_novel_chapter_service import generate_or_resume_chapter
from .story_novel_continuity_service import run_layered_continuity
from .story_novel_downstream_gate import (
    chapter_source_evidence,
    freeze_adaptation_plan,
    require_canonical_revision,
)
from .story_novel_legacy_task import run_legacy_export
from .story_novel_memory_context import mark_revision_ledger_stale
from .story_novel_plan_versions import is_v3_plan, is_v4_plan
from .story_novel_planning_service import ensure_generation_plan
from .story_novel_resume_cursor import advance_resume_cursor, resume_suffix_plan_rows
from .story_novel_revision_service import StoryNovelRevisionService
from .story_novel_task_generation import generate_task_text as _generate_text
from .story_seed_structure_service import structure_story_seed


async def _generate_missing_chapters(service, revision, task, *, only_position=None):
    task_guard.ensure_task_not_cancelled(service.db, task)
    generate = partial(
        task_guard.generate_text_unless_cancelled, service.db, task, _generate_text
    )
    plan = await ensure_generation_plan(
        service, revision, task, partial(generate, stage="planning")
    )
    plan_rows = plan["chapters"]
    if only_position is None and (is_v3_plan(plan) or is_v4_plan(plan)):
        plan_rows = resume_suffix_plan_rows(service, revision, plan_rows)
    if only_position is not None:
        mark_revision_ledger_stale(
            revision,
            from_position=only_position,
            archive_generation_calls=True,
        )
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
        advance_resume_cursor(revision, plan_rows)
        service.db.commit()
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


async def _run_continuity(service, revision, task, *, review_model=None):
    generate = partial(
        task_guard.generate_text_unless_cancelled,
        service.db,
        task,
        _generate_text,
        stage="continuity",
        model_override=review_model,
    )
    await run_layered_continuity(
        service, revision, task, generate, reviewer_model=review_model
    )


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


def process_story_novel_task(task_id: int, payload: dict, user_id: int) -> None:
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
    model = str(payload.get("model") or story.ai_model or "").strip()
    model = model or f"deepseek:{DEEPSEEK_DEFAULT_MODEL}"
    carrier = SimpleNamespace(model=model, temperature=0.7)
    anyio.run(
        partial(
            structure_story_seed,
            db,
            story,
            task,
            carrier,
            partial(_generate_text, stage="planning"),
            expected_version=int(payload["story_seed_version"]),
            requested_chapter_count=payload.get("chapter_count"),
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
        anyio.run(
            partial(
                _run_continuity,
                service,
                revision,
                task,
                review_model=payload.get("review_model"),
            )
        )
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
