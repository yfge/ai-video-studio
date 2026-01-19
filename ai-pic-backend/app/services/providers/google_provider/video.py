"""
Google Veo video generation module.

Implements text-to-video and image-to-video using Gemini Veo models.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from ..polling_utils import TaskPoller, google_operation_status_mapper
from .helpers import clean_model_id, fetch_image_bytes
from .video_helpers import (
    append_api_key,
    extract_video_uri,
    format_http_status_error,
    normalize_operation_path,
    normalize_ratio,
    normalize_resolution,
    resolve_duration,
    supports_reference_images,
)


async def _poll_operation(
    client: httpx.AsyncClient,
    base_url: str,
    operation_name: str,
) -> Optional[Dict[str, Any]]:
    op_path = normalize_operation_path(operation_name)

    async def poll_fn() -> Dict[str, Any]:
        resp = await client.get(f"{base_url.rstrip('/')}/v1beta/{op_path}")
        resp.raise_for_status()
        return resp.json()

    poller = TaskPoller(
        poll_fn=poll_fn,
        status_mapper=google_operation_status_mapper,
        result_extractor=lambda data: data,
        max_attempts=180,
        initial_delay=10.0,
        task_id=operation_name,
        task_type="video",
    )
    return await poller.poll()


async def generate_video(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    config_timeout: Any,
    prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    model: Optional[str] = None,
    duration: Optional[int] = None,
    resolution: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    end_image_url: Optional[str] = None,
    reference_images: Optional[List[Any]] = None,
    person_generation: Optional[str] = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate video using Google Veo models."""
    default_model = "veo-3.1-generate-preview"

    if not api_key:
        return AIResponse(
            success=False,
            error="GoogleProvider 未配置 API Key",
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
        )

    if client is None:
        return AIResponse(
            success=False,
            error="Google 客户端未初始化",
            provider=provider_name,
            model=model or default_model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
        )

    model_id = clean_model_id(model) or default_model
    endpoint = (
        f"{base_url.rstrip('/')}/v1beta/models/{model_id}:predictLongRunning"
    )

    if not prompt and not image_url:
        return AIResponse(
            success=False,
            error="缺少视频生成提示词或首帧图像",
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
        )

    try:
        instance: Dict[str, Any] = {}
        if prompt:
            instance["prompt"] = prompt
        if image_url:
            instance["image"] = await fetch_image_bytes(image_url, config_timeout)
        if end_image_url:
            instance["lastFrame"] = await fetch_image_bytes(
                end_image_url, config_timeout
            )

        body: Dict[str, Any] = {"instances": [instance]}
        parameters: Dict[str, Any] = {}

        resolved_ratio = normalize_ratio(
            aspect_ratio
            or kwargs.get("aspectRatio")
            # Our internal API uses `ratio` for video aspect ratio; keep backward-compatible
            # with provider-specific `aspectRatio`.
            or kwargs.get("ratio")
        )
        if resolved_ratio:
            parameters["aspectRatio"] = resolved_ratio

        resolved_resolution = normalize_resolution(
            resolution or kwargs.get("resolution")
        )
        if resolved_resolution:
            parameters["resolution"] = resolved_resolution

        resolved_duration = resolve_duration(
            model_id,
            duration or kwargs.get("durationSeconds"),
            resolution=resolved_resolution,
        )
        if resolved_duration:
            parameters["durationSeconds"] = resolved_duration

        resolved_negative = negative_prompt or kwargs.get("negativePrompt")
        if resolved_negative:
            parameters["negativePrompt"] = resolved_negative

        if person_generation:
            parameters["personGeneration"] = person_generation

        if reference_images and supports_reference_images(model_id):
            refs: List[Dict[str, Any]] = []
            for item in reference_images[:3]:
                if isinstance(item, str):
                    image_payload = await fetch_image_bytes(item, config_timeout)
                    refs.append(
                        {"image": image_payload, "referenceType": "asset"}
                    )
                elif isinstance(item, dict):
                    image_value = (
                        item.get("image")
                        or item.get("image_url")
                        or item.get("url")
                    )
                    if not image_value:
                        continue
                    image_payload = await fetch_image_bytes(image_value, config_timeout)
                    reference_type = (
                        item.get("reference_type")
                        or item.get("referenceType")
                        or "asset"
                    )
                    refs.append(
                        {
                            "image": image_payload,
                            "referenceType": reference_type,
                        }
                    )
            if refs:
                parameters["referenceImages"] = refs

        if parameters:
            body["parameters"] = parameters

        resp = await client.post(endpoint, json=body)
        resp.raise_for_status()
        create_payload = resp.json()
        operation_name = create_payload.get("name")
        if not operation_name:
            return AIResponse(
                success=False,
                error="Google Veo 响应缺少 operation name",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"raw": create_payload},
            )

        operation = await _poll_operation(client, base_url, operation_name)
        if not operation:
            return AIResponse(
                success=False,
                error="Google Veo 生成任务失败或超时",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"operation_name": operation_name},
            )

        video_uri = extract_video_uri(operation)
        if not video_uri:
            return AIResponse(
                success=False,
                error="Google Veo 响应未返回视频地址",
                provider=provider_name,
                model=model_id,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"operation_name": operation_name},
            )

        download_url = append_api_key(video_uri, api_key)
        return AIResponse(
            success=True,
            data={
                "video_url": video_uri,
                "download_url": download_url,
                "duration": resolved_duration,
                "resolution": resolved_resolution,
                "aspect_ratio": resolved_ratio,
            },
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=(
                AIModelType.IMAGE_TO_VIDEO
                if image_url
                else AIModelType.TEXT_TO_VIDEO
            ),
            metadata={"operation_name": operation_name},
        )
    except Exception as exc:
        if isinstance(exc, httpx.HTTPStatusError):
            formatted = format_http_status_error(exc, label="Google Veo")
            exc = RuntimeError(formatted)
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=(
                AIModelType.IMAGE_TO_VIDEO
                if image_url
                else AIModelType.TEXT_TO_VIDEO
            ),
        )
