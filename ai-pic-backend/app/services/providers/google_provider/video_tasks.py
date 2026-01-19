"""
Google Veo async video task module.

This module implements a two-phase workflow:
1) Submit a long-running operation and return its operation name as `task_id`
2) Poll the operation by `task_id` to retrieve final video URLs
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from ..polling_utils import TaskStatus, google_operation_status_mapper
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


async def submit_video_task(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    config_timeout: Any,
    prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    end_image_url: Optional[str] = None,
    model: Optional[str] = None,
    duration: Optional[int] = None,
    resolution: Optional[str] = None,
    ratio: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    reference_images: Optional[List[Any]] = None,
    person_generation: Optional[str] = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Submit a Veo video generation task and return a `task_id`."""
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
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model_id}:predictLongRunning"

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
            ratio
            or kwargs.get("aspectRatio")
            or kwargs.get("aspect_ratio")
            or kwargs.get("ratio")
        )
        if resolved_ratio:
            parameters["aspectRatio"] = resolved_ratio

        resolved_resolution = normalize_resolution(resolution or kwargs.get("resolution"))
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
                    refs.append({"image": image_payload, "referenceType": "asset"})
                elif isinstance(item, dict):
                    image_value = item.get("image") or item.get("image_url") or item.get("url")
                    if not image_value:
                        continue
                    image_payload = await fetch_image_bytes(image_value, config_timeout)
                    reference_type = item.get("reference_type") or item.get("referenceType") or "asset"
                    refs.append({"image": image_payload, "referenceType": reference_type})
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
                    AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"raw": create_payload},
            )

        return AIResponse(
            success=True,
            data={
                "task_id": operation_name,
                "duration": resolved_duration,
                "resolution": resolved_resolution,
                "aspect_ratio": resolved_ratio,
            },
            provider=provider_name,
            model=model_id,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=(
                AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
            ),
            metadata={"task_id": operation_name},
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
                AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
            ),
        )


async def fetch_video_task_status(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    task_id: str,
    format_error: Callable = str,
) -> AIResponse:
    """Fetch Veo long-running operation status by `task_id`."""
    if not api_key:
        return AIResponse(
            success=False,
            error="GoogleProvider 未配置 API Key",
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )

    if client is None:
        return AIResponse(
            success=False,
            error="Google 客户端未初始化",
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )

    op_path = normalize_operation_path(task_id)
    try:
        resp = await client.get(f"{base_url.rstrip('/')}/v1beta/{op_path}")
        resp.raise_for_status()
        payload = resp.json()

        status = google_operation_status_mapper(payload)
        video_url = None
        download_url = None
        error_message = None

        if status in (TaskStatus.SUCCESS, TaskStatus.COMPLETED):
            video_url = extract_video_uri(payload)
            if video_url:
                download_url = append_api_key(video_url, api_key)
        elif status == TaskStatus.FAILED:
            raw_error = payload.get("error")
            if isinstance(raw_error, dict):
                error_message = raw_error.get("message") or raw_error.get("status")
            elif raw_error:
                error_message = str(raw_error)

        return AIResponse(
            success=True,
            data={
                "status": status.value,
                "video_url": video_url,
                "download_url": download_url,
                "error": error_message,
                "raw": payload,
            },
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )
    except Exception as exc:
        if isinstance(exc, httpx.HTTPStatusError):
            formatted = format_http_status_error(exc, label="Google Veo")
            exc = RuntimeError(formatted)
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )
