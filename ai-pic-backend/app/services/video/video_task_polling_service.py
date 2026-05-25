from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

import anyio
from app.core.logging import get_logger
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.repositories.video_generation_task_repository import (
    VideoGenerationTaskRepository,
)
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_generation_service import VideoGenerationService
from app.services.video.video_task_generation_metadata import (
    build_video_generation_metadata,
)
from app.services.video.video_task_polling_logging import log_pending_tasks
from app.services.video.video_task_polling_parent_task import refresh_parent_task_status
from app.services.video.video_task_storyboard_updater import apply_storyboard_result
from app.services.video.video_task_timeline_rework_updater import (
    apply_timeline_rework_result,
)
from app.services.video.video_task_utils import load_parameters, map_provider_status


class VideoTaskPollingService:
    def __init__(self, db, ai_manager):
        self.db = db
        self.repo = VideoGenerationTaskRepository(db)
        self.ai_manager = ai_manager
        self.logger = get_logger("video_task_polling")

    def poll_pending_tasks(self, limit: int = 50) -> int:
        pending = self.repo.list_pending(limit=limit)
        log_pending_tasks(self.logger, pending, limit)
        if not pending:
            return 0

        processor = VideoGenerationService(ai_manager=self.ai_manager)
        now = datetime.utcnow()
        for item in pending:
            self._process_pending_item(item, processor, now)
        return len(pending)

    def _process_pending_item(
        self,
        item: VideoGenerationTask,
        processor: VideoGenerationService,
        now: datetime,
    ) -> None:
        if item.expires_at and item.expires_at < now:
            self._mark_timeout(item, now)
            return

        response = self._poll_provider(item, now)
        if not response or not response.success:
            self._handle_poll_failure(item, response)
            return

        mapped = map_provider_status((response.data or {}).get("status"))
        if mapped == VideoGenerationTaskStatus.PROCESSING:
            self._mark_processing(item)
            return
        if mapped in {
            VideoGenerationTaskStatus.FAILED,
            VideoGenerationTaskStatus.TIMEOUT,
        }:
            self._mark_failed(item, response, now, mapped)
            return

        self._handle_success(item, response, processor, now)

    def _poll_provider(
        self, item: VideoGenerationTask, now: datetime
    ) -> Optional[AIResponse]:
        response = anyio.run(self._fetch_task_status, item)
        item.last_polled_at = now
        return response

    def _handle_poll_failure(
        self, item: VideoGenerationTask, response: Optional[AIResponse]
    ) -> None:
        item.status = VideoGenerationTaskStatus.PROCESSING
        item.error_message = response.error if response else "轮询失败"
        self.db.commit()

    def _mark_processing(self, item: VideoGenerationTask) -> None:
        item.status = VideoGenerationTaskStatus.PROCESSING
        self.db.commit()

    def _mark_failed(
        self,
        item: VideoGenerationTask,
        response: AIResponse,
        now: datetime,
        status: VideoGenerationTaskStatus,
        error_override: Optional[str] = None,
    ) -> None:
        item.status = status
        item.completed_at = now
        error_message = error_override or (response.data or {}).get("error")
        if not error_message:
            error_message = (
                "任务超时"
                if status == VideoGenerationTaskStatus.TIMEOUT
                else "任务失败"
            )
        item.error_message = error_message
        self.db.commit()
        refresh_parent_task_status(self.db, self.repo, item.task_id)

    def _handle_success(
        self,
        item: VideoGenerationTask,
        response: AIResponse,
        processor: VideoGenerationService,
        now: datetime,
    ) -> None:
        payload = response.data or {}
        video_url = payload.get("video_url")
        video_bytes_base64 = payload.get("video_bytes_base64")
        if not (video_url or video_bytes_base64):
            self._mark_failed(
                item,
                response,
                now,
                VideoGenerationTaskStatus.FAILED,
                error_override="任务完成但未返回视频内容",
            )
            return

        params = load_parameters(item.parameters)
        result_payload = self._build_result_payload(item, response, processor, params)
        self._persist_success(item, result_payload, params, now)

    def _build_result_payload(
        self,
        item: VideoGenerationTask,
        response: AIResponse,
        processor: VideoGenerationService,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        return anyio.run(
            processor._process_successful_response,
            self._build_ai_response(item, response),
            params.get("prompt"),
            params.get("image_url"),
            params.get("end_image_url"),
            params.get("duration") or 5,
            params.get("fps") or 24,
            params.get("resolution") or "720p",
            params.get("target_duration_seconds"),
        )

    def _persist_success(
        self,
        item: VideoGenerationTask,
        result_payload: Dict[str, Any],
        params: Dict[str, Any],
        now: datetime,
    ) -> None:
        item.result = json.dumps(result_payload, ensure_ascii=False)
        item.generation_metadata = build_video_generation_metadata(
            item.provider,
            item.model,
            item.provider_task_id,
            item.model_type,
            params,
            result_payload,
        )
        item.status = VideoGenerationTaskStatus.SUCCEEDED
        item.completed_at = now
        self.db.commit()
        if params.get("timeline_rework"):
            apply_timeline_rework_result(self.db, item, result_payload, params)
        elif item.script_id is not None and item.frame_index is not None:
            apply_storyboard_result(self.db, item, result_payload, params)
        refresh_parent_task_status(self.db, self.repo, item.task_id)

    async def _fetch_task_status(self, item: VideoGenerationTask):
        provider = self.ai_manager.providers.get(item.provider)
        if not provider or not hasattr(provider, "fetch_video_task_status"):
            return None
        return await provider.fetch_video_task_status(item.provider_task_id)

    def _build_ai_response(self, item: VideoGenerationTask, response) -> AIResponse:
        model_type = (
            AIModelType.IMAGE_TO_VIDEO
            if item.model_type == "image_to_video"
            else AIModelType.TEXT_TO_VIDEO
        )
        return AIResponse(
            success=True,
            data={
                "video_url": (response.data or {}).get("video_url"),
                "download_url": (response.data or {}).get("download_url"),
                "thumbnail_url": (response.data or {}).get("thumbnail_url"),
                "last_frame_url": (response.data or {}).get("last_frame_url"),
                "video_bytes_base64": (response.data or {}).get("video_bytes_base64"),
                "video_mime_type": (response.data or {}).get("video_mime_type"),
            },
            provider=item.provider,
            model=item.model or "unknown",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type,
            metadata={"task_id": item.provider_task_id},
        )

    def _mark_timeout(self, item: VideoGenerationTask, now: datetime) -> None:
        item.status = VideoGenerationTaskStatus.TIMEOUT
        item.completed_at = now
        item.error_message = "任务超时"
        self.db.commit()
        refresh_parent_task_status(self.db, self.repo, item.task_id)
