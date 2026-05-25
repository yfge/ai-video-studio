"""Timeline delete, restore, and rollback operations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.models.timeline import RenderJob, Timeline
from app.models.user import User
from app.repositories.timeline_repository import RenderJobRepository, TimelineRepository
from app.schemas.timeline import (
    RenderJobResponse,
    TimelineDeleteRequest,
    TimelineResponse,
    TimelineRollbackRequest,
    TimelineVersionRequest,
)
from app.services.timeline_responses import render_job_response, timeline_response
from app.services.timeline_revision_service import TimelineRevisionService
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineLifecycleService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.render_jobs = RenderJobRepository(db)
        self.revisions = TimelineRevisionService(db)

    def delete_timeline(
        self,
        timeline_id: int,
        payload: TimelineDeleteRequest,
        current_user: User,
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        self._check_expected_version(timeline, payload.expected_version)
        timeline.soft_delete(
            user_id=current_user.id,
            reason=payload.reason or "timeline_deleted",
        )
        timeline.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(timeline)
        return timeline_response(timeline)

    def restore_timeline(
        self,
        timeline_id: int,
        payload: TimelineVersionRequest,
        current_user: User,
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(
            timeline_id,
            current_user,
            include_deleted=True,
        )
        self._check_expected_version(timeline, payload.expected_version)
        self._restore_soft_deleted(timeline)
        timeline.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(timeline)
        return timeline_response(timeline)

    def rollback_timeline(
        self,
        timeline_id: int,
        payload: TimelineRollbackRequest,
        current_user: User,
    ) -> TimelineResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        self._check_expected_version(timeline, payload.expected_version)
        if payload.target_version >= timeline.version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rollback target_version must be older than current version",
            )
        revision = self.revisions.get_revision(
            timeline_id=timeline.id,
            timeline_version=payload.target_version,
        )
        if revision is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline revision not found",
            )

        source_version = timeline.version
        self.revisions.ensure_revision(
            timeline,
            reason="pre_rollback_snapshot",
            user_id=current_user.id,
        )
        timeline.title = revision.title
        timeline.status = revision.status
        timeline.source_audio_timeline_version = revision.source_audio_timeline_version
        timeline.version = source_version + 1
        timeline.spec = {**(revision.spec or {}), "version": timeline.version}
        timeline.rollback_of_version = source_version
        timeline.rollback_target_version = payload.target_version
        timeline.rolled_back_at = datetime.utcnow()
        timeline.rolled_back_by = current_user.id
        timeline.updated_by = current_user.id
        timeline.spec = self.revisions.spec_with_identity(timeline)
        self.revisions.ensure_revision(
            timeline,
            reason=f"rollback_to_{payload.target_version}",
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(timeline)
        return timeline_response(timeline)

    def delete_render_job(
        self,
        timeline_id: int,
        render_job_id: int,
        payload: TimelineDeleteRequest,
        current_user: User,
    ) -> RenderJobResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        self._check_expected_version(timeline, payload.expected_version)
        job = self._get_render_job_or_404(timeline, render_job_id)
        job.soft_delete(
            user_id=current_user.id,
            reason=payload.reason or "render_job_deleted",
        )
        self.db.commit()
        self.db.refresh(job)
        return render_job_response(job)

    def restore_render_job(
        self,
        timeline_id: int,
        render_job_id: int,
        payload: TimelineVersionRequest,
        current_user: User,
    ) -> RenderJobResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        self._check_expected_version(timeline, payload.expected_version)
        job = self._get_render_job_or_404(
            timeline,
            render_job_id,
            include_deleted=True,
        )
        self._restore_soft_deleted(job)
        self.db.commit()
        self.db.refresh(job)
        return render_job_response(job)

    def _get_timeline_or_404(
        self,
        timeline_id: int,
        current_user: User,
        *,
        include_deleted: bool = False,
    ) -> Timeline:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=self._story_owner_filter(current_user),
            include_deleted=include_deleted,
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )
        return timeline

    def _get_render_job_or_404(
        self,
        timeline: Timeline,
        render_job_id: int,
        *,
        include_deleted: bool = False,
    ) -> RenderJob:
        job = self.render_jobs.get_for_timeline(
            timeline_id=timeline.id,
            render_job_id=render_job_id,
            include_deleted=include_deleted,
        )
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="render job not found",
            )
        return job

    @staticmethod
    def _check_expected_version(timeline: Timeline, expected_version: int) -> None:
        if timeline.version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )

    @staticmethod
    def _restore_soft_deleted(entity: Timeline | RenderJob) -> None:
        entity.is_deleted = False
        entity.deleted_at = None
        entity.deleted_by = None
        entity.deleted_reason = None

    @staticmethod
    def _story_owner_filter(current_user: User) -> Optional[int]:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id
