"""Commit one chapter's extracted candidates and ledger checkpoint atomically."""

from app.core.exceptions import ConflictError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_extraction import NarrativeExtractionRequest
from app.services.narrative_memory.candidate_verification import (
    complete_novel_candidate_set,
)
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_candidate_refresh import (
    active_source_candidate_ids,
    candidate_batch_matches_source,
    extraction_checkpoint_fingerprint,
    lock_extraction_checkpoint,
    stale_replaced_candidates,
)
from .story_novel_task_guard import ensure_task_not_cancelled


async def ensure_chapter_extraction(service, revision, chapter, task=None) -> dict:
    from .story_novel_chapter_service import (
        chapter_entry,
        save_ledger_entry,
        source_candidates,
        sync_plan_chapter_runtime,
    )

    if task is not None:
        ensure_task_not_cancelled(service.db, task)
    position = chapter.position
    entry = chapter_entry(revision, position)
    source_hash = novel_chapter_source_hash(chapter)
    previous_ids = set(entry.get("event_ids") or []) | set(
        entry.get("memory_ids") or []
    )
    previous_ids.update(
        active_source_candidate_ids(
            service.db,
            revision.story_id,
            chapter.business_id,
            source_hash,
        )
    )
    events, memories = source_candidates(service.db, revision, chapter)
    ids_match = entry.get("event_ids") == [
        item.business_id for item in events
    ] and entry.get("memory_ids") == [item.business_id for item in memories]
    if (
        entry.get("extraction_status") == "ready"
        and entry.get("source_hash") == source_hash
        and ids_match
        and (
            (revision.generation_plan or {}).get("schema")
            != "story_novel_generation_plan.v2"
            or complete_novel_candidate_set(entry, events, memories)
        )
    ):
        sync_plan_chapter_runtime(revision, position, entry)
        return entry

    expected = extraction_checkpoint_fingerprint(revision, chapter)
    checkpoint_locked = False

    def lock_checkpoint() -> None:
        nonlocal checkpoint_locked
        lock_extraction_checkpoint(service, revision, chapter, task, expected)
        checkpoint_locked = True

    try:
        extracted = await NarrativeExtractionService(
            NarrativeMemoryRepository(service.db)
        ).extract(
            revision.story,
            NarrativeExtractionRequest(
                source_scope="novel_chapter",
                source_artifact_business_id=chapter.business_id,
                model=revision.model,
            ),
            service.user,
            commit=False,
            before_ingest=lock_checkpoint,
        )
        if not checkpoint_locked:
            lock_checkpoint()
        events = list(extracted.get("events") or [])
        memories = list(extracted.get("memories") or [])
        if not candidate_batch_matches_source(chapter, events, memories):
            raise ConflictError("候选提取结果不属于当前章节 checkpoint")
        if (revision.generation_plan or {}).get(
            "schema"
        ) == "story_novel_generation_plan.v2" and not complete_novel_candidate_set(
            entry, events, memories
        ):
            raise ConflictError("候选集合未完整覆盖章节事件与角色获知关系")
        replacement_ids = {item.business_id for item in [*events, *memories]}
        stale_replaced_candidates(
            service.db, revision.story_id, previous_ids, replacement_ids
        )
        entry.update(
            {
                "status": ("body_ready" if entry.get("state_validation") else "ready"),
                "body_hash": chapter.content_hash,
                "source_hash": source_hash,
                "extraction_status": "ready",
                "event_ids": [item.business_id for item in events],
                "memory_ids": [item.business_id for item in memories],
            }
        )
        save_ledger_entry(revision, position, entry)
        sync_plan_chapter_runtime(revision, position, entry)
        service.db.commit()
    except Exception:
        service.db.rollback()
        raise
    return entry
