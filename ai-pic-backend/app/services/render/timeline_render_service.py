"""Timeline render job execution."""

from __future__ import annotations

import tempfile
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.timeline import RenderJob
from app.repositories.timeline_repository import RenderJobRepository, TimelineRepository
from app.services.render.timeline_render_clips import (
    TimelineClipVideo,
    resolve_timeline_video_clips,
)
from app.services.render.timeline_render_output import persist_timeline_render_output
from app.services.render.video_concat import VideoClip, concat_video_clips

logger = get_logger()


class TimelineRenderService:
    """Execute render_jobs for Timeline Spec v1."""

    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.render_jobs = RenderJobRepository(db)

    async def process_render_job(
        self,
        render_job_id: int,
        user_id: int | None = None,
    ) -> RenderJob | None:
        job = self.render_jobs.get_by_id(render_job_id)
        if job is None or job.is_deleted:
            logger.warning("Timeline render job not found: %s", render_job_id)
            return None

        try:
            return await self._process(job, user_id=user_id)
        except Exception as exc:  # noqa: BLE001 - task boundary must persist failures
            logger.exception("Timeline render job failed: %s", render_job_id)
            return self._mark_failed(
                job,
                {
                    "code": "render_exception",
                    "message": str(exc),
                },
            )

    async def _process(
        self,
        job: RenderJob,
        *,
        user_id: int | None,
    ) -> RenderJob:
        timeline = self.timelines.get_by_id(job.timeline_id)
        if timeline is None or timeline.is_deleted:
            return self._mark_failed(job, {"code": "timeline_not_found"})
        if timeline.version != job.timeline_version:
            return self._mark_failed(
                job,
                {
                    "code": "stale_timeline_version",
                    "current_version": timeline.version,
                    "job_version": job.timeline_version,
                },
            )

        self._mark_running(job, progress=10, log={"code": "resolving_clips"})
        resolved, missing = resolve_timeline_video_clips(self.db, timeline)
        if missing:
            return self._mark_failed(
                job,
                {
                    "code": "missing_clip_videos",
                    "missing_clips": missing,
                    "resolved_clip_count": len(resolved),
                },
            )
        if not resolved:
            return self._mark_failed(
                job,
                {
                    "code": "no_video_clips",
                    "missing_clips": [],
                },
            )

        self._mark_running(
            job,
            progress=35,
            log={"code": "rendering", "clip_count": len(resolved)},
        )
        output_path = await self._render_to_temp_file(resolved)

        self._mark_running(job, progress=80, log={"code": "persisting_output"})
        asset = await persist_timeline_render_output(
            self.db,
            job=job,
            timeline=timeline,
            output_path=output_path,
            clips=resolved,
            user_id=user_id,
        )

        job.status = "succeeded"
        job.progress = 100
        job.output_asset_id = asset.id
        job.log = {
            "code": "render_succeeded",
            "clip_count": len(resolved),
            "output_asset_id": asset.id,
            "output_url": asset.file_url or asset.file_path,
        }
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    async def _render_to_temp_file(self, clips: list[TimelineClipVideo]) -> str:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            output_path = tmp.name
        result = await concat_video_clips(
            clips=[
                VideoClip(
                    url=clip.url,
                    target_duration_seconds=clip.duration_seconds,
                    frame_number=index + 1,
                    description=clip.clip_id,
                )
                for index, clip in enumerate(clips)
            ],
            output_path=output_path,
            audio_url=None,
            keep_original_audio=True,
        )
        if not result.get("success"):
            raise RuntimeError(str(result.get("error") or "timeline render failed"))
        return output_path

    def _mark_running(
        self,
        job: RenderJob,
        *,
        progress: int,
        log: dict[str, Any],
    ) -> None:
        job.status = "running"
        job.progress = progress
        job.log = log
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

    def _mark_failed(self, job: RenderJob, log: dict[str, Any]) -> RenderJob:
        job.status = "failed"
        job.progress = 100
        job.log = log
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
