"""Apply completed provider video tasks to Timeline clip rework lineage."""

from __future__ import annotations

from typing import Any

from app.models.video_generation_task import VideoGenerationTask
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineClipAssetRepository,
    TimelineRepository,
)
from app.services.timeline_rework_render_queue import (
    dispatch_provider_rework_render_job,
    queue_provider_rework_render_job,
)


def apply_timeline_rework_result(
    db,
    item: VideoGenerationTask,
    result_payload: dict[str, Any],
    params: dict[str, Any],
) -> None:
    context = params.get("timeline_rework")
    if not isinstance(context, dict):
        return
    timeline_id = _maybe_int(context.get("timeline_id"))
    timeline_version = _maybe_int(context.get("timeline_version"))
    clip_id = _string_value(context.get("clip_id"))
    video_url = _string_value(result_payload.get("video_url")) or _string_value(
        result_payload.get("original_video_url")
    )
    if not (timeline_id and timeline_version and clip_id and video_url):
        return

    timelines = TimelineRepository(db)
    timeline = timelines.get_by_id(timeline_id)
    if timeline is None or timeline.is_deleted or timeline.version != timeline_version:
        return

    media_assets = MediaAssetRepository(db)
    clip_assets = TimelineClipAssetRepository(db)
    media_asset = media_assets.find_by_location(asset_type="video", file_url=video_url)
    if media_asset is None:
        media_asset = media_assets.create(
            asset_type="video",
            origin="provider_rework",
            file_url=video_url,
            mime_type=result_payload.get("mime_type") or "video/mp4",
            duration_ms=_duration_ms(result_payload),
            extra_metadata={
                "video_generation_task_id": item.id,
                "provider_task_id": item.provider_task_id,
                "provider": item.provider,
                "model": item.model,
            },
            created_by=item.user_id,
        )
        db.flush()

    asset_role = _string_value(context.get("asset_role")) or "generated_video"
    existing = clip_assets.get_active_link(
        timeline_id=timeline.id,
        timeline_version=timeline.version,
        clip_id=clip_id,
        asset_role=asset_role,
        media_asset_id=media_asset.id,
    )
    if existing is not None:
        clip_link = existing
    else:
        previous = clip_assets.get_latest_for_clip_role(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            asset_role=asset_role,
        )
        clip_link = clip_assets.create(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            track_type="video",
            asset_role=asset_role,
            media_asset_id=media_asset.id,
            source="provider_rework",
            source_ref={
                "action": context.get("action"),
                "reason": context.get("reason"),
                "video_generation_task_id": item.id,
                "provider_task_id": item.provider_task_id,
                "provider": item.provider,
                "model": item.model,
                "preserves_clip_id": True,
            },
            replacement_of_id=previous.id if previous else None,
            created_by=item.user_id,
        )
        db.flush()

    render_job, should_dispatch_render = queue_provider_rework_render_job(
        db,
        timeline=timeline,
        clip_asset=clip_link,
        context=context,
        user_id=item.user_id,
    )
    db.commit()
    if render_job is not None and should_dispatch_render:
        dispatch_provider_rework_render_job(render_job, user_id=item.user_id)


def _duration_ms(result_payload: dict[str, Any]) -> int | None:
    try:
        duration = float(result_payload.get("duration") or 0)
    except (TypeError, ValueError):
        return None
    return int(duration * 1000) if duration > 0 else None


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
