"""Volcengine video generation module."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType
from .video_request import (
    _build_prompt_with_flags,
    _normalize_model,
    build_video_request,
)
from .video_response import extract_error, extract_output_urls, extract_task_id

logger = logging.getLogger(__name__)

__all__ = [
    "_build_prompt_with_flags",
    "_normalize_model",
    "generate_video",
    "poll_task_status",
]


async def poll_task_status(
    client: httpx.AsyncClient,
    base_url: str,
    task_id: str,
    max_attempts: int = 60,
    delay: int = 3,
) -> Dict[str, Any]:
    """Poll Volcengine content generation task status."""
    last_error: str | None = None

    for attempt in range(max_attempts):
        try:
            response = await client.get(
                f"{base_url}/contents/generations/tasks/{task_id}",
            )
            response.raise_for_status()
            data = response.json() if response.content else {}
            if not isinstance(data, dict):
                raise RuntimeError(
                    f"火山引擎任务 {task_id} 返回非 dict 响应: {type(data).__name__}"
                )

            status = str(data.get("status") or "").lower()
            if status == "succeeded":
                return data
            if status in {"failed", "canceled", "cancelled", "expired"}:
                err_msg = extract_error(data) or f"任务状态: {status}"
                raise RuntimeError(f"火山引擎任务失败: {err_msg}")
            if status in {"queued", "running", "processing", "pending"}:
                await asyncio.sleep(delay)
                continue

            logger.warning("火山引擎任务 %s 未知状态: %s", task_id, status)
            raise RuntimeError(f"火山引擎任务未知状态: {status}")
        except RuntimeError:
            raise
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "轮询火山引擎任务状态失败 (尝试 %d/%d): %s",
                attempt + 1,
                max_attempts,
                exc,
            )
            await asyncio.sleep(delay)

    suffix = f", 最后错误: {last_error}" if last_error else ""
    raise RuntimeError(
        f"火山引擎任务 {task_id} 轮询超时 ({max_attempts * delay}s){suffix}"
    )


async def generate_video(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    model: Optional[str] = None,
    duration: int = 5,
    fps: int = 24,
    resolution: str = "720p",
    end_image_url: Optional[str] = None,
    ratio: Optional[str] = None,
    watermark: Optional[bool] = None,
    seed: Optional[int] = None,
    camera_fixed: Optional[bool] = None,
    service_tier: Optional[str] = None,
    execution_expires_after: Optional[int] = None,
    return_last_frame: Optional[bool] = None,
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    """Generate video using Volcengine Ark Video Generation API."""
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
                ark_model,
                model_type,
            )

        task_id = extract_task_id(create_data)
        if not task_id:
            return _failure_response(
                "火山引擎视频生成响应缺少任务ID",
                provider_name,
                ark_model,
                model_type,
                metadata={"raw": create_data},
            )

        result = await poll_task_status(
            client,
            base_url,
            task_id,
            max_attempts=(600 if model_type == AIModelType.IMAGE_TO_VIDEO else 120),
            delay=3,
        )
        urls = extract_output_urls(result)
        if not urls.get("video_url"):
            return _failure_response(
                "火山引擎视频生成成功但未返回视频URL",
                provider_name,
                ark_model,
                model_type,
                metadata={"task_id": task_id, "raw": result},
            )

        return AIResponse(
            success=True,
            data={**urls, "duration": resolved["duration"]},
            provider=provider_name,
            model=ark_model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type,
            metadata={
                "task_id": task_id,
                "prompt": request_data["content"][0]["text"],
                "watermark": watermark,
                "seed": seed,
                "service_tier": service_tier,
                **resolved,
            },
        )
    except Exception as exc:
        return _failure_response(
            format_error(exc),
            provider_name,
            model or _normalize_model(None),
            (AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO),
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
