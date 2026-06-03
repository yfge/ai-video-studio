"""Volcengine async video task helpers."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import httpx
from app.core.logging import get_logger
from app.services.providers.base import AIModelType, AIResponse, AITaskType

from .video_request import _normalize_model, build_video_request, has_visual_reference
from .video_response import (
    extract_error,
    extract_output_urls,
    extract_task_id,
    map_status,
)

logger = get_logger(__name__)


async def submit_video_task(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: Optional[str],
    image_url: Optional[str],
    model: Optional[str],
    duration: int,
    fps: int,
    resolution: str,
    end_image_url: Optional[str],
    ratio: Optional[str],
    watermark: Optional[bool],
    seed: Optional[int],
    camera_fixed: Optional[bool],
    service_tier: Optional[str],
    execution_expires_after: Optional[int],
    return_last_frame: Optional[bool],
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Submit a Volcengine video task and return the provider task ID."""
    try:
        ark_model, model_type, request_data, resolved = build_video_request(
            prompt=prompt,
            image_url=image_url,
            end_image_url=end_image_url,
            model=model,
            duration=duration,
            fps=fps,
            resolution=resolution,
            ratio=ratio,
            watermark=watermark,
            seed=seed,
            camera_fixed=camera_fixed,
            service_tier=service_tier,
            execution_expires_after=execution_expires_after,
            return_last_frame=return_last_frame,
            extra_kwargs=kwargs,
        )
        return await _submit_request(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            model=ark_model,
            model_type=model_type,
            request_data=request_data,
            resolved=resolved,
            format_error=format_error,
        )
    except Exception as exc:
        fallback_type = (
            AIModelType.IMAGE_TO_VIDEO
            if image_url or has_visual_reference(kwargs)
            else AIModelType.TEXT_TO_VIDEO
        )
        return _failure_response(
            format_error(exc),
            provider_name,
            model or _normalize_model(None),
            fallback_type,
        )


async def _submit_request(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    model: str,
    model_type: AIModelType,
    request_data: Dict[str, Any],
    resolved: Dict[str, Any],
    format_error: Callable,
) -> AIResponse:
    try:
        create_resp = await client.post(
            f"{base_url}/contents/generations/tasks",
            json=request_data,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json() if create_resp.content else {}

        error_message = extract_error(create_data)
        if error_message:
            return _failure_response(
                f"火山引擎视频生成错误: {error_message}",
                provider_name,
                model,
                model_type,
            )

        task_id = extract_task_id(create_data)
        if not task_id:
            return _failure_response(
                "火山引擎视频生成响应缺少任务ID",
                provider_name,
                model,
                model_type,
                metadata={"raw": create_data},
            )

        return AIResponse(
            success=True,
            data={"task_id": task_id, **resolved},
            provider=provider_name,
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type,
            metadata={"task_id": task_id},
        )
    except Exception as exc:
        return _failure_response(
            format_error(exc),
            provider_name,
            model,
            model_type,
        )


async def fetch_video_task_status(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    task_id: str,
    format_error: Callable = str,
) -> AIResponse:
    """Fetch async video task status from Volcengine."""
    try:
        response = await client.get(f"{base_url}/contents/generations/tasks/{task_id}")
        logger.info(
            "Video task status http response: "
            "provider=%s task_id=%s status=%s body=%s",
            provider_name,
            task_id,
            response.status_code,
            response.text,
        )
        response.raise_for_status()

        data = response.json() if response.content else {}
        if not isinstance(data, dict):
            data = {}
        urls = extract_output_urls(data)
        return AIResponse(
            success=True,
            data={
                "status": map_status(str(data.get("status") or "")).value,
                **urls,
                "raw": data,
            },
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
            metadata={"task_id": task_id},
        )
    except Exception as exc:
        return _failure_response(
            format_error(exc),
            provider_name,
            "task_status",
            AIModelType.TEXT_TO_VIDEO,
        )


def _failure_response(
    message: str,
    provider_name: str,
    model: str,
    model_type: AIModelType,
    metadata: Optional[Dict[str, Any]] = None,
) -> AIResponse:
    return AIResponse(
        success=False,
        error=message,
        provider=provider_name,
        model=model,
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=model_type,
        metadata=metadata or {},
    )
