"""Operator rework actions that preserve stable Timeline clip identity."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineClipAssetRepository,
    TimelineRepository,
)
from app.schemas.timeline import TimelineClipAssetResponse, TimelineClipReworkRequest
from app.services.timeline_responses import timeline_clip_asset_response
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineClipReworkService:
    """Record replacement media for a clip without changing its `clip_id`."""

    _ACTION_DEFAULTS: dict[str, tuple[str, str]] = {
        "re_dub": ("source_audio", "audio"),
        "re_cut": ("generated_video", "video"),
        "re_render": ("render_output", "video"),
    }
    _ACTION_ROLES: dict[str, set[str]] = {
        "re_dub": {"source_audio"},
        "re_cut": {"storyboard_video", "generated_video", "render_output"},
        "re_render": {"generated_video", "render_output"},
    }

    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.media_assets = MediaAssetRepository(db)
        self.clip_assets = TimelineClipAssetRepository(db)

    def rework_clip(
        self,
        timeline_id: int,
        clip_id: str,
        payload: TimelineClipReworkRequest,
        current_user: User,
    ) -> TimelineClipAssetResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )
        clip = self._clip_or_404(timeline, clip_id)
        asset = self.media_assets.get_by_id(payload.media_asset_id)
        if asset is None or asset.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="media asset not found",
            )

        asset_role, expected_asset_type = self._resolve_role(payload)
        if asset.asset_type != expected_asset_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{payload.action} requires a {expected_asset_type} media asset"
                ),
            )
        existing_exact = self.clip_assets.get_active_link(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            asset_role=asset_role,
            media_asset_id=asset.id,
        )
        if existing_exact is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="clip media asset is already linked",
            )

        previous = self.clip_assets.get_latest_for_clip_role(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            asset_role=asset_role,
        )
        link = self.clip_assets.create(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            track_type=self._track_type(clip),
            asset_role=asset_role,
            media_asset_id=asset.id,
            source="operator_rework",
            source_ref={
                "action": payload.action,
                "reason": payload.reason,
                "expected_version": payload.expected_version,
                "previous_clip_asset_id": previous.id if previous else None,
                "preserves_clip_id": True,
            },
            replacement_of_id=previous.id if previous else None,
            created_by=current_user.id,
        )
        self.db.commit()
        self.db.refresh(link)
        return timeline_clip_asset_response(link)

    def _resolve_role(self, payload: TimelineClipReworkRequest) -> tuple[str, str]:
        default_role, expected_asset_type = self._ACTION_DEFAULTS[payload.action]
        asset_role = payload.asset_role or default_role
        if asset_role not in self._ACTION_ROLES[payload.action]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{payload.action} does not support asset_role {asset_role}",
            )
        return asset_role, expected_asset_type

    def _clip_or_404(self, timeline: Timeline, clip_id: str) -> dict[str, Any]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        for track in spec.get("tracks") or []:
            if not isinstance(track, dict):
                continue
            track_type = track.get("track_type") or track.get("type")
            for clip in track.get("clips") or []:
                if isinstance(clip, dict) and clip.get("clip_id") == clip_id:
                    return {**clip, "track_type": clip.get("track_type") or track_type}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="timeline clip not found",
        )

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
    def _track_type(clip: dict[str, Any]) -> str | None:
        value = clip.get("track_type")
        return str(value) if value else None

    @staticmethod
    def _story_owner_filter(current_user: User) -> int | None:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id
