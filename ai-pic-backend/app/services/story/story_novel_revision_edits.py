"""Mutable chapter operations kept outside the revision facade."""

from fastapi import HTTPException

from .story_novel_domain import active_chapters, refresh_revision_content, sha256_text
from .story_novel_memory_context import (
    capture_chapter_source_hashes,
    ensure_timestamp,
    invalidate_chapter_source,
    invalidate_reordered_chapters,
    mark_revision_ledger_stale,
)


def ensure_draft(revision) -> None:
    if revision.lifecycle_status != "draft":
        raise HTTPException(status_code=409, detail="已审批小说不可编辑，请克隆新草稿")


def save_chapter(service, revision_id: str, chapter_id: str, request):
    revision = service.revision(revision_id)
    service._ensure_draft(revision)
    service.ensure_no_active_task(revision)
    chapter = service.repo.chapter(revision.id, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    ensure_timestamp(chapter.updated_at, request.expected_updated_at)
    source_before = capture_chapter_source_hashes([chapter])
    for field in ("title", "content_text", "summary", "cliffhanger"):
        value = getattr(request, field, None)
        if value is not None:
            setattr(chapter, field, value)
    chapter.content_hash = sha256_text(chapter.content_text)
    chapter.review_status = "ready"
    mark_revision_ledger_stale(
        revision, from_position=chapter.position, edited_chapter=chapter
    )
    service._invalidate_from(revision, chapter.position + 1)
    refresh_revision_content(revision)
    invalidate_chapter_source(
        service.db, revision, chapter, source_before[chapter.business_id]
    )
    service.db.commit()
    service.db.refresh(chapter)
    return chapter


def reorder_chapters(service, revision_id: str, request):
    revision = service.revision(revision_id)
    service._ensure_draft(revision)
    service.ensure_no_active_task(revision)
    ensure_timestamp(revision.updated_at, request.expected_updated_at)
    chapters = active_chapters(revision)
    existing = {row.business_id: row for row in chapters}
    ordered = request.ordered_chapter_business_ids
    if len(ordered) != len(set(ordered)) or set(ordered) != set(existing):
        raise HTTPException(status_code=400, detail="章节排序列表不完整或有重复")
    changed_at = len(chapters) + 1
    old = {row.business_id: row.position for row in chapters}
    source_before = capture_chapter_source_hashes(chapters)
    for position, business_id in enumerate(ordered, start=1):
        changed_at = min(changed_at, old[business_id], position)
        existing[business_id].position = position
    invalidate_reordered_chapters(service.db, revision, chapters, source_before)
    mark_revision_ledger_stale(revision, from_position=changed_at)
    service._invalidate_from(revision, changed_at)
    refresh_revision_content(revision)
    service.db.commit()
    return revision
