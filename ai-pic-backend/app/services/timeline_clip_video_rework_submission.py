"""Submit provider video tasks for Timeline clip rework."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from app.models.task import TaskStatus
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.video_generation_task_repository import (
    VideoGenerationTaskRepository,
)
from app.services.video.video_task_dispatcher import VideoTaskDispatcher
from app.services.video.video_task_generation_metadata import (
    build_video_generation_metadata,
)
from app.services.video.video_task_submission_helpers import submit_provider_task
from app.services.video.video_task_utils import (
    abs_url,
    build_parameters_payload,
    coerce_duration,
    normalize_submission_options,
)

VIDEO_REWORK_TASK_TIMEOUT = timedelta(hours=1)


class TimelineClipVideoReworkSubmissionService:
    def __init__(self, db, ai_manager):
        self.db = db
        self.tasks = TaskRepository(db)
        self.video_tasks = VideoGenerationTaskRepository(db)
        self.dispatcher = VideoTaskDispatcher(ai_manager)

    def submit(self, *, task_id: int, payload: dict[str, Any], user_id: int) -> None:
        task = self.tasks.get_by_id(task_id)
        if not task:
            raise RuntimeError("任务不存在")
        task.status = TaskStatus.PROCESSING
        self.db.commit()

        opts = normalize_submission_options(payload)
        prompt = self._string_value(payload.get("prompt"))
        start_url = self._abs_optional(payload.get("image_url"))
        end_url = self._abs_optional(payload.get("end_image_url"))
        target_duration_seconds = float(payload.get("duration") or 5.0)
        request_duration_seconds = coerce_duration(target_duration_seconds)
        response = submit_provider_task(
            self.dispatcher,
            prompt=prompt,
            start_url=start_url,
            end_url=end_url,
            duration=request_duration_seconds,
            opts=opts,
        )
        if not response.success:
            self._record_failure(task_id, user_id, prompt, response.error)
            task.status = TaskStatus.FAILED
            task.error_message = response.error or "视频重做任务提交失败"
            self.db.commit()
            raise RuntimeError(task.error_message)

        provider_task_id = self._string_value((response.data or {}).get("task_id"))
        if not provider_task_id:
            self._record_failure(task_id, user_id, prompt, "未返回任务ID")
            task.status = TaskStatus.FAILED
            task.error_message = "未返回任务ID"
            self.db.commit()
            raise RuntimeError(task.error_message)

        provider_duration_seconds = int(
            (response.data or {}).get("duration") or request_duration_seconds
        )
        self._create_video_task(
            task_id=task_id,
            user_id=user_id,
            response=response,
            provider_task_id=provider_task_id,
            prompt=prompt,
            start_url=start_url,
            end_url=end_url,
            target_duration_seconds=target_duration_seconds,
            provider_duration_seconds=provider_duration_seconds,
            opts=opts,
            payload=payload,
        )
        self.db.commit()

    def _create_video_task(
        self,
        *,
        task_id: int,
        user_id: int,
        response,
        provider_task_id: str,
        prompt: str | None,
        start_url: str | None,
        end_url: str | None,
        target_duration_seconds: float,
        provider_duration_seconds: int,
        opts: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        params_payload = build_parameters_payload(
            prompt,
            start_url,
            end_url,
            None,
            provider_duration_seconds,
            opts,
            target_duration_seconds=round(float(target_duration_seconds), 3),
            provider_duration_seconds=provider_duration_seconds,
        )
        params_payload["timeline_rework"] = self._timeline_rework_context(payload)
        self.video_tasks.create(
            task_id=task_id,
            script_id=None,
            frame_index=None,
            user_id=user_id,
            provider=response.provider,
            provider_task_id=provider_task_id,
            model=response.model,
            model_type="image_to_video" if start_url else "text_to_video",
            prompt=prompt,
            parameters=json.dumps(params_payload, ensure_ascii=False),
            generation_metadata=build_video_generation_metadata(
                response.provider,
                response.model,
                provider_task_id,
                "image_to_video" if start_url else "text_to_video",
                params_payload,
            ),
            status=VideoGenerationTaskStatus.SUBMITTED,
            submitted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + VIDEO_REWORK_TASK_TIMEOUT,
        )

    def _record_failure(
        self,
        task_id: int,
        user_id: int,
        prompt: str | None,
        error_message: str | None,
    ) -> None:
        self.video_tasks.create(
            task_id=task_id,
            script_id=None,
            frame_index=None,
            user_id=user_id,
            provider="unknown",
            provider_task_id="",
            model=None,
            model_type="image_to_video",
            prompt=prompt,
            parameters=json.dumps({}, ensure_ascii=False),
            status=VideoGenerationTaskStatus.FAILED,
            error_message=error_message or "视频重做任务提交失败",
        )

    @staticmethod
    def _timeline_rework_context(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "timeline_id": payload.get("timeline_id"),
            "timeline_business_id": payload.get("timeline_business_id"),
            "timeline_version": payload.get("timeline_version"),
            "clip_id": payload.get("clip_id"),
            "action": payload.get("action"),
            "asset_role": payload.get("asset_role") or "generated_video",
            "reason": payload.get("reason"),
            "auto_render": payload.get("auto_render"),
            "render_type": payload.get("render_type"),
            "render_preset": payload.get("render_preset"),
        }

    @staticmethod
    def _abs_optional(value: Any) -> str | None:
        text = TimelineClipVideoReworkSubmissionService._string_value(value)
        return abs_url(text) if text else None

    @staticmethod
    def _string_value(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
