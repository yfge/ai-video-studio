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
from .helpers import clean_model_id
from .video_request import build_veo_request_body
from .video_helpers import (
    append_api_key,
    extract_video_uri,
    format_http_status_error,
    normalize_operation_path,
)
from .video_vertex import (
    build_vertex_fetch_predict_operation_url,
    build_vertex_predict_long_running_url,
    extract_video_bytes_base64,
    extract_video_mime_type,
    parse_vertex_operation_name,
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
    vertex_project_id: Optional[str] = None,
    vertex_location: Optional[str] = None,
    access_token: Optional[str] = None,
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
    use_vertex = bool(vertex_project_id and vertex_location)
    endpoint = (
        build_vertex_predict_long_running_url(
            base_url,
            project_id=vertex_project_id or "",
            location=vertex_location or "",
            model_id=model_id,
        )
        if use_vertex
        else f"{base_url.rstrip('/')}/v1beta/models/{model_id}:predictLongRunning"
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
        body, resolved = await build_veo_request_body(
            prompt=prompt,
            image_url=image_url,
            end_image_url=end_image_url,
            config_timeout=config_timeout,
            model_id=model_id,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            negative_prompt=negative_prompt,
            reference_images=reference_images,
            person_generation=person_generation,
            **kwargs,
        )
        resolved_ratio = resolved.get("aspect_ratio")
        resolved_resolution = resolved.get("resolution")
        resolved_duration = resolved.get("duration")

        headers = (
            {"Authorization": f"Bearer {access_token}"}
            if use_vertex and access_token
            else None
        )
        resp = await client.post(endpoint, json=body, headers=headers)
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
    access_token: Optional[str] = None,
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

    try:
        vertex = parse_vertex_operation_name(task_id)
        if vertex:
            endpoint = build_vertex_fetch_predict_operation_url(
                base_url,
                project_id=vertex["project_id"],
                location=vertex["location"],
                model_id=vertex["model_id"],
            )
            headers = {"Authorization": f"Bearer {access_token}"} if access_token else None
            resp = await client.post(
                endpoint,
                json={"operationName": task_id},
                headers=headers,
            )
        else:
            op_path = normalize_operation_path(task_id)
            resp = await client.get(f"{base_url.rstrip('/')}/v1beta/{op_path}")
        resp.raise_for_status()
        payload = resp.json()

        status = google_operation_status_mapper(payload)
        video_url = None
        download_url = None
        video_bytes = None
        video_mime_type = None
        error_message = None

        if status in (TaskStatus.SUCCESS, TaskStatus.COMPLETED):
            video_url = extract_video_uri(payload)
            video_bytes = extract_video_bytes_base64(payload)
            video_mime_type = extract_video_mime_type(payload)
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
                "video_bytes_base64": video_bytes,
                "video_mime_type": video_mime_type,
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
