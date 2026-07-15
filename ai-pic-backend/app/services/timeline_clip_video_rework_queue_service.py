"""Queue provider-backed video rework for stable Timeline clips."""

from __future__ import annotations

import json
from typing import Any

from app.models.task import TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline import (
    TimelineClipVideoReworkTaskRequest,
    TimelineClipVideoReworkTaskResponse,
)
from app.services.timeline_clip_video_grid_reference import (
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
    render_preset,
    render_ratio,
    requires_operator_review,
    story_owner_filter,
)
from app.services.timeline_clip_video_rework_images import (
    TimelineClipVideoReworkImageResolver,
)
from app.services.timeline_clip_video_storyboard_reference import (
    build_clip_storyboard_rework_payload,
)
from app.services.timeline_clip_visual_prompt_builder import (
    build_timeline_clip_video_motion_prompt,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TimelineClipVideoReworkQueueService:
    def __init__(self, db: Session):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.images = TimelineClipVideoReworkImageResolver(db)
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
        if requires_operator_review(clip) and not payload.operator_reviewed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="operator review required before video generation",
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
        status_value = getattr(task.status, "value", task.status)
        return TimelineClipVideoReworkTaskResponse(
            task_id=task.id, status=str(status_value)
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
        target_duration = payload.duration or clip_duration_seconds(clip)
        bound_context = build_video_rework_bound_context(
            self.db,
            timeline=timeline,
            clip=clip,
            payload=payload,
        )
        if payload.use_clip_storyboard or reference_mode in {
            "clip_storyboard_sheet",
            "clip_storyboard_panel",
        }:
            prompt_metadata = {}
            if reference_mode != "clip_storyboard_panel":
                reference_mode = "clip_storyboard_sheet"
            clip_storyboard_payload = build_clip_storyboard_rework_payload(
                timeline,
                clip_id,
                clip,
                payload,
                duration_seconds=target_duration,
                asset_ref_url=self.images.asset_ref_url,
                fallback_prompt=clip_prompt,
            )
            prompt = clip_storyboard_payload["prompt"]
            start_url = None
            end_url = None
        elif payload.use_storyboard_grid or reference_mode == "storyboard_grid_panel":
            prompt_metadata = {}
            reference_mode = "storyboard_grid_panel"
            grid_payload = build_grid_storyboard_rework_payload(
                timeline,
                clip_id,
                clip,
                payload,
                asset_ref_url=self.images.asset_ref_url,
                fallback_prompt=clip_prompt,
            )
            prompt = grid_payload["prompt"]
            start_url = None
            end_url = None
        else:
            prompt, prompt_metadata = build_timeline_clip_video_motion_prompt(
                clip,
                payload.prompt,
            )
            start_url = self.images.start_frame_url(timeline, clip_id, clip)
            end_url = self.images.end_frame_url(clip) if payload.use_end_frame else None

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
            "duration": target_duration,
            "model": payload.model,
            "fps": payload.fps,
            "resolution": payload.resolution,
            "ratio": payload.ratio or render_ratio(timeline),
            "return_last_frame": payload.return_last_frame,
            "operator_reviewed": payload.operator_reviewed,
            "auto_render": True,
            "render_type": "final",
            "render_preset": render_preset(timeline),
            **prompt_metadata,
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
