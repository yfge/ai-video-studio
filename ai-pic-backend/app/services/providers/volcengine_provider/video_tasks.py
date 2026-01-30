from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import httpx
from app.core.logging import get_logger
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.providers.polling_utils import TaskStatus

from .video import _build_prompt_with_flags, _normalize_model

logger = get_logger(__name__)


def _map_status(value: str) -> TaskStatus:
    status = (value or "").lower()
    if status == "succeeded":
        return TaskStatus.SUCCESS
    if status in {"failed", "canceled", "cancelled"}:
        return TaskStatus.FAILED
    if status in {"queued", "running", "processing", "pending"}:
        return TaskStatus.PROCESSING
    return TaskStatus.PENDING


def _build_content(
    final_prompt: str,
    image_url: Optional[str],
    end_image_url: Optional[str],
) -> list[Dict[str, Any]]:
    content: list[Dict[str, Any]] = [{"type": "text", "text": final_prompt}]
    if image_url:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_url},
                "role": "first_frame",
            }
        )
    if end_image_url:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": end_image_url},
                "role": "last_frame",
            }
        )
    return content


def _build_request_data(
    ark_model: str,
    content: list[Dict[str, Any]],
    service_tier: Optional[str],
    execution_expires_after: Optional[int],
    return_last_frame: Optional[bool],
    kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    request_data: Dict[str, Any] = {"model": ark_model, "content": content}
    if service_tier:
        request_data["service_tier"] = service_tier
    if execution_expires_after is not None:
        request_data["execution_expires_after"] = int(execution_expires_after)
    if return_last_frame is not None:
        request_data["return_last_frame"] = bool(return_last_frame)

    for key, value in (kwargs or {}).items():
        if key in request_data:
            continue
        request_data[key] = value
    return request_data


def _extract_task_id(data: Dict[str, Any]) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    task_id = data.get("id") or data.get("task_id")
    if task_id:
        return task_id
    nested = data.get("data")
    if isinstance(nested, dict):
        return nested.get("id") or nested.get("task_id")
    return None


def _extract_error(data: Dict[str, Any]) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    err = data.get("error") or {}
    if not isinstance(err, dict):
        return None
    message = err.get("message") or err.get("code")
    return f"火山引擎视频生成错误: {message or 'Unknown error'}" if message else None


def _build_failure_response(
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
        metadata=metadata,
    )


def _build_success_response(
    *,
    provider_name: str,
    model: str,
    model_type: AIModelType,
    task_id: str,
    duration: int,
    fps: int,
    resolution: str,
    ratio: Optional[str],
) -> AIResponse:
    return AIResponse(
        success=True,
        data={
            "task_id": task_id,
            "duration": duration,
            "fps": fps,
            "resolution": resolution,
            "ratio": ratio,
        },
        provider=provider_name,
        model=model,
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=model_type,
        metadata={"task_id": task_id},
    )


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
    model_type = AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
    return await _prepare_and_submit_safe(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        prompt=prompt,
        image_url=image_url,
        model=model,
        duration=duration,
        fps=fps,
        resolution=resolution,
        end_image_url=end_image_url,
        ratio=ratio,
        watermark=watermark,
        seed=seed,
        camera_fixed=camera_fixed,
        service_tier=service_tier,
        execution_expires_after=execution_expires_after,
        return_last_frame=return_last_frame,
        format_error=format_error,
        model_type=model_type,
        extra_kwargs=kwargs,
    )


async def _prepare_and_submit_safe(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    format_error: Callable,
    model_type: AIModelType,
    extra_kwargs: Dict[str, Any],
    **options: Any,
) -> AIResponse:
    try:
        return await _prepare_and_submit(
            client=client,
            base_url=base_url,
            provider_name=provider_name,
            format_error=format_error,
            model_type=model_type,
            extra_kwargs=extra_kwargs,
            **options,
        )

    except Exception as exc:
        return _build_failure_response(
            format_error(exc),
            provider_name,
            (options.get("model") or "doubao-seedance-1-0-pro-250528"),
            model_type,
        )


async def _prepare_and_submit(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    format_error: Callable,
    model_type: AIModelType,
    extra_kwargs: Dict[str, Any],
    **options: Any,
) -> AIResponse:
    image_url = options.get("image_url")
    ark_model = _normalize_model(options.get("model"), image_url is not None)
    final_prompt, dur, fps_int, rs, rt = _build_prompt_with_flags(
        options.get("prompt"),
        options.get("resolution"),
        options.get("ratio"),
        options.get("duration"),
        options.get("fps"),
        options.get("watermark"),
        options.get("seed"),
        options.get("camera_fixed"),
    )
    content = _build_content(final_prompt, image_url, options.get("end_image_url"))
    request_data = _build_request_data(
        ark_model,
        content,
        options.get("service_tier"),
        options.get("execution_expires_after"),
        options.get("return_last_frame"),
        extra_kwargs,
    )
    return await _submit_request(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        model=ark_model,
        model_type=model_type,
        request_data=request_data,
        duration=dur,
        fps=fps_int,
        resolution=rs or options.get("resolution"),
        ratio=rt,
        format_error=format_error,
    )


async def _submit_request(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    model: str,
    model_type: AIModelType,
    request_data: Dict[str, Any],
    duration: int,
    fps: int,
    resolution: str,
    ratio: Optional[str],
    format_error: Callable,
) -> AIResponse:
    try:
        create_resp = await client.post(
            f"{base_url}/contents/generations/tasks",
            json=request_data,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json() if create_resp.content else {}

        error_message = _extract_error(create_data)
        if error_message:
            return _build_failure_response(
                error_message,
                provider_name,
                model,
                model_type,
            )

        task_id = _extract_task_id(create_data)
        if not task_id:
            return _build_failure_response(
                "火山引擎视频生成响应缺少任务ID",
                provider_name,
                model,
                model_type,
                metadata={"raw": create_data},
            )

        return _build_success_response(
            provider_name=provider_name,
            model=model,
            model_type=model_type,
            task_id=task_id,
            duration=duration,
            fps=fps,
            resolution=resolution,
            ratio=ratio,
        )

    except Exception as exc:
        return _build_failure_response(
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
    try:
        response = await client.get(f"{base_url}/contents/generations/tasks/{task_id}")
        logger.info(
            "Video task status http response: provider=%s task_id=%s status=%s body=%s",
            provider_name,
            task_id,
            response.status_code,
            response.text,
        )
        response.raise_for_status()

        data = response.json() if response.content else {}
        if not isinstance(data, dict):
            data = {}

        status = _map_status(str(data.get("status") or ""))
        content_out = data.get("content") or {}
        video_url = (
            content_out.get("video_url")
            or content_out.get("videoUrl")
            or content_out.get("url")
            or data.get("video_url")
            or data.get("videoUrl")
            or data.get("url")
        )
        thumbnail_url = (
            content_out.get("thumbnail_url")
            or content_out.get("cover_image_url")
            or content_out.get("cover_url")
            or content_out.get("poster_url")
        )
        last_frame_url = content_out.get("last_frame_url") or content_out.get(
            "lastFrameUrl"
        )

        return AIResponse(
            success=True,
            data={
                "status": status.value,
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "last_frame_url": last_frame_url,
                "raw": data,
            },
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
            metadata={"task_id": task_id},
        )

    except Exception as exc:
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO,
        )
