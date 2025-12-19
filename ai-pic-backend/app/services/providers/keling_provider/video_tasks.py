from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

import httpx

from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.providers.polling_utils import TaskStatus, keling_status_mapper


def _coerce_duration(value: Any) -> int:
    try:
        dur = int(value)
    except (TypeError, ValueError):
        return 5
    if dur <= 0:
        return 5
    return dur


def _resolve_images(
    image: Optional[str],
    image_url: Optional[str],
    image_tail: Optional[str],
    end_image_url: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    primary_image = image or image_url
    tail_image = image_tail or end_image_url
    return primary_image, tail_image


def _normalize_mode(mode: str) -> str:
    mode_used = str(mode or "").strip().lower()
    return "pro" if mode_used != "pro" else mode_used


def _normalize_duration(duration: int) -> int:
    dur_int = _coerce_duration(duration)
    allowed_durations = [5, 10]
    if dur_int not in allowed_durations:
        dur_int = min(allowed_durations, key=lambda d: abs(d - dur_int))
    return dur_int


def _apply_optional_fields(
    request_data: Dict[str, Any],
    *,
    tail_image: Optional[str],
    prompt: Optional[str],
    negative_prompt: Optional[str],
    cfg_scale: Optional[float],
    camera_control: Optional[Dict[str, Any]],
    model: str,
) -> None:
    if tail_image:
        request_data["image_tail"] = tail_image
    if prompt:
        request_data["prompt"] = prompt
    if negative_prompt:
        request_data["negative_prompt"] = negative_prompt
    if cfg_scale is not None and not model.startswith("kling-v2"):
        request_data["cfg_scale"] = cfg_scale
    if camera_control:
        request_data["camera_control"] = camera_control


def _apply_resolution_ratio(
    request_data: Dict[str, Any],
    *,
    resolution: Optional[str],
    ratio: Optional[str],
    kwargs: Dict[str, Any],
) -> None:
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


def _apply_extra_fields(request_data: Dict[str, Any], kwargs: Dict[str, Any]) -> None:
    for key in ["dynamic_masks", "static_mask", "voice_list", "sound"]:
        if key in kwargs:
            request_data[key] = kwargs[key]


def _build_request_data(
    *,
    model: str,
    primary_image: str,
    tail_image: Optional[str],
    prompt: Optional[str],
    negative_prompt: Optional[str],
    cfg_scale: Optional[float],
    camera_control: Optional[Dict[str, Any]],
    mode: str,
    duration: int,
    resolution: Optional[str],
    ratio: Optional[str],
    kwargs: Dict[str, Any],
) -> Tuple[Dict[str, Any], int, str]:
    dur_int = _normalize_duration(duration)
    mode_used = _normalize_mode(mode)
    request_data = {
        "model_name": model,
        "image": primary_image,
        "mode": mode_used,
        "duration": dur_int,
    }
    _apply_optional_fields(
        request_data,
        tail_image=tail_image,
        prompt=prompt,
        negative_prompt=negative_prompt,
        cfg_scale=cfg_scale,
        camera_control=camera_control,
        model=model,
    )
    _apply_resolution_ratio(
        request_data,
        resolution=resolution,
        ratio=ratio,
        kwargs=kwargs,
    )
    _apply_extra_fields(request_data, kwargs)
    return request_data, dur_int, mode_used


def _build_error_response(
    message: str, provider_name: str, model: str
) -> AIResponse:
    return AIResponse(
        success=False,
        error=message,
        provider=provider_name,
        model=model,
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=AIModelType.IMAGE_TO_VIDEO,
    )


def _require_primary_image(
    primary_image: Optional[str],
    provider_name: str,
    model: str,
) -> Optional[AIResponse]:
    if primary_image:
        return None
    return _build_error_response(
        "image parameter is required for video generation",
        provider_name,
        model,
    )


def _extract_task_id(data: Dict[str, Any]) -> Optional[str]:
    return data.get("data", {}).get("task_id")


def _format_http_error(exc: httpx.HTTPStatusError) -> str:
    detail = ""
    try:
        payload = exc.response.json()
        code = payload.get("code")
        msg = payload.get("message") or payload.get("msg")
        detail = f"code={code}, message={msg}"
    except Exception:
        detail = exc.response.text or str(exc)
    return f"Keling image2video HTTP {exc.response.status_code}: {detail}"


async def submit_video_task(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    prompt: Optional[str],
    image: Optional[str],
    image_url: Optional[str],
    image_tail: Optional[str],
    end_image_url: Optional[str],
    model: str,
    mode: str,
    duration: int,
    resolution: Optional[str],
    ratio: Optional[str],
    negative_prompt: Optional[str],
    cfg_scale: Optional[float],
    camera_control: Optional[Dict[str, Any]],
    format_error: Callable = str,
    **kwargs: Any,
) -> AIResponse:
    primary_image, tail_image = _resolve_images(
        image, image_url, image_tail, end_image_url
    )
    error_response = _require_primary_image(primary_image, provider_name, model)
    if error_response:
        return error_response
    return await _submit_with_payload(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        get_auth_headers=get_auth_headers,
        model=model,
        mode=mode,
        duration=duration,
        resolution=resolution,
        ratio=ratio,
        prompt=prompt,
        negative_prompt=negative_prompt,
        cfg_scale=cfg_scale,
        camera_control=camera_control,
        primary_image=primary_image,
        tail_image=tail_image,
        format_error=format_error,
        extra_kwargs=kwargs,
    )


async def _submit_with_payload(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    model: str,
    mode: str,
    duration: int,
    resolution: Optional[str],
    ratio: Optional[str],
    prompt: Optional[str],
    negative_prompt: Optional[str],
    cfg_scale: Optional[float],
    camera_control: Optional[Dict[str, Any]],
    primary_image: str,
    tail_image: Optional[str],
    format_error: Callable,
    extra_kwargs: Dict[str, Any],
) -> AIResponse:
    request_data, dur_int, mode_used = _build_request_data(
        model=model,
        primary_image=primary_image,
        tail_image=tail_image,
        prompt=prompt,
        negative_prompt=negative_prompt,
        cfg_scale=cfg_scale,
        camera_control=camera_control,
        mode=mode,
        duration=duration,
        resolution=resolution,
        ratio=ratio,
        kwargs=extra_kwargs,
    )
    return await _submit_request(
        client=client,
        base_url=base_url,
        provider_name=provider_name,
        get_auth_headers=get_auth_headers,
        request_data=request_data,
        model=model,
        duration=dur_int,
        mode_used=mode_used,
        format_error=format_error,
    )


async def _submit_request(
    *,
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    request_data: Dict[str, Any],
    model: str,
    duration: int,
    mode_used: str,
    format_error: Callable,
) -> AIResponse:
    try:
        response = await client.post(
            f"{base_url}/v1/videos/image2video",
            json=request_data,
            headers=get_auth_headers(),
        )
        response.raise_for_status()

        data = response.json()
        task_id = _extract_task_id(data)
        if not task_id:
            return _build_error_response("No task_id in response", provider_name, model)

        return AIResponse(
            success=True,
            data={"task_id": task_id, "duration": duration},
            provider=provider_name,
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id, "mode": mode_used},
        )

    except httpx.HTTPStatusError as exc:
        return _build_error_response(_format_http_error(exc), provider_name, model)
    except Exception as exc:
        return _build_error_response(format_error(exc), provider_name, model)


async def fetch_video_task_status(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    get_auth_headers: Callable[[], Dict[str, str]],
    task_id: str,
    format_error: Callable = str,
) -> AIResponse:
    try:
        response = await client.get(
            f"{base_url}/v1/videos/image2video/{task_id}",
            headers=get_auth_headers(),
        )
        response.raise_for_status()

        data = response.json().get("data", {})
        status = keling_status_mapper(data)

        video_url = None
        if status in (TaskStatus.SUCCESS, TaskStatus.COMPLETED):
            videos = (data.get("task_result") or {}).get("videos") or []
            if videos:
                video_url = videos[0].get("url")

        return AIResponse(
            success=True,
            data={
                "status": status.value,
                "video_url": video_url,
                "raw": data,
            },
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={"task_id": task_id},
        )

    except Exception as exc:
        return AIResponse(
            success=False,
            error=format_error(exc),
            provider=provider_name,
            model="task_status",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )
