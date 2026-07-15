"""Resolve image inputs for provider-backed Timeline clip video tasks."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineClipAssetRepository,
)
from app.services.timeline_clip_video_rework_helpers import maybe_int, string_value
from sqlalchemy.orm import Session


class TimelineClipVideoReworkImageResolver:
    def __init__(self, db: Session):
        self.media_assets = MediaAssetRepository(db)
        self.clip_assets = TimelineClipAssetRepository(db)

    def start_frame_url(
        self,
        timeline: Timeline,
        clip_id: str,
        clip: dict[str, Any],
    ) -> str | None:
        return (
            self.asset_ref_url(clip.get("start_frame_asset_ref"))
            or self.asset_ref_url(clip.get("storyboard_image_asset_ref"))
            or string_value(clip.get("start_image_url"))
            or string_value(clip.get("image_url"))
            or self._lineage_image_url(timeline, clip_id)
        )

    def end_frame_url(self, clip: dict[str, Any]) -> str | None:
        return self.asset_ref_url(clip.get("end_frame_asset_ref")) or string_value(
            clip.get("end_image_url")
        )

    def asset_ref_url(self, asset_ref: Any) -> str | None:
        if not isinstance(asset_ref, dict):
            return None
        for key in ("file_url", "url", "image_url", "video_url", "file_path"):
            value = string_value(asset_ref.get(key))
            if value:
                return value
        asset_id = maybe_int(
            asset_ref.get("media_asset_id")
            or asset_ref.get("asset_id")
            or asset_ref.get("image_asset_id")
            or asset_ref.get("video_asset_id")
        )
        asset = self.media_assets.get_by_id(asset_id) if asset_id else None
        if asset is None or asset.is_deleted:
            return None
        return asset.file_url or asset.file_path

    def _lineage_image_url(self, timeline: Timeline, clip_id: str) -> str | None:
        for role in ("start_frame", "storyboard_image"):
            link = self.clip_assets.get_latest_for_clip_role(
                timeline_id=timeline.id,
                timeline_version=timeline.version,
                clip_id=clip_id,
                asset_role=role,
            )
            if link is None:
                link = self.clip_assets.get_latest_for_clip_role_any_version(
                    timeline_id=timeline.id,
                    clip_id=clip_id,
                    asset_role=role,
                )
            asset = link.media_asset if link is not None else None
            if asset is not None and not asset.is_deleted:
                url = asset.file_url or asset.file_path
                if url:
                    return url
        return None
