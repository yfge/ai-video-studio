"""
MiniMax video generation module.

Contains video generation, task polling, and file retrieval.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from app.services.minimax_client import MinimaxAPIError, MinimaxClient

logger = logging.getLogger(__name__)

from app.services.video.video_duration import resolve_duration_ceil

from ..base import AIModelType, AIResponse, AITaskType
from ..polling_utils import TaskPoller, minimax_status_mapper


async def generate_video(
    client: MinimaxClient,
    provider_name: str,
    first_frame_image: str,
    prompt: Optional[str] = None,
    last_frame_image: Optional[str] = None,
    model: str = "MiniMax-Hailuo-2.3",
    duration: int = 6,
    resolution: str = "768P",
    prompt_optimizer: bool = True,
    fast_pretreatment: bool = False,
    aigc_watermark: bool = False,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """
    Generate video from image(s) using MiniMax video generation API.

    Endpoint: POST /v1/video_generation
    Polling: GET /v1/query/video_generation

    Args:
        client: MiniMax API client
        provider_name: Provider name for response
        first_frame_image: First frame image (URL or base64 data URL)
        prompt: Text description (max 2000 chars), supports camera control directives
        last_frame_image: Last frame image (optional, for first-last frame generation)
        model: Video generation model name
        duration: Video duration in seconds (6 or 10)
        resolution: Video resolution (512P/720P/768P/1080P, depends on model)
        prompt_optimizer: Auto-optimize prompt (default True)
        fast_pretreatment: Faster prompt optimization (Hailuo 2.3/02 only)
        aigc_watermark: Add watermark to generated video
        format_error: Error formatting function

    Returns:
        AIResponse with video URL or error
    """
    try:
        dur_int = resolve_duration_ceil(
            target_seconds=duration, allowed_durations=[6, 10]
        ).provider_seconds

        # Build request payload
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

        # Create video generation task
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

        # Poll task status
        result = await _poll_video_task(client, task_id)

        if result and "video_url" in result:
            return AIResponse(
                success=True,
                data={
                    "video_url": result["video_url"],
                    "file_id": result.get("file_id"),
                    "duration": dur_int,
                    "width": result.get("video_width"),
                    "height": result.get("video_height"),
                },
                provider=provider_name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
                metadata={
                    "task_id": task_id,
                    "resolution": resolution,
                    "duration": dur_int,
                },
            )
        else:
            return AIResponse(
                success=False,
                error="Video generation task failed or timed out",
                provider=provider_name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
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


async def _poll_video_task(
    client: MinimaxClient, task_id: str
) -> Optional[Dict[str, Any]]:
    """
    Poll video generation task status.

    Endpoint: GET /v1/query/video_generation?task_id={task_id}
    """

    async def poll_fn() -> Dict[str, Any]:
        return await client.get_json(
            "/query/video_generation", params={"task_id": task_id}
        )

    async def extract_result(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract video info and download URL from response"""
        file_id = data.get("file_id")
        if not file_id:
            return {}

        # Retrieve video file information
        file_info = await _retrieve_video_file(client, file_id)
        if file_info:
            return {
                "video_url": file_info.get("download_url"),
                "file_id": file_id,
                "video_width": data.get("video_width"),
                "video_height": data.get("video_height"),
            }
        return {}

    poller = TaskPoller(
        poll_fn=poll_fn,
        status_mapper=minimax_status_mapper,
        result_extractor=extract_result,
        max_attempts=180,  # 30 minutes with 10s interval
        initial_delay=10.0,
        task_id=task_id,
        task_type="video",
    )

    return await poller.poll()


async def _retrieve_video_file(
    client: MinimaxClient, file_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve video file information including download URL.

    Endpoint: GET /v1/files/retrieve?file_id={file_id}

    Args:
        client: MiniMax API client
        file_id: File ID from successful video generation task

    Returns:
        File information dict with download_url, or None on error
    """
    try:
        response_data = await client.get_json(
            "/files/retrieve", params={"file_id": file_id}
        )

        file_obj = response_data.get("file", {})
        return {
            "file_id": file_obj.get("file_id"),
            "download_url": file_obj.get("download_url"),
            "filename": file_obj.get("filename"),
            "bytes": file_obj.get("bytes"),
            "created_at": file_obj.get("created_at"),
        }

    except MinimaxAPIError as err:
        logger.warning("Error retrieving video file %s: %s", file_id, err)
        return None
