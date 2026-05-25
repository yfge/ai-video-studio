"""Queue provider-backed video rework for stable Timeline clips."""

from __future__ import annotations

import json
from typing import Any, Optional

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
from app.services.timeline_clip_video_rework_dispatch import (
    dispatch_timeline_clip_video_rework_task,
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
        prompt = self._prompt(clip, payload.prompt)
        start_url = self._start_frame_url(clip)
        end_url = self._end_frame_url(clip) if payload.use_end_frame else None
        if not (prompt or start_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline clip rework requires a prompt or start frame",
            )
        return {
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
            "duration": payload.duration or self._clip_duration_seconds(clip),
            "model": payload.model,
            "fps": payload.fps,
            "resolution": payload.resolution,
            "ratio": payload.ratio,
            "return_last_frame": payload.return_last_frame,
        }

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
            user_id=self._story_owner_filter(current_user),
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
            or self._string_value(clip.get("start_image_url"))
            or self._string_value(clip.get("image_url"))
        )

    def _end_frame_url(self, clip: dict[str, Any]) -> str | None:
        return self._asset_ref_url(
            clip.get("end_frame_asset_ref")
        ) or self._string_value(clip.get("end_image_url"))

    def _asset_ref_url(self, asset_ref: Any) -> str | None:
        if not isinstance(asset_ref, dict):
            return None
        for key in ("file_url", "url", "image_url", "video_url", "file_path"):
            value = self._string_value(asset_ref.get(key))
            if value:
                return value
        asset_id = self._maybe_int(
            asset_ref.get("media_asset_id")
            or asset_ref.get("asset_id")
            or asset_ref.get("image_asset_id")
            or asset_ref.get("video_asset_id")
        )
        asset = self.media_assets.get_by_id(asset_id) if asset_id else None
        if asset is None or asset.is_deleted:
            return None
        return asset.file_url or asset.file_path

    @staticmethod
    def _prompt(clip: dict[str, Any], override: str | None) -> str | None:
        if override and override.strip():
            return override.strip()
        for key in ("ai_prompt", "prompt", "description", "text", "label"):
            value = TimelineClipVideoReworkQueueService._string_value(clip.get(key))
            if value:
                return value
        return None

    @staticmethod
    def _clip_duration_seconds(clip: dict[str, Any]) -> float:
        start_ms = TimelineClipVideoReworkQueueService._maybe_int(clip.get("start_ms"))
        end_ms = TimelineClipVideoReworkQueueService._maybe_int(clip.get("end_ms"))
        if start_ms is not None and end_ms is not None and end_ms > start_ms:
            return max((end_ms - start_ms) / 1000, 0.1)
        duration_ms = TimelineClipVideoReworkQueueService._maybe_int(
            clip.get("duration_ms")
        )
        if duration_ms and duration_ms > 0:
            return max(duration_ms / 1000, 0.1)
        duration_seconds = TimelineClipVideoReworkQueueService._maybe_float(
            clip.get("duration_seconds")
        )
        return max(duration_seconds, 0.1) if duration_seconds else 5.0

    @staticmethod
    def _story_owner_filter(current_user: User) -> Optional[int]:
        if getattr(current_user, "is_superuser", False) or getattr(
            current_user, "is_admin", False
        ):
            return None
        return current_user.id

    @staticmethod
    def _string_value(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _maybe_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
