"""Persist Timeline render outputs as media_assets."""

from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.models.timeline import MediaAsset, RenderJob, Timeline
from app.repositories.timeline_repository import MediaAssetRepository
from app.services.media import upload_bytes
from app.services.render.timeline_render_types import TimelineClipVideo
from app.services.render.video_render_normalize import probe_render_video
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from sqlalchemy.orm import Session


async def persist_timeline_render_output(
    db: Session,
    *,
    job: RenderJob,
    timeline: Timeline,
    output_path: str,
    clips: list[TimelineClipVideo],
    user_id: int | None,
) -> MediaAsset:
    output_bytes = Path(output_path).read_bytes()
    sha256 = hashlib.sha256(output_bytes).hexdigest()
    try:
        render_probe = probe_render_video(output_path)
    except Exception:  # Output was already contract-checked by the render pipeline.
        render_probe = {}
    duration_seconds = render_probe.get("duration_seconds") or sum(
        clip.duration_seconds for clip in clips
    )
    duration_ms = round(float(duration_seconds) * 1000)
    filename = (
        f"timeline_{timeline.id}_v{job.timeline_version}_"
        f"{job.render_type}_{job.id}.mp4"
    )
    upload_result = await upload_bytes(
        content=output_bytes,
        filename=filename,
        media_type="video",
        prefix="timeline-renders",
        metadata={
            "timeline_id": timeline.id,
            "timeline_version": job.timeline_version,
            "render_job_id": job.id,
            "render_type": job.render_type,
            "clip_count": len(clips),
            "duration_ms": duration_ms,
            "sha256": sha256,
        },
    )

    file_url = None
    object_key = None
    file_path = None
    if upload_result and upload_result.get("success"):
        file_url = upload_result.get("file_url")
        object_key = upload_result.get("object_key")
        os.unlink(output_path)
    else:
        file_path = _store_local_render(output_path, filename)
        file_url = file_path

    media_assets = MediaAssetRepository(db)
    asset = media_assets.create(
        asset_type="video",
        origin="rendered",
        file_url=file_url,
        object_key=object_key,
        file_path=file_path,
        mime_type="video/mp4",
        hash=sha256,
        duration_ms=duration_ms,
        extra_metadata={
            "timeline_id": timeline.id,
            "timeline_version": job.timeline_version,
            "render_job_id": job.id,
            "render_type": job.render_type,
            "preset": job.preset or {},
            "render_probe": render_probe,
            "clip_ids": [clip.clip_id for clip in clips],
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
        },
        created_by=user_id or job.created_by,
    )
    db.flush()
    TimelineClipAssetLineageService(db).record_render_output(
        timeline=timeline,
        render_job_id=job.id,
        output_asset=asset,
        clips=clips,
        user_id=user_id or job.created_by,
    )
    return asset


def _store_local_render(output_path: str, filename: str) -> str:
    relative_dir = Path("renders") / "timeline"
    target_dir = Path(settings.UPLOAD_DIR) / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    shutil.move(output_path, target_path)
    return f"/uploads/{relative_dir.as_posix()}/{filename}"
