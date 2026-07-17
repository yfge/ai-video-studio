"""Protection rules for automatic Timeline video-window upgrades."""

from __future__ import annotations

from app.models.task import TaskType
from app.models.timeline import Timeline
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import (
    RenderJobRepository,
    TimelineClipAssetRepository,
)
from app.services.timeline_clip_asset_candidates import timeline_clip_asset_candidates
from app.services.timeline_video_segmentation_config import VIDEO_SEGMENTATION_STRATEGY
from sqlalchemy.orm import Session

_VIDEO_ASSET_ROLES = {"generated_video", "storyboard_video", "render_output"}


def timeline_needs_video_segmentation_upgrade(timeline: Timeline) -> bool:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    source = spec.get("source") if isinstance(spec.get("source"), dict) else {}
    segmentation = (
        source.get("video_segmentation")
        if isinstance(source.get("video_segmentation"), dict)
        else {}
    )
    return segmentation.get("strategy") != VIDEO_SEGMENTATION_STRATEGY


def timeline_allows_automatic_video_segmentation_upgrade(
    db: Session,
    timeline: Timeline,
) -> bool:
    if _has_video_assets(db, timeline):
        return False
    if timeline.business_id and TaskRepository(db).list_active_for_target_any_user(
        target_business_id=timeline.business_id,
        task_type=TaskType.VIDEO_GENERATION,
    ):
        return False
    if RenderJobRepository(db).list_for_timeline(timeline.id):
        return False
    return True


def _has_video_assets(db: Session, timeline: Timeline) -> bool:
    links = TimelineClipAssetRepository(db).list_for_timeline(
        timeline_id=timeline.id,
        timeline_version=timeline.version,
    )
    if any(link.asset_role in _VIDEO_ASSET_ROLES for link in links):
        return True
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    return any(
        candidate.asset_role in _VIDEO_ASSET_ROLES
        for candidate in timeline_clip_asset_candidates(spec)
    )
