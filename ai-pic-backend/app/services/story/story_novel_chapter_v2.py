"""Canon/state-gated chapter generation for generation-plan v2."""

from __future__ import annotations

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_chapter_checkpoint import (
    checkpoint_gated_result,
    fail_gate,
    finalize_state,
    pause_state_pending,
)
from .story_novel_chapter_gate import (
    chapter_length_range,
    generate_validated_chapter,
    non_whitespace_chars,
)
from .story_novel_domain import active_chapters
from .story_novel_generation_context import build_chapter_context
from .story_novel_prose_canon_gate import revision_prose_canon_violations
from .story_novel_state_pending import resume_pending_state
from .story_novel_state_pending_preflight import pending_checkpoint_reusable


async def generate_or_resume_v2(
    service,
    revision,
    task,
    chapter_plan: dict,
    generate_text,
    *,
    force: bool = False,
):
    from .story_novel_chapter_service import chapter_entry
    from .story_novel_task_guard import ensure_task_not_cancelled

    position = int(chapter_plan["position"])
    existing = next(
        (item for item in active_chapters(revision) if item.position == position), None
    )
    context_pack = build_chapter_context(service, revision, position, chapter_plan)
    entry = chapter_entry(revision, position)
    resumed = await _resume_checkpoint(
        service,
        revision,
        task,
        position,
        existing,
        entry,
        context_pack,
        chapter_plan,
        generate_text,
        force,
    )
    if resumed:
        return resumed
    task.description = f"正在生成并验证第 {position}/{revision.chapter_count} 章…"
    service.db.commit()
    gated = await generate_validated_chapter(
        revision,
        chapter_plan=chapter_plan,
        context_pack=context_pack,
        generate_text=generate_text,
    )
    ensure_task_not_cancelled(service.db, task)
    return await _checkpoint_new_body(
        service,
        revision,
        task,
        position,
        chapter_plan,
        context_pack["evidence"],
        existing,
        gated,
    )


async def _resume_checkpoint(
    service,
    revision,
    task,
    position,
    existing,
    entry,
    context_pack,
    plan,
    generate_text,
    force,
):
    from .story_novel_chapter_service import ensure_chapter_extraction
    from .story_novel_state_service import replay_checkpoint_state

    if entry.get("status") == "state_pending" and not force:
        if not pending_checkpoint_reusable(
            revision, existing, entry, context_pack, plan
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"第 {position} 章的待恢复状态与当前计划不一致；"
                    "正文未改写，请显式重新生成该章"
                ),
            )
        return await resume_pending_state(
            service,
            revision,
            task,
            position,
            existing,
            entry,
            context_pack,
            plan,
            generate_text,
        )

    evidence = context_pack["evidence"]
    minimum, _target, maximum = chapter_length_range(plan)
    reusable = (
        existing
        and minimum <= non_whitespace_chars(existing.content_text) <= maximum
        and entry.get("status") in {"body_ready", "ready"}
        and entry.get("body_hash") == existing.content_hash
        and entry.get("source_hash") == novel_chapter_source_hash(existing)
        and entry.get("context_hash") == evidence["context_hash"]
        and entry.get("canon_hash") == evidence["canon_hash"]
        and entry.get("state_before_hash") == evidence["state_before_hash"]
        and (entry.get("state_validation") or {}).get("status") == "passed"
        and entry.get("plot_delta_source") == "typed_state"
        and entry.get("plot_delta_version") == 1
        and replay_checkpoint_state(context_pack["state_before"], entry) is not None
        and not revision_prose_canon_violations(revision, plan, existing.content_text)
        and not force
    )
    if not reusable:
        if existing is not None and entry.get("status") == "ready" and not force:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"第 {position} 章 ready checkpoint 与当前计划或上下文不一致；"
                    "正文未改写，请显式重新生成该章"
                ),
            )
        if existing is not None or entry:
            _stale_unusable_checkpoint(service, revision, position, existing)
        return None
    task.description = f"第 {position} 章状态有效，正在校验事实与记忆…"
    service.db.commit()
    entry = await ensure_chapter_extraction(service, revision, existing, task)
    finalize_state(service, revision, position, entry)
    return existing


def _stale_unusable_checkpoint(service, revision, position: int, existing) -> None:
    from .story_novel_chapter_service import sync_plan_chapter_runtime
    from .story_novel_memory_context import (
        invalidate_chapter_source,
        mark_revision_ledger_stale,
    )

    mark_revision_ledger_stale(
        revision,
        from_position=position,
        edited_chapter=existing,
    )
    service._invalidate_from(revision, position)
    ledger = dict(revision.continuity_ledger or {})
    recovery = int(ledger.get("recovery_from_position") or 0)
    if recovery >= position:
        ledger.pop("recovery_from_position", None)
        revision.continuity_ledger = ledger
    if existing is not None:
        source_hash = novel_chapter_source_hash(existing)
        invalidate_chapter_source(
            service.db,
            revision,
            existing,
            source_hash,
            force=True,
            reason_code="resume_checkpoint_invalid",
        )
    entries = (revision.continuity_ledger or {}).get("chapters") or {}
    for key, stale_entry in entries.items():
        if int(key) >= position:
            sync_plan_chapter_runtime(revision, int(key), stale_entry)
    service.db.commit()


async def _checkpoint_new_body(
    service, revision, task, position, plan, evidence, existing, gated
):
    from .story_novel_chapter_service import ensure_chapter_extraction

    result = gated.get("result")
    if not result:
        raise HTTPException(status_code=500, detail=f"第 {position} 章未返回有效正文")
    chapter, entry = checkpoint_gated_result(
        service, revision, position, result, gated, evidence, existing
    )
    if not gated["passed"]:
        if gated.get("state_extraction_evidence_only") is True:
            pause_state_pending(
                service,
                revision,
                chapter,
                position,
                entry,
                gated["state_validation"]["violations"],
            )
        fail_gate(service, revision, chapter, position, plan, gated)
    service.db.commit()
    entry = await ensure_chapter_extraction(service, revision, chapter, task)
    finalize_state(service, revision, position, entry)
    return chapter
