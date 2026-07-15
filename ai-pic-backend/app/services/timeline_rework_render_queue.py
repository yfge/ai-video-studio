"""Queue Timeline renders after provider-backed clip rework succeeds."""

from __future__ import annotations

from typing import Any

from app.models.timeline import RenderJob, Timeline, TimelineClipAsset
from app.repositories.timeline_repository import RenderJobRepository
from app.services.render.timeline_render_clips import TimelineClipResolver
from app.services.timeline_render_dispatch import (
    dispatch_timeline_render_job_for_user_id,
)
from app.services.timeline_render_hash import render_preset_hash
from sqlalchemy.orm import Session

REWORK_RENDER_TYPES = {"proxy", "final", "export"}
DEFAULT_REWORK_RENDER_TYPE = "final"


def queue_provider_rework_render_job(
    db: Session,
    *,
    timeline: Timeline,
    clip_asset: TimelineClipAsset,
    context: dict[str, Any],
    user_id: int | None,
) -> tuple[RenderJob | None, bool]:
    """Create an idempotent render job for a successful provider rework."""

    if not _truthy(context.get("auto_render")):
        return None, False
    if not _timeline_render_ready(db, timeline):
        return None, False

    render_type = _render_type(context.get("render_type"))
    preset = _render_preset(timeline, clip_asset, context)
    preset_hash = render_preset_hash(preset)
    render_jobs = RenderJobRepository(db)
    existing = render_jobs.get_idempotent(
        timeline_id=timeline.id,
        timeline_version=timeline.version,
        render_type=render_type,
        preset_hash=preset_hash,
    )
    if existing is not None:
        return existing, False

    job = render_jobs.create(
        timeline_id=timeline.id,
        timeline_version=timeline.version,
        render_type=render_type,
        preset_hash=preset_hash,
        preset=preset,
        status="queued",
        progress=0,
        created_by=user_id,
    )
    db.flush()
    return job, True


def _timeline_render_ready(db: Session, timeline: Timeline) -> bool:
    resolved, missing = TimelineClipResolver(db).resolve(timeline)
    return bool(resolved) and not missing


def dispatch_provider_rework_render_job(
    job: RenderJob,
    *,
    user_id: int | None,
) -> None:
    dispatch_timeline_render_job_for_user_id(job, user_id)


def _render_preset(
    timeline: Timeline,
    clip_asset: TimelineClipAsset,
    context: dict[str, Any],
) -> dict[str, Any]:
    raw_preset = context.get("render_preset")
    preset = (
        dict(raw_preset) if isinstance(raw_preset, dict) else _default_preset(timeline)
    )
    source_ref = (
        clip_asset.source_ref if isinstance(clip_asset.source_ref, dict) else {}
    )
    preset["rework"] = {
        "source": "provider_rework",
        "clip_id": clip_asset.clip_id,
        "timeline_clip_asset_id": clip_asset.id,
        "media_asset_id": clip_asset.media_asset_id,
        "replacement_of_id": clip_asset.replacement_of_id,
        "action": context.get("action"),
        "video_generation_task_id": source_ref.get("video_generation_task_id"),
        "provider_task_id": source_ref.get("provider_task_id"),
    }
    return preset


def _default_preset(timeline: Timeline) -> dict[str, Any]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    return {
        "fps": spec.get("fps") or 24,
        "resolution": spec.get("resolution") or "1080x1920",
    }


def _render_type(value: Any) -> str:
    return (
        value
        if isinstance(value, str) and value in REWORK_RENDER_TYPES
        else DEFAULT_REWORK_RENDER_TYPE
    )


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off"}
    return bool(value)
