"""Queue provider-backed video rework for stable Timeline clips."""

from __future__ import annotations

import json
from typing import Any

from app.models.task import TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineRepository,
)
from app.schemas.timeline import (
    TimelineClipVideoReworkTaskRequest,
    TimelineClipVideoReworkTaskResponse,
)
from app.services.timeline_clip_video_grid_reference import (
    build_clip_storyboard_rework_payload,
    build_grid_storyboard_rework_payload,
)
from app.services.timeline_clip_video_rework_context import (
    apply_video_rework_bound_context,
    build_video_rework_bound_context,
)
from app.services.timeline_clip_video_rework_dispatch import (
    dispatch_timeline_clip_video_rework_task,
)
from app.services.timeline_clip_video_rework_helpers import (
    clip_duration_seconds,
    clip_prompt,
    dedupe_strings,
    maybe_int,
    render_preset,
    story_owner_filter,
    string_value,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineClipVideoReworkQueueService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.media_assets = MediaAssetRepository(db)
        self.tasks = TaskRepository(db)

    def queue_video_rework(
        self,
        timeline_id: int,
        clip_id: str,
        payload: TimelineClipVideoReworkTaskRequest,
        current_user: User,
    ) -> TimelineClipVideoReworkTaskResponse:
        timeline = self._get_timeline_or_404(timeline_id, current_user)
        if timeline.version != payload.expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="timeline version conflict",
            )
        clip = self._clip_or_404(timeline, clip_id)
        if clip.get("track_type") != "video":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="video rework requires a video clip",
            )
        task_payload = self._task_payload(timeline, clip_id, clip, payload)
        task = self.tasks.create(
            target_business_id=timeline.business_id,
            title=f"Timeline clip rework - {clip_id}",
            description="Provider-backed Timeline clip video rework",
            task_type=TaskType.VIDEO_GENERATION,
            prompt=task_payload.get("prompt"),
            parameters=json.dumps(task_payload, ensure_ascii=False),
            user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(task)
        dispatch_timeline_clip_video_rework_task(task, task_payload, current_user)
        return TimelineClipVideoReworkTaskResponse(
            task_id=task.id,
            status=str(
                task.status.value if hasattr(task.status, "value") else task.status
            ),
        )

    def _task_payload(
        self,
        timeline: Timeline,
        clip_id: str,
        clip: dict[str, Any],
        payload: TimelineClipVideoReworkTaskRequest,
    ) -> dict[str, Any]:
        clip_storyboard_payload = None
        grid_payload = None
        reference_mode = payload.reference_mode or "start_end"
        bound_context = build_video_rework_bound_context(
            self.db,
            timeline=timeline,
            clip=clip,
            payload=payload,
        )
        if payload.use_clip_storyboard or reference_mode == "clip_storyboard_panel":
            reference_mode = "clip_storyboard_panel"
            clip_storyboard_payload = build_clip_storyboard_rework_payload(
                timeline,
                clip_id,
                clip,
                payload,
                asset_ref_url=self._asset_ref_url,
                fallback_prompt=clip_prompt,
            )
            prompt = clip_storyboard_payload["prompt"]
            start_url = None
            end_url = None
        elif payload.use_storyboard_grid or reference_mode == "storyboard_grid_panel":
            reference_mode = "storyboard_grid_panel"
            grid_payload = build_grid_storyboard_rework_payload(
                timeline,
                clip_id,
                clip,
                payload,
                asset_ref_url=self._asset_ref_url,
                fallback_prompt=clip_prompt,
            )
            prompt = grid_payload["prompt"]
            start_url = None
            end_url = None
        else:
            prompt = clip_prompt(clip, payload.prompt)
            start_url = self._start_frame_url(clip)
            end_url = self._end_frame_url(clip) if payload.use_end_frame else None

        if not (prompt or start_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline clip rework requires a prompt or start frame",
            )
        task_payload = {
            "timeline_id": timeline.id,
            "timeline_business_id": timeline.business_id,
            "timeline_version": timeline.version,
            "clip_id": clip_id,
            "action": payload.action,
            "asset_role": payload.asset_role or "generated_video",
            "reason": payload.reason,
            "prompt": prompt,
            "image_url": start_url,
            "end_image_url": end_url,
            "duration": payload.duration or clip_duration_seconds(clip),
            "model": payload.model,
            "fps": payload.fps,
            "resolution": payload.resolution,
            "ratio": payload.ratio,
            "return_last_frame": payload.return_last_frame,
            "auto_render": True,
            "render_type": "final",
            "render_preset": render_preset(timeline),
        }
        if clip_storyboard_payload:
            task_payload.update(
                {
                    "reference_mode": reference_mode,
                    "reference_images": clip_storyboard_payload["reference_images"],
                    "clip_storyboard": clip_storyboard_payload["clip_storyboard"],
                }
            )
        elif grid_payload:
            task_payload.update(
                {
                    "reference_mode": reference_mode,
                    "reference_images": grid_payload["reference_images"],
                    "storyboard_grid": grid_payload["storyboard_grid"],
                }
            )
        elif payload.reference_images:
            task_payload["reference_images"] = dedupe_strings(payload.reference_images)
        apply_video_rework_bound_context(
            task_payload,
            payload=payload,
            context=bound_context,
            reference_mode=reference_mode,
        )
        return task_payload

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
            user_id=story_owner_filter(current_user),
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )
        return timeline

    def _start_frame_url(self, clip: dict[str, Any]) -> str | None:
        return (
            self._asset_ref_url(clip.get("start_frame_asset_ref"))
            or self._asset_ref_url(clip.get("storyboard_image_asset_ref"))
            or string_value(clip.get("start_image_url"))
            or string_value(clip.get("image_url"))
        )

    def _end_frame_url(self, clip: dict[str, Any]) -> str | None:
        return self._asset_ref_url(clip.get("end_frame_asset_ref")) or string_value(
            clip.get("end_image_url")
        )

    def _asset_ref_url(self, asset_ref: Any) -> str | None:
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
