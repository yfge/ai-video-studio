"""Narrative-memory integration helpers for the novel workflow."""

from datetime import datetime, timezone

from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.generation_context_service import (
    NarrativeGenerationContextService,
)
from app.services.narrative_memory.invalidation_service import (
    NarrativeMemoryInvalidationService,
)
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException


def ensure_timestamp(actual: datetime | None, expected: datetime) -> None:
    def utc(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

    if actual and abs((utc(actual) - utc(expected)).total_seconds()) > 0.001:
        raise HTTPException(status_code=409, detail="内容已被其他窗口更新")


def chapter_memory_context(db, revision, position: int):
    return NarrativeGenerationContextService(
        NarrativeMemoryRepository(db)
    ).chapter_context(
        revision.story,
        revision_business_id=revision.business_id,
        position=position,
    )


def capture_chapter_source_hashes(chapters) -> dict[str, str]:
    return {item.business_id: novel_chapter_source_hash(item) for item in chapters}


def invalidate_chapter_source(
    db,
    revision,
    chapter,
    source_before_hash: str,
    *,
    force: bool = False,
    reason_code: str = "source_hash_changed",
):
    return NarrativeMemoryInvalidationService(
        NarrativeMemoryRepository(db)
    ).mark_source_changed(
        revision.story,
        artifact_business_id=chapter.business_id,
        source_before_hash=source_before_hash,
        source_after_hash=novel_chapter_source_hash(chapter),
        force=force,
        reason_code=reason_code,
        commit=False,
    )


def invalidate_reordered_chapters(db, revision, chapters, source_before) -> None:
    for chapter in chapters:
        invalidate_chapter_source(
            db, revision, chapter, source_before[chapter.business_id]
        )


def invalidate_revision_candidates(db, revision) -> None:
    invalidator = NarrativeMemoryInvalidationService(NarrativeMemoryRepository(db))
    for chapter in revision.chapters:
        source_hash = novel_chapter_source_hash(chapter)
        invalidator.mark_source_changed(
            revision.story,
            artifact_business_id=chapter.business_id,
            source_before_hash=source_hash,
            source_after_hash=source_hash,
            force=True,
            reason_code="generation_plan_recompiled",
            commit=False,
        )


def mark_revision_ledger_stale(
    revision,
    *,
    from_position: int,
    edited_chapter=None,
) -> None:
    ledger = dict(revision.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    for key, raw in list(chapters.items()):
        if int(key) < from_position:
            continue
        entry = dict(raw)
        entry["status"] = "stale"
        entry["extraction_status"] = "stale"
        if edited_chapter is not None and int(key) == edited_chapter.position:
            entry["body_hash"] = edited_chapter.content_hash
            entry["source_hash"] = novel_chapter_source_hash(edited_chapter)
            entry["event_ids"] = []
            entry["memory_ids"] = []
            if (revision.generation_plan or {}).get("schema") != (
                "story_novel_generation_plan.v2"
            ):
                entry["status"] = "body_ready"
            else:
                entry["state_delta"] = None
                entry["state_after"] = None
                entry["state_after_hash"] = None
                entry["state_validation"] = {"status": "stale", "violations": []}
        chapters[key] = entry
    ledger["chapters"] = chapters
    ledger["state_status"] = "stale"
    ledger["stale_from_position"] = min(
        int(ledger.get("stale_from_position") or from_position),
        from_position,
    )
    ledger.pop("current_state", None)
    revision.continuity_ledger = ledger
