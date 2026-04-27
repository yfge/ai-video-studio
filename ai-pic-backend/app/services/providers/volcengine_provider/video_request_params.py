"""Volcengine video request parameter normalization."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .video_models import (
    SEEDANCE_10_LITE_I2V_MODEL,
    SEEDANCE_15_PRO_MODEL,
    SEEDANCE_20_FAST_MODEL,
    SEEDANCE_20_MODEL,
)

SEEDANCE20_MODELS = {SEEDANCE_20_MODEL, SEEDANCE_20_FAST_MODEL}
SEEDANCE15_MODELS = {SEEDANCE_15_PRO_MODEL}
REQUEST_PASSTHROUGH_KEYS = {
    "callback_url",
    "draft",
    "safety_identifier",
    "tools",
}


def apply_generation_params(
    request_data: Dict[str, Any],
    *,
    ark_model: str,
    duration: int,
    fps: int,
    resolution: str,
    ratio: Optional[str],
    watermark: Optional[bool],
    seed: Optional[int],
    camera_fixed: Optional[bool],
) -> Dict[str, Any]:
    resolved_resolution = normalize_resolution(resolution) or "720p"
    if ark_model == SEEDANCE_20_FAST_MODEL and resolved_resolution == "1080p":
        resolved_resolution = "720p"
    resolved_ratio = (ratio or "").strip() or None
    resolved_duration = coerce_duration(ark_model, duration)
    request_data.update(
        {"resolution": resolved_resolution, "duration": resolved_duration}
    )
    if resolved_ratio:
        request_data["ratio"] = resolved_ratio
    if watermark is not None:
        request_data["watermark"] = bool(watermark)
    if seed is not None:
        request_data["seed"] = int(seed)
    if camera_fixed is not None and ark_model not in SEEDANCE20_MODELS:
        request_data["camera_fixed"] = bool(camera_fixed)
    return {
        "duration": resolved_duration,
        "fps": coerce_fps(fps),
        "resolution": resolved_resolution,
        "ratio": resolved_ratio,
    }


def apply_task_params(
    request_data: Dict[str, Any],
    *,
    ark_model: str,
    service_tier: Optional[str],
    execution_expires_after: Optional[int],
    return_last_frame: Optional[bool],
    extra_kwargs: Dict[str, Any],
) -> None:
    if service_tier and (
        ark_model not in SEEDANCE20_MODELS or service_tier == "default"
    ):
        request_data["service_tier"] = service_tier
    if execution_expires_after is not None:
        request_data["execution_expires_after"] = int(execution_expires_after)
    if return_last_frame is not None:
        request_data["return_last_frame"] = bool(return_last_frame)
    if ark_model in SEEDANCE20_MODELS | SEEDANCE15_MODELS:
        generate_audio = extra_kwargs.get("generate_audio")
        if generate_audio is not None:
            request_data["generate_audio"] = bool(generate_audio)
    for key in REQUEST_PASSTHROUGH_KEYS:
        if key in extra_kwargs and extra_kwargs[key] is not None:
            request_data[key] = extra_kwargs[key]


def normalize_resolution(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lowered = str(value).strip().lower()
    if lowered in {"480p", "720p", "1080p"}:
        return lowered
    if "1080" in lowered or "1088" in lowered:
        return "1080p"
    if "720" in lowered:
        return "720p"
    if "480" in lowered:
        return "480p"
    return None


def coerce_duration(ark_model: str, value: Any) -> int:
    try:
        duration = int(value)
    except (TypeError, ValueError):
        duration = 5
    if duration == -1 and ark_model in SEEDANCE20_MODELS | SEEDANCE15_MODELS:
        return -1
    min_duration, max_duration = (4, 15) if ark_model in SEEDANCE20_MODELS else (2, 12)
    if ark_model in SEEDANCE15_MODELS:
        min_duration = 4
    return max(min_duration, min(duration, max_duration))


def coerce_fps(value: Any) -> int:
    try:
        fps = int(value)
    except (TypeError, ValueError):
        fps = 24
    return 24 if fps != 24 else fps


def supports_reference_media(ark_model: str) -> bool:
    return ark_model in SEEDANCE20_MODELS or ark_model == SEEDANCE_10_LITE_I2V_MODEL
