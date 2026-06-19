"""Resolve renderable video URLs from Timeline clip asset lineage."""

from __future__ import annotations

from app.models.timeline import Timeline
from app.repositories.timeline_repository import TimelineClipAssetRepository
from sqlalchemy.orm import Session


class TimelineClipAssetVideoResolver:
    def __init__(self, db: Session):
        self.clip_assets = TimelineClipAssetRepository(db)

    def resolve(self, *, timeline: Timeline, clip_id: str) -> tuple[str | None, str]:
        link = self.clip_assets.get_latest_for_clip_role(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            asset_role="generated_video",
        )
        if link is None:
            link = self.clip_assets.get_latest_for_clip_role_any_version(
                timeline_id=timeline.id,
                clip_id=clip_id,
                asset_role="generated_video",
            )
        asset = link.media_asset if link is not None else None
        if asset is None or asset.is_deleted:
            return None, "missing"
        url = asset.file_url or asset.file_path
        if not url:
            return None, "missing"
        source = link.source or "timeline_clip_asset"
        return url, f"timeline_clip_asset:{source}"
