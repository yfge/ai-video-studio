"""Promote Timeline-derived storyboard images into stable clip asset lineage."""

from __future__ import annotations

from typing import Any, Sequence

from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineClipAssetRepository,
    TimelineRepository,
)
from sqlalchemy.orm import Session


def sync_storyboard_frame_images_to_timeline(
    db: Session,
    *,
    script_id: int,
    task_id: int,
    user_id: int | None,
    frames: Sequence[Any],
    frame_indexes: Sequence[int],
) -> int:
    """Create idempotent storyboard-image links for generated Timeline frames."""

    timelines = TimelineRepository(db)
    media_assets = MediaAssetRepository(db)
    clip_assets = TimelineClipAssetRepository(db)
    timeline_cache: dict[int, Any] = {}
    linked = 0

    for frame_index in frame_indexes:
        if frame_index < 0 or frame_index >= len(frames):
            continue
        frame = frames[frame_index]
        if not isinstance(frame, dict):
            continue
        timeline_id = _positive_int(frame.get("timeline_id"))
        clip_id = _string(frame.get("timeline_clip_id"))
        image_url = _frame_image_url(frame)
        if not timeline_id or not clip_id or not image_url:
            continue

        timeline = timeline_cache.get(timeline_id)
        if timeline is None:
            timeline = timelines.get_by_id(timeline_id)
            timeline_cache[timeline_id] = timeline
        if (
            timeline is None
            or timeline.is_deleted
            or timeline.script_id != script_id
            or not _timeline_has_clip(timeline.spec, clip_id)
        ):
            continue
        timeline_version = _positive_int(frame.get("timeline_version"))
        timeline_version = timeline_version or timeline.version
        if timeline_version > timeline.version:
            continue

        media_asset = media_assets.find_by_location(
            asset_type="image", file_url=image_url
        )
        if media_asset is None:
            media_asset = media_assets.create(
                asset_type="image",
                origin="generated",
                file_url=image_url,
                mime_type=_image_mime_type(image_url),
                extra_metadata={
                    "kind": "timeline_storyboard_image",
                    "task_id": task_id,
                    "script_id": script_id,
                    "timeline_id": timeline.id,
                    "timeline_version": timeline_version,
                    "clip_id": clip_id,
                    "frame_id": frame.get("frame_id"),
                    "frame_index": frame_index,
                },
                created_by=user_id,
            )
            db.flush()

        existing = clip_assets.get_active_link(
            timeline_id=timeline.id,
            timeline_version=timeline_version,
            clip_id=clip_id,
            asset_role="storyboard_image",
            media_asset_id=media_asset.id,
        )
        if existing is not None:
            continue
        clip_assets.create(
            timeline_id=timeline.id,
            timeline_version=timeline_version,
            clip_id=clip_id,
            track_type="video",
            asset_role="storyboard_image",
            media_asset_id=media_asset.id,
            source="storyboard_image_generation",
            source_ref={
                "task_id": task_id,
                "script_id": script_id,
                "timeline_version": timeline_version,
                "frame_id": frame.get("frame_id"),
                "frame_index": frame_index,
                "preserves_clip_id": True,
            },
            created_by=user_id,
        )
        linked += 1
    return linked


def _timeline_has_clip(spec: Any, clip_id: str) -> bool:
    if not isinstance(spec, dict):
        return False
    return any(
        isinstance(clip, dict) and (clip.get("clip_id") or clip.get("id")) == clip_id
        for track in spec.get("tracks") or []
        if isinstance(track, dict)
        for clip in track.get("clips") or []
    )


def _frame_image_url(frame: dict[str, Any]) -> str | None:
    return _string(frame.get("start_image_url")) or _string(frame.get("image_url"))


def _string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _image_mime_type(url: str) -> str:
    clean = url.lower().split("?", 1)[0]
    if clean.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if clean.endswith(".webp"):
        return "image/webp"
    return "image/png"
