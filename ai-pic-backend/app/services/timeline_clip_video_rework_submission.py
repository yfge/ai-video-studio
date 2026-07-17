"""Submit provider video tasks for Timeline clip rework."""

from __future__ import annotations

from typing import Any

from app.models.task import TaskStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.video_generation_task_repository import (
    VideoGenerationTaskRepository,
)
from app.services.video.video_task_dispatcher import VideoTaskDispatcher
from app.services.video.video_task_submission_failure import (
    TimelineVideoSubmissionAttempt,
    persist_timeline_video_submission_failure,
)
from app.services.video.video_task_submission_helpers import submit_provider_task
from app.services.video.video_task_submission_persistence import (
    persist_submitted_timeline_video_task,
)
from app.services.video.video_task_utils import (
    abs_url,
    coerce_duration,
    normalize_submission_options,
)


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
        reference_images = self._reference_images(payload.get("reference_images"))
        target_duration_seconds = float(
            payload.get("target_duration_seconds") or payload.get("duration") or 5.0
        )
        request_duration_seconds = coerce_duration(target_duration_seconds)
        model_type = self._model_type(start_url, reference_images)
        attempt = TimelineVideoSubmissionAttempt(
            task_id=task_id,
            user_id=user_id,
            prompt=prompt,
            start_url=start_url,
            end_url=end_url,
            reference_images=reference_images,
            target_duration_seconds=target_duration_seconds,
            provider_duration_seconds=request_duration_seconds,
            model_type=model_type,
            opts=opts,
            timeline_rework=self._timeline_rework_context(payload),
        )
        try:
            response = submit_provider_task(
                self.dispatcher,
                prompt=prompt,
                start_url=start_url,
                end_url=end_url,
                reference_images=reference_images,
                duration=request_duration_seconds,
                opts=opts,
                target_duration_seconds=target_duration_seconds,
            )
        except Exception as exc:
            error_message = f"视频任务提交异常: {exc}"
            self._record_failure(attempt, error_message, None)
            self._fail_parent(task, error_message)
        if not response.success:
            error_message = response.error or "视频重做任务提交失败"
            self._record_failure(attempt, error_message, response)
            self._fail_parent(task, error_message)

        provider_task_id = self._string_value((response.data or {}).get("task_id"))
        if not provider_task_id:
            error_message = "未返回任务ID"
            self._record_failure(attempt, error_message, response)
            self._fail_parent(task, error_message)
        model_type = self._response_model_type(response) or model_type

        provider_duration_seconds = int(
            (response.data or {}).get("provider_duration_seconds")
            or (response.data or {}).get("duration")
            or request_duration_seconds
        )
        persist_submitted_timeline_video_task(
            self.video_tasks,
            task_id=task_id,
            user_id=user_id,
            response=response,
            provider_task_id=provider_task_id,
            prompt=prompt,
            start_url=start_url,
            end_url=end_url,
            reference_images=reference_images,
            target_duration_seconds=target_duration_seconds,
            provider_duration_seconds=provider_duration_seconds,
            model_type=model_type,
            opts=opts,
            timeline_rework=self._timeline_rework_context(payload),
        )
        self.db.commit()

    def _record_failure(
        self,
        attempt: TimelineVideoSubmissionAttempt,
        error_message: str,
        response: Any | None,
    ) -> None:
        persist_timeline_video_submission_failure(
            self.video_tasks,
            attempt=attempt,
            error_message=error_message,
            response=response,
        )

    def _fail_parent(self, task: Any, error_message: str) -> None:
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        self.db.commit()
        raise RuntimeError(error_message)

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
            "operator_reviewed": payload.get("operator_reviewed"),
            "reference_mode": payload.get("reference_mode"),
            "clip_storyboard": payload.get("clip_storyboard"),
            "storyboard_grid": payload.get("storyboard_grid"),
            "character_virtual_ip_ids": payload.get("character_virtual_ip_ids"),
            "character_reference_images": payload.get("character_reference_images"),
            "environment_reference_images": payload.get("environment_reference_images"),
            "bound_context": payload.get("bound_context"),
        }

    @staticmethod
    def _abs_optional(value: Any) -> str | None:
        text = TimelineClipVideoReworkSubmissionService._string_value(value)
        return abs_url(text) if text else None

    @staticmethod
    def _reference_images(value: Any) -> list[str] | None:
        if not isinstance(value, list):
            return None
        refs = [
            abs_url(item.strip())
            for item in value
            if isinstance(item, str) and item.strip()
        ]
        return refs or None

    @staticmethod
    def _model_type(
        start_url: str | None,
        reference_images: list[str] | None,
    ) -> str:
        return "image_to_video" if start_url or reference_images else "text_to_video"

    @staticmethod
    def _response_model_type(response: Any) -> str | None:
        value = getattr(response, "model_type", None)
        if hasattr(value, "value"):
            return str(value.value)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _string_value(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
