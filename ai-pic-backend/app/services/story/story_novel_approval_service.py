"""Approval boundary for a complete long-form novel revision."""

from datetime import datetime

from app.models.story_novel_export import StoryNovelExport
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_chapter_service import (
    MAX_CHAPTER_CHARS,
    MIN_CHAPTER_CHARS,
    non_whitespace_chars,
)
from .story_novel_domain import active_chapters


def approve_revision(service, revision):
    chapters = active_chapters(revision)
    if len(chapters) != int(revision.chapter_count or 0) or any(
        row.review_status != "ready" for row in chapters
    ):
        raise HTTPException(status_code=409, detail="仍有待复核章节")
    invalid_lengths = [
        row.position
        for row in chapters
        if not MIN_CHAPTER_CHARS
        <= non_whitespace_chars(row.content_text)
        <= MAX_CHAPTER_CHARS
    ]
    if invalid_lengths:
        raise HTTPException(
            status_code=409, detail=f"章节长度不合格: {invalid_lengths}"
        )
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    invalid_extraction = [
        row.position
        for row in chapters
        if (
            (ledger_rows.get(str(row.position)) or {}).get("extraction_status")
            != "ready"
            or (ledger_rows.get(str(row.position)) or {}).get("body_hash")
            != row.content_hash
            or (ledger_rows.get(str(row.position)) or {}).get("source_hash")
            != novel_chapter_source_hash(row)
        )
    ]
    if invalid_extraction:
        raise HTTPException(
            status_code=409,
            detail=f"章节事实或记忆提取不完整: {invalid_extraction}",
        )
    if revision.continuity_status != "passed":
        raise HTTPException(status_code=409, detail="连续性检查尚未通过")
    coverage = {
        item.get("business_id"): item.get("content_hash")
        for item in (revision.continuity_report or {}).get("coverage") or []
    }
    expected_coverage = {row.business_id: row.content_hash for row in chapters}
    if coverage != expected_coverage:
        raise HTTPException(status_code=409, detail="连续性报告未覆盖全部当前章节")
    story = revision.story
    if story.canonical_novel_export_id:
        previous = service.db.get(StoryNovelExport, story.canonical_novel_export_id)
        if previous and previous.id != revision.id:
            previous.lifecycle_status = "superseded"
    revision.lifecycle_status = "approved"
    revision.approved_at = datetime.utcnow()
    revision.approved_by = service.user.id
    story.canonical_novel_export_id = revision.id
    CandidateService(NarrativeMemoryRepository(service.db)).approve_source_candidates(
        story,
        valid_sources={
            row.business_id: novel_chapter_source_hash(row) for row in chapters
        },
        user_id=service.user.id,
        commit=False,
    )
    service.db.commit()
    return revision
