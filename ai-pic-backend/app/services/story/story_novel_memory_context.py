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


def invalidate_chapter_source(db, revision, chapter, source_before_hash: str):
    return NarrativeMemoryInvalidationService(
        NarrativeMemoryRepository(db)
    ).mark_source_changed(
        revision.story,
        artifact_business_id=chapter.business_id,
        source_before_hash=source_before_hash,
        source_after_hash=novel_chapter_source_hash(chapter),
        commit=False,
    )


def invalidate_reordered_chapters(db, revision, chapters, source_before) -> None:
    for chapter in chapters:
        invalidate_chapter_source(
            db, revision, chapter, source_before[chapter.business_id]
        )
