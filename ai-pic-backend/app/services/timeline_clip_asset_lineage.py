"""Clip asset lineage built around stable Timeline clip ids."""

from __future__ import annotations

from typing import Optional

from app.models.timeline import MediaAsset, Timeline
from app.models.user import User
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineClipAssetRepository,
    TimelineRepository,
)
from app.schemas.timeline import TimelineClipAssetResponse
from app.services.render.timeline_render_clips import TimelineClipVideo
from app.services.timeline_clip_asset_candidates import (
    ClipAssetCandidate,
    timeline_clip_asset_candidates,
)
from app.services.timeline_responses import timeline_clip_asset_response
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineClipAssetLineageService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.media_assets = MediaAssetRepository(db)
        self.clip_assets = TimelineClipAssetRepository(db)

    def list_clip_assets(
        self,
        timeline_id: int,
        current_user: User,
        *,
        timeline_version: int | None = None,
        clip_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[TimelineClipAssetResponse]:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        items = self.clip_assets.list_for_timeline(
            timeline_id=timeline.id,
            timeline_version=timeline_version,
            clip_id=clip_id,
            include_deleted=include_deleted,
        )
        return [timeline_clip_asset_response(item) for item in items]

    def sync_timeline_assets(self, timeline: Timeline, *, user_id: int | None) -> None:
        for candidate in self._candidates_from_spec(timeline):
            asset = self._ensure_media_asset(candidate, user_id=user_id)
            self._ensure_clip_asset_link(
                timeline,
                candidate,
                media_asset=asset,
                user_id=user_id,
            )

    def record_render_output(
        self,
        *,
        timeline: Timeline,
        render_job_id: int,
        output_asset: MediaAsset,
        clips: list[TimelineClipVideo],
        user_id: int | None,
    ) -> None:
        for clip in clips:
            candidate = ClipAssetCandidate(
                clip_id=clip.clip_id,
                track_type="video",
                asset_role="render_output",
                asset_type="video",
                origin="rendered",
                media_asset_id=output_asset.id,
                source="render_job",
                source_ref={
                    "render_job_id": render_job_id,
                    "timeline_version": timeline.version,
                    "clip_source": clip.source,
                    "start_ms": clip.start_ms,
                    "end_ms": clip.end_ms,
                },
            )
            self._ensure_clip_asset_link(
                timeline,
                candidate,
                media_asset=output_asset,
                render_job_id=render_job_id,
                user_id=user_id,
            )

    def _ensure_media_asset(
        self,
        candidate: ClipAssetCandidate,
        *,
        user_id: int | None,
    ) -> MediaAsset:
        if candidate.media_asset_id:
            asset = self.media_assets.get_by_id(candidate.media_asset_id)
            if asset is None or asset.is_deleted:
                raise ValueError("timeline_clip_asset_missing_media_asset")
            return asset
        existing = self.media_assets.find_by_location(
            asset_type=candidate.asset_type,
            file_url=candidate.file_url,
            file_path=candidate.file_path,
            object_key=candidate.object_key,
        )
        if existing is not None:
            return existing
        asset = self.media_assets.create(
            asset_type=candidate.asset_type,
            origin=candidate.origin,
            file_url=candidate.file_url,
            file_path=candidate.file_path,
            object_key=candidate.object_key,
            mime_type=candidate.mime_type,
            duration_ms=candidate.duration_ms,
            extra_metadata=candidate.source_ref,
            created_by=user_id,
        )
        self.db.flush()
        return asset

    def _ensure_clip_asset_link(
        self,
        timeline: Timeline,
        candidate: ClipAssetCandidate,
        *,
        media_asset: MediaAsset,
        user_id: int | None,
        render_job_id: int | None = None,
    ) -> None:
        existing = self.clip_assets.get_active_link(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=candidate.clip_id,
            asset_role=candidate.asset_role,
            media_asset_id=media_asset.id,
        )
        if existing is not None:
            return
        self.clip_assets.create(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=candidate.clip_id,
            track_type=candidate.track_type,
            asset_role=candidate.asset_role,
            media_asset_id=media_asset.id,
            render_job_id=render_job_id,
            source=candidate.source,
            source_ref=candidate.source_ref,
            created_by=user_id,
        )
        self.db.flush()

    def _candidates_from_spec(self, timeline: Timeline) -> list[ClipAssetCandidate]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        return timeline_clip_asset_candidates(spec)

    def _get_timeline_or_404(self, timeline_id: int, current_user: User) -> Timeline:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=self._story_owner_filter(current_user),
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )
        return timeline

    @staticmethod
    def _story_owner_filter(current_user: User) -> Optional[int]:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id
