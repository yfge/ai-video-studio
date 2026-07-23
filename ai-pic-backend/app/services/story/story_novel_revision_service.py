from __future__ import annotations

from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.user import User
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.generation_requests import StoryNovelExportRequest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .story_novel_domain import (
    active_chapters,
    build_story_snapshot,
    refresh_revision_content,
    sha256_text,
)
from .story_novel_approval_service import approve_revision
from .story_novel_memory_context import (
    capture_chapter_source_hashes,
    ensure_timestamp,
    invalidate_chapter_source,
    invalidate_reordered_chapters,
    mark_revision_ledger_stale,
)


class StoryNovelRevisionService:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.repo = StoryNovelRepository(db)

    def story(self, business_id: str):
        story = self.repo.accessible_story(business_id, self.user)
        if not story:
            raise HTTPException(status_code=404, detail="故事不存在")
        return story

    def revision(self, business_id: str) -> StoryNovelExport:
        revision = self.repo.accessible_revision(business_id, self.user)
        if not revision:
            raise HTTPException(status_code=404, detail="小说版本不存在")
        return revision

    def create_draft(
        self,
        story_business_id: str,
        request: StoryNovelExportRequest,
        *,
        task_id: int | None = None,
    ) -> StoryNovelExport:
        story = self.story(story_business_id)
        if not story.story_seed or story.story_seed_status != "confirmed":
            raise HTTPException(
                status_code=409, detail="请先确认 Story Seed，再生成小说"
            )
        if story.workflow_mode != "novel_adaptation_v1":
            story.workflow_mode = "novel_adaptation_v1"
        revision = StoryNovelExport(
            story_id=story.id,
            story_business_id=story.business_id,
            task_id=task_id,
            user_id=self.user.id,
            style="prose",
            target_words=0,
            chapter_count=None,
            total_words=0,
            model=request.model,
            temperature=request.temperature,
            content_text="",
            revision_number=self.repo.next_revision_number(story.id),
            lifecycle_status="draft",
            continuity_status="unchecked",
            adaptation_plan_status="empty",
            story_snapshot=build_story_snapshot(story),
            generation_plan={"version": 1, "status": "planning", "chapters": []},
            continuity_ledger={
                "schema": "story_novel_continuity.v2",
                "state_status": "empty",
                "chapters": {},
            },
        )
        self.db.add(revision)
        self.db.flush()
        return revision

    def checkpoint_chapter(
        self,
        revision: StoryNovelExport,
        *,
        position: int,
        title: str,
        content_text: str,
        summary: str | None,
        cliffhanger: str | None,
    ) -> StoryNovelChapter:
        chapter = next(
            (row for row in active_chapters(revision) if row.position == position),
            None,
        )
        if not chapter:
            chapter = StoryNovelChapter(
                novel_export_id=revision.id,
                novel_export_business_id=revision.business_id,
                position=position,
                title=title,
                content_text=content_text,
            )
            self.db.add(chapter)
            revision.chapters.append(chapter)
        chapter.title = title
        chapter.content_text = content_text.strip()
        chapter.summary = summary
        chapter.cliffhanger = cliffhanger
        chapter.review_status = "ready"
        chapter.content_hash = sha256_text(chapter.content_text)
        refresh_revision_content(revision)
        self.db.commit()
        return chapter

    def save_chapter(self, revision_id: str, chapter_id: str, request):
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        chapter = self.repo.chapter(revision.id, chapter_id)
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
        self._invalidate_from(revision, chapter.position + 1)
        refresh_revision_content(revision)
        invalidate_chapter_source(
            self.db, revision, chapter, source_before[chapter.business_id]
        )
        self.db.commit()
        self.db.refresh(chapter)
        return chapter

    def reorder(self, revision_id: str, request) -> StoryNovelExport:
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
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
        invalidate_reordered_chapters(self.db, revision, chapters, source_before)
        mark_revision_ledger_stale(revision, from_position=changed_at)
        self._invalidate_from(revision, changed_at)
        refresh_revision_content(revision)
        self.db.commit()
        return revision

    def clone(self, revision_id: str) -> StoryNovelExport:
        source = self.revision(revision_id)
        story = source.story
        request = StoryNovelExportRequest(
            style="prose", model=source.model, temperature=source.temperature
        )
        clone = self.create_draft(story.business_id, request)
        clone.story_snapshot = build_story_snapshot(story)
        clone.generation_plan = source.generation_plan
        clone.target_words = source.target_words
        clone.chapter_count = source.chapter_count
        for row in active_chapters(source):
            self.checkpoint_chapter(
                clone,
                position=row.position,
                title=row.title,
                content_text=row.content_text,
                summary=row.summary,
                cliffhanger=row.cliffhanger,
            )
        clone.continuity_status = "review_required"
        self.db.commit()
        return clone

    def accept_issue(self, revision_id: str, issue_id: str, reason: str):
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        report = dict(revision.continuity_report or {})
        issues = [dict(item) for item in report.get("issues") or []]
        issue = next((item for item in issues if str(item.get("id")) == issue_id), None)
        if not issue:
            raise HTTPException(status_code=404, detail="连续性问题不存在")
        issue["accepted_reason"] = reason
        report["issues"] = issues
        revision.continuity_report = report
        blockers = [
            item
            for item in issues
            if item.get("severity") == "blocking" and not item.get("accepted_reason")
        ]
        revision.continuity_status = "failed" if blockers else "passed"
        self.db.commit()
        return revision

    def approve(self, revision_id: str) -> StoryNovelExport:
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        return approve_revision(self, revision)

    def _invalidate_from(self, revision: StoryNovelExport, position: int) -> None:
        for row in self.repo.chapters_from_position(revision.id, position):
            row.review_status = "review_required"
        revision.continuity_status = "review_required"
        if revision.adaptation_plan_status != "empty":
            revision.adaptation_plan_status = "stale"

    @staticmethod
    def _ensure_draft(revision: StoryNovelExport) -> None:
        if revision.lifecycle_status != "draft":
            raise HTTPException(
                status_code=409, detail="已审批小说不可编辑，请克隆新草稿"
            )
