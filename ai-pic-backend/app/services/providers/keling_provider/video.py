"""
Keling video generation module.

Contains image-to-video and multi-image video generation functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import httpx

from app.services.video.video_duration import resolve_duration_ceil

from ..base import AIModelType, AIResponse, AITaskType
from ..polling_utils import TaskPoller, keling_status_mapper

if TYPE_CHECKING:
    pass


async def poll_video_task(
    client: httpx.AsyncClient,
    base_url: str,
    task_id: str,
    get_auth_headers: Callable[[], Dict[str, str]],
) -> Optional[Dict[str, Any]]:
    """
    Poll video generation task status.

    Endpoint: GET /v1/videos/image2video/{task_id}
    """

    async def poll_fn() -> Dict[str, Any]:
        response = await client.get(
            f"{base_url}/v1/videos/image2video/{task_id}",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def extract_result(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract video URL from response"""
        task_result = data.get("task_result", {})
        videos = task_result.get("videos", [])
        if videos and len(videos) > 0:
            return {"video_url": videos[0].get("url")}
        return {}

    poller = TaskPoller(
        poll_fn=poll_fn,
        status_mapper=keling_status_mapper,
        result_extractor=extract_result,
        max_attempts=180,  # 30 minutes with 10s interval
        initial_delay=10.0,
        task_id=task_id,
        task_type="video",
    )

    return await poller.poll()


async def generate_video(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    prompt: Optional[str] = None,
    image: Optional[str] = None,
    image_url: Optional[str] = None,
    image_tail: Optional[str] = None,
    end_image_url: Optional[str] = None,
    model: str = "kling-v2-1",
    mode: str = "pro",
    duration: int = 5,
    resolution: Optional[str] = None,
    ratio: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    cfg_scale: Optional[float] = None,
    camera_control: Optional[Dict[str, Any]] = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """
    Generate video from image using Keling AI.

    Endpoint: POST /v1/videos/image2video
    Polling: GET /v1/videos/image2video/{task_id}

    Args:
        client: HTTP client
        base_url: API base URL
        provider_name: Provider name for response
        get_auth_headers: Function to get fresh auth headers
        prompt: Text description for video generation
        image: First frame image (required, URL or base64)
        image_url: Alias for first frame
        image_tail: Last frame image (optional)
        end_image_url: Alias for last frame
        model: Model name
        mode: Generation mode ("std" or "pro")
        duration: Video duration in seconds (5 or 10)
        resolution: Output resolution (e.g., "720P", "1080P")
        ratio: Aspect ratio (e.g., "16:9")
        negative_prompt: Negative prompt
        cfg_scale: Prompt relevance (V1 models only)
        camera_control: Camera movement configuration

    Returns:
        AIResponse with generated video URL
    """
    primary_image = image or image_url
    tail_image = image_tail or end_image_url

    if not primary_image:
        return AIResponse(
            success=False,
            error="image parameter is required for video generation",
            provider=provider_name,
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    try:
        # Keling video only supports 5s/10s; resolve via ceil-to-allowed strategy
        try:
            dur_int = int(duration)
        except (TypeError, ValueError):
            dur_int = 5
        allowed_durations = [5, 10]
        dur_int = resolve_duration_ceil(
            target_seconds=dur_int,
            allowed_durations=allowed_durations,
        ).provider_seconds

        # Build request payload
        mode_used = str(mode or "").strip().lower()
        if mode_used != "pro":
            mode_used = "pro"
        request_data = {
            "model_name": model,
            "image": primary_image,
            "mode": mode_used,
            "duration": dur_int,
        }

        # Add optional parameters
        if tail_image:
            request_data["image_tail"] = tail_image
        if prompt:
            request_data["prompt"] = prompt
        if negative_prompt:
            request_data["negative_prompt"] = negative_prompt
        if cfg_scale is not None and not model.startswith("kling-v2"):
            # cfg_scale only supported by V1 models
            request_data["cfg_scale"] = cfg_scale
        if camera_control:
            request_data["camera_control"] = camera_control

        # Resolution and aspect ratio
        resolved_resolution = (
            resolution
            or kwargs.get("resolution")
            or kwargs.get("rs")
            or kwargs.get("output_resolution")
        )
        if resolved_resolution:
            request_data["resolution"] = str(resolved_resolution).upper()

        resolved_ratio = ratio or kwargs.get("ratio") or kwargs.get("aspect_ratio")
        if resolved_ratio:
            request_data["aspect_ratio"] = str(resolved_ratio)

        # Add any additional parameters from kwargs
        for key in ["dynamic_masks", "static_mask", "voice_list", "sound"]:
            if key in kwargs:
                request_data[key] = kwargs[key]

        # Create video generation task
        try:
            response = await client.post(
                f"{base_url}/v1/videos/image2video",
                json=request_data,
                headers=get_auth_headers(),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail: str = ""
            try:
                payload = exc.response.json()
                code = payload.get("code")
                msg = payload.get("message") or payload.get("msg")
                detail = f"code={code}, message={msg}"
            except Exception:
                detail = exc.response.text or str(exc)
            return AIResponse(
                success=False,
                error=f"Keling image2video HTTP {exc.response.status_code}: {detail}",
                provider=provider_name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

        data = response.json()

        task_id = data.get("data", {}).get("task_id")
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
        result = await poll_video_task(client, base_url, task_id, get_auth_headers)

        if result and "video_url" in result:
            return AIResponse(
                success=True,
                data={"video_url": result["video_url"], "duration": dur_int},
                provider=provider_name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
                metadata={
                    "task_id": task_id,
                    "duration": dur_int,
                    "mode": mode_used,
                    "prompt": prompt,
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

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )


async def generate_video_from_multiple_images(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    image_list: List[str],
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    mode: str = "pro",
    duration: int = 5,
    aspect_ratio: Optional[str] = None,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """
    Generate video from multiple images (kling-v1-6 only).

    Endpoint: POST /v1/videos/multi-image2video

    Args:
        client: HTTP client
        base_url: API base URL
        provider_name: Provider name for response
        get_auth_headers: Function to get fresh auth headers
        image_list: List of 2-4 images (URLs or base64)
        prompt: Text description
        negative_prompt: Negative prompt
        mode: Generation mode ("std" or "pro")
        duration: Video duration (5 or 10 seconds)
        aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")

    Returns:
        AIResponse with generated video URL
    """
    if not image_list or len(image_list) < 2 or len(image_list) > 4:
        return AIResponse(
            success=False,
            error="image_list must contain 2-4 images",
            provider=provider_name,
            model="kling-v1-6",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    try:
        request_data = {
            "model_name": "kling-v1-6",  # Only supported by v1-6
            "image_list": image_list,
            "mode": "pro",
            "duration": duration,
        }

        if prompt:
            request_data["prompt"] = prompt
        if negative_prompt:
            request_data["negative_prompt"] = negative_prompt
        if aspect_ratio:
            request_data["aspect_ratio"] = aspect_ratio

        response = await client.post(
            f"{base_url}/v1/videos/multi-image2video",
            json=request_data,
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        data = response.json()

        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            return AIResponse(
                success=False,
                error="No task_id in response",
                provider=provider_name,
                model="kling-v1-6",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

        # Poll task status
        result = await poll_video_task(client, base_url, task_id, get_auth_headers)

        if result and "video_url" in result:
            return AIResponse(
                success=True,
                data={"video_url": result["video_url"], "duration": duration},
                provider=provider_name,
                model="kling-v1-6",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
                metadata={
                    "task_id": task_id,
                    "duration": duration,
                    "mode": "pro",
                    "image_count": len(image_list),
                },
            )
        else:
            return AIResponse(
                success=False,
                error="Multi-image video generation failed or timed out",
                provider=provider_name,
                model="kling-v1-6",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model="kling-v1-6",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )


async def get_task_status(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    task_id: str,
    task_type: str = "video",
    format_error: Callable = str,
) -> AIResponse:
    """
    Get task status for a given task ID.

    Args:
        client: HTTP client
        base_url: API base URL
        provider_name: Provider name for response
        get_auth_headers: Function to get fresh auth headers
        task_id: Task ID to query
        task_type: Type of task ("image" or "video")

    Returns:
        AIResponse with task status information
    """
    try:
        # Use appropriate endpoint based on task type
        if task_type == "image":
            endpoint = f"{base_url}/v1/images/generations/{task_id}"
        else:  # video
            endpoint = f"{base_url}/v1/videos/image2video/{task_id}"

        response = await client.get(endpoint, headers=get_auth_headers())
        response.raise_for_status()

        data = response.json().get("data", {})

        return AIResponse(
            success=True,
            data=data,
            provider=provider_name,
            model="task_status",
            task_type=(
                AITaskType.VIDEO_GENERATION
                if task_type == "video"
                else AITaskType.PORTRAIT_GENERATION
            ),
            model_type=(
                AIModelType.IMAGE_TO_VIDEO
                if task_type == "video"
                else AIModelType.TEXT_TO_IMAGE
            ),
            metadata={"task_id": task_id, "task_type": task_type},
        )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
        )
