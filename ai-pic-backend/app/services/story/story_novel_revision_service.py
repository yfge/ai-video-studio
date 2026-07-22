from __future__ import annotations

from datetime import datetime, timezone

from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.user import User
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.generation_requests import StoryNovelExportRequest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .story_novel_domain import (
    active_chapters,
    build_story_snapshot,
    default_generation_plan,
    refresh_revision_content,
    sha256_text,
)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


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
        if story.workflow_mode != "novel_adaptation_v1":
            story.workflow_mode = "novel_adaptation_v1"
        chapter_count = request.chapter_count or max(
            3, min(24, round(request.target_words / 1800))
        )
        revision = StoryNovelExport(
            story_id=story.id,
            story_business_id=story.business_id,
            task_id=task_id,
            user_id=self.user.id,
            style="prose",
            target_words=request.target_words,
            chapter_count=chapter_count,
            total_words=0,
            model=request.model,
            temperature=request.temperature,
            content_text="",
            revision_number=self.repo.next_revision_number(story.id),
            lifecycle_status="draft",
            continuity_status="unchecked",
            adaptation_plan_status="empty",
            story_snapshot=build_story_snapshot(story),
            generation_plan=default_generation_plan(story, chapter_count),
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
        self._check_timestamp(chapter.updated_at, request.expected_updated_at)
        for field in ("title", "content_text", "summary", "cliffhanger"):
            value = getattr(request, field, None)
            if value is not None:
                setattr(chapter, field, value)
        chapter.content_hash = sha256_text(chapter.content_text)
        chapter.review_status = "ready"
        self._invalidate_from(revision, chapter.position + 1)
        refresh_revision_content(revision)
        self.db.commit()
        self.db.refresh(chapter)
        return chapter

    def reorder(self, revision_id: str, request) -> StoryNovelExport:
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        self._check_timestamp(revision.updated_at, request.expected_updated_at)
        chapters = active_chapters(revision)
        existing = {row.business_id: row for row in chapters}
        ordered = request.ordered_chapter_business_ids
        if len(ordered) != len(set(ordered)) or set(ordered) != set(existing):
            raise HTTPException(status_code=400, detail="章节排序列表不完整或有重复")
        changed_at = len(chapters) + 1
        old = {row.business_id: row.position for row in chapters}
        for position, business_id in enumerate(ordered, start=1):
            changed_at = min(changed_at, old[business_id], position)
            existing[business_id].position = position
        self._invalidate_from(revision, changed_at)
        refresh_revision_content(revision)
        self.db.commit()
        return revision

    def clone(self, revision_id: str) -> StoryNovelExport:
        source = self.revision(revision_id)
        story = source.story
        request = StoryNovelExportRequest(
            style="prose",
            target_words=source.target_words,
            chapter_count=source.chapter_count,
            model=source.model,
            temperature=source.temperature,
        )
        clone = self.create_draft(story.business_id, request)
        clone.story_snapshot = build_story_snapshot(story)
        clone.generation_plan = source.generation_plan
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
        chapters = active_chapters(revision)
        if len(chapters) != int(revision.chapter_count or 0) or any(
            row.review_status != "ready" for row in chapters
        ):
            raise HTTPException(status_code=409, detail="仍有待复核章节")
        if revision.continuity_status != "passed":
            raise HTTPException(status_code=409, detail="连续性检查尚未通过")
        story = revision.story
        if story.canonical_novel_export_id:
            previous = self.db.get(StoryNovelExport, story.canonical_novel_export_id)
            if previous and previous.id != revision.id:
                previous.lifecycle_status = "superseded"
        revision.lifecycle_status = "approved"
        revision.approved_at = datetime.utcnow()
        revision.approved_by = self.user.id
        story.canonical_novel_export_id = revision.id
        self.db.commit()
        return revision

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

    @staticmethod
    def _check_timestamp(actual: datetime | None, expected: datetime) -> None:
        if actual and abs((_utc(actual) - _utc(expected)).total_seconds()) > 0.001:
            raise HTTPException(status_code=409, detail="内容已被其他窗口更新")
