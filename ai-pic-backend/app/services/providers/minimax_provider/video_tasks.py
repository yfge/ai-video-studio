from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from app.core.logging import get_logger
from app.services.minimax_client import MinimaxAPIError, MinimaxClient
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.providers.polling_utils import TaskStatus, minimax_status_mapper

from .video import _retrieve_video_file

logger = get_logger(__name__)


def _coerce_duration(value: Any) -> int:
    try:
        dur = int(value)
    except (TypeError, ValueError):
        return 6
    if dur <= 0:
        return 6
    return dur


def _build_payload(
    *,
    model: str,
    first_frame_image: str,
    prompt: Optional[str],
    last_frame_image: Optional[str],
    duration: int,
    resolution: str,
    prompt_optimizer: bool,
    fast_pretreatment: bool,
    aigc_watermark: bool,
) -> tuple[Dict[str, Any], int]:
    dur_int = _coerce_duration(duration)
    payload = {
        "model": model,
        "first_frame_image": first_frame_image,
        "duration": dur_int,
        "resolution": resolution,
        "prompt_optimizer": prompt_optimizer,
        "aigc_watermark": aigc_watermark,
    }

    if prompt:
        payload["prompt"] = prompt
    if last_frame_image:
        payload["last_frame_image"] = last_frame_image
    if fast_pretreatment and model in [
        "MiniMax-Hailuo-2.3",
        "MiniMax-Hailuo-2.3-Fast",
        "MiniMax-Hailuo-02",
    ]:
        payload["fast_pretreatment"] = fast_pretreatment
    return payload, dur_int


async def _submit_payload(
    *,
    client: MinimaxClient,
    provider_name: str,
    model: str,
    payload: Dict[str, Any],
    duration: int,
    format_error: Callable,
) -> AIResponse:
    try:
        response_data = await client.post_json("/video_generation", payload)
        task_id = response_data.get("task_id")
        if not task_id:
            return AIResponse(
                success=False,
                error="No task_id in response",
                provider=provider_name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

        return AIResponse(
            success=True,
            data={"task_id": task_id, "duration": duration},
            provider=provider_name,
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )

    except MinimaxAPIError as err:
        return AIResponse(
            success=False,
            error=format_error(err),
            provider=provider_name,
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )


async def submit_video_task(
    client: MinimaxClient,
    provider_name: str,
    first_frame_image: str,
    prompt: Optional[str],
    last_frame_image: Optional[str],
    model: str,
    duration: int,
    resolution: str,
    prompt_optimizer: bool,
    fast_pretreatment: bool,
    aigc_watermark: bool,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    payload, dur_int = _build_payload(
        model=model,
        first_frame_image=first_frame_image,
        prompt=prompt,
        last_frame_image=last_frame_image,
        duration=duration,
        resolution=resolution,
        prompt_optimizer=prompt_optimizer,
        fast_pretreatment=fast_pretreatment,
        aigc_watermark=aigc_watermark,
    )
    return await _submit_payload(
        client=client,
        provider_name=provider_name,
        model=model,
        payload=payload,
        duration=dur_int,
        format_error=format_error,
    )


async def fetch_video_task_status(
    client: MinimaxClient,
    provider_name: str,
    task_id: str,
    format_error: Callable = str,
) -> AIResponse:
    try:
        data = await client.get_json(
            "/query/video_generation", params={"task_id": task_id}
        )
        logger.info(
            "Video task status http response: provider=%s task_id=%s body=%s",
            provider_name,
            task_id,
            json.dumps(data, ensure_ascii=False),
        )
        status = minimax_status_mapper(data)
        video_url = None
        file_id = data.get("file_id")

        if status in (TaskStatus.SUCCESS, TaskStatus.COMPLETED) and file_id:
            file_info = await _retrieve_video_file(client, file_id)
            if file_info:
                video_url = file_info.get("download_url")

        return AIResponse(
            success=True,
            data={
                "status": status.value,
                "video_url": video_url,
                "file_id": file_id,
                "video_width": data.get("video_width"),
                "video_height": data.get("video_height"),
                "raw": data,
            },
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )

    except MinimaxAPIError as err:
        return AIResponse(
            success=False,
            error=format_error(err),
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )
