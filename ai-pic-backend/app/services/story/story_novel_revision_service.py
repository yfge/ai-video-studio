from __future__ import annotations

from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.user import User
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.generation_requests import StoryNovelExportRequest
from app.schemas.story_novel_export import StoryNovelCreateRevisionRequest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .story_novel_approval_service import approve_revision
from .story_novel_canon_edit_service import update_revision_canon
from .story_novel_canon_service import content_hash
from .story_novel_domain import (
    active_chapters,
    build_story_snapshot,
    refresh_revision_content,
    sha256_text,
)
from .story_novel_length_service import apply_length_spec
from .story_novel_plan_versions import is_v3_plan
from .story_novel_revision_edits import ensure_draft, reorder_chapters, save_chapter
from .story_novel_revision_factory import (
    create_legacy_revision,
    create_platform_revision,
)
from .story_novel_v3_clone import clone_generation_plan


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
        self._ensure_story_idle(story, exclude_task_id=task_id)
        if not story.story_seed or story.story_seed_status != "confirmed":
            raise HTTPException(
                status_code=409, detail="请先确认 Story Seed，再生成小说"
            )
        if story.workflow_mode != "novel_adaptation_v1":
            story.workflow_mode = "novel_adaptation_v1"
        seed = story.story_seed or {}
        if seed.get("schema") == "story_seed_v2":
            return create_platform_revision(
                self,
                story,
                StoryNovelCreateRevisionRequest(
                    model=request.model, temperature=request.temperature
                ),
                task_id,
            )
        return create_legacy_revision(self, story, request, task_id)

    def create_platform_draft(
        self,
        story_business_id: str,
        request: StoryNovelCreateRevisionRequest,
        *,
        task_id: int | None = None,
    ) -> StoryNovelExport:
        story = self.story(story_business_id)
        self._ensure_story_idle(story, exclude_task_id=task_id)
        if story.workflow_mode != "novel_adaptation_v1":
            story.workflow_mode = "novel_adaptation_v1"
        return create_platform_revision(self, story, request, task_id)

    def update_length_spec(self, revision_id: str, request):
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        self.ensure_no_active_task(revision)
        plan = apply_length_spec(revision, request)
        revision.generation_plan = plan
        revision.chapter_count = plan["chapter_count"]
        revision.target_words = plan["planned_target_chars"]
        self.db.commit()
        self.db.refresh(revision)
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
        commit: bool = True,
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
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return chapter

    def save_chapter(self, revision_id: str, chapter_id: str, request):
        return save_chapter(self, revision_id, chapter_id, request)

    def reorder(self, revision_id: str, request) -> StoryNovelExport:
        return reorder_chapters(self, revision_id, request)

    def clone(self, revision_id: str) -> StoryNovelExport:
        source = self.revision(revision_id)
        self.ensure_no_active_task(source)
        story = source.story
        request = StoryNovelExportRequest(
            style="prose", model=source.model, temperature=source.temperature
        )
        clone = self.create_draft(story.business_id, request)
        clone.story_snapshot = build_story_snapshot(story)
        clone.generation_plan = clone_generation_plan(source.generation_plan)
        if is_v3_plan(source.generation_plan):
            clone.continuity_ledger = {
                "schema": "story_novel_continuity.v4",
                "state_status": "stale",
                "stale_from_position": 1,
                "chapters": {},
            }
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
        self.ensure_no_active_task(revision)
        report = dict(revision.continuity_report or {})
        issues = [dict(item) for item in report.get("issues") or []]
        issue = next((item for item in issues if str(item.get("id")) == issue_id), None)
        if not issue:
            raise HTTPException(status_code=404, detail="连续性问题不存在")
        issue["accepted_reason"] = reason
        report["issues"] = issues
        blockers = [
            item
            for item in issues
            if item.get("severity") == "blocking" and not item.get("accepted_reason")
        ]
        hard_failed = any(
            value
            for key, value in (report.get("hard_metrics") or {}).items()
            if key != "chapter_repair_rate"
        )
        if report.get("schema") == "story_novel_continuity_review.v3":
            report.pop("report_hash", None)
            report["report_hash"] = content_hash(report)
        revision.continuity_report = report
        revision.continuity_status = "failed" if blockers or hard_failed else "passed"
        self.db.commit()
        return revision

    def update_canon(self, revision_id: str, request):
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        self.ensure_no_active_task(revision)
        return update_revision_canon(self, revision, request)

    def approve(self, revision_id: str) -> StoryNovelExport:
        revision = self.revision(revision_id)
        self._ensure_draft(revision)
        self.ensure_no_active_task(revision)
        return approve_revision(self, revision)

    def ensure_no_active_task(
        self, revision: StoryNovelExport, *, exclude_task_id: int | None = None
    ) -> None:
        active = self.repo.active_task_for_targets(
            [revision.business_id, revision.story_business_id],
            exclude_task_id=exclude_task_id,
        )
        if active:
            raise HTTPException(
                status_code=409,
                detail=f"小说任务 {active.id} 正在运行，请先取消任务",
            )

    def _ensure_story_idle(self, story, *, exclude_task_id: int | None = None) -> None:
        revisions = self.repo.story_revisions(story.id)
        active = self.repo.active_task_for_targets(
            [story.business_id, *(item.business_id for item in revisions)],
            exclude_task_id=exclude_task_id,
        )
        if active:
            raise HTTPException(
                status_code=409,
                detail=f"小说任务 {active.id} 正在运行，请先取消任务",
            )

    def _invalidate_from(self, revision: StoryNovelExport, position: int) -> None:
        for row in self.repo.chapters_from_position(revision.id, position):
            row.review_status = "review_required"
        revision.continuity_status = "review_required"
        if revision.adaptation_plan_status != "empty":
            revision.adaptation_plan_status = "stale"

    _ensure_draft = staticmethod(ensure_draft)
