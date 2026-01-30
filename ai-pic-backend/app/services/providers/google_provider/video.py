"""
Google Veo video generation module.

Implements text-to-video and image-to-video using Gemini Veo models.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from .helpers import clean_model_id
from .video_helpers import append_api_key, extract_video_uri, format_http_status_error
from .video_request import build_veo_request_body
from .video_vertex import (
    build_vertex_headers,
    build_vertex_predict_long_running_url,
    extract_video_bytes_base64,
    extract_video_mime_type,
    poll_veo_operation,
)


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
    vertex_project_id: Optional[str] = None,
    vertex_location: Optional[str] = None,
    access_token: Optional[str] = None,
    vertex_api_key: Optional[str] = None,
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
        build_kwargs = dict(kwargs)
        raw_ratio = aspect_ratio or build_kwargs.get("ratio")
        build_kwargs.pop("ratio", None)
        body, resolved = await build_veo_request_body(
            prompt=prompt,
            image_url=image_url,
            end_image_url=end_image_url,
            config_timeout=config_timeout,
            model_id=model_id,
            duration=duration,
            resolution=resolution,
            ratio=raw_ratio,
            negative_prompt=negative_prompt,
            reference_images=reference_images,
            person_generation=person_generation,
            **build_kwargs,
        )
        resolved_ratio = resolved.get("aspect_ratio")
        resolved_resolution = resolved.get("resolution")
        resolved_duration = resolved.get("duration")

        headers = (
            build_vertex_headers(access_token, vertex_api_key) if use_vertex else None
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
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"raw": create_payload},
            )

        operation = await poll_veo_operation(
            client=client,
            base_url=base_url,
            operation_name=operation_name,
            access_token=access_token,
            api_key=vertex_api_key,
        )
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
        video_bytes = extract_video_bytes_base64(operation)
        video_mime_type = extract_video_mime_type(operation)
        if not (video_uri or video_bytes):
            return AIResponse(
                success=False,
                error="Google Veo 响应未返回视频内容",
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

        download_url = append_api_key(video_uri, api_key) if video_uri else None
        return AIResponse(
            success=True,
            data={
                "video_url": video_uri,
                "download_url": download_url,
                "video_bytes_base64": video_bytes,
                "video_mime_type": video_mime_type,
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
                AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
            ),
        )
