from __future__ import annotations

from typing import Any


def _normalize_model_id(model_id: str) -> str:
    return (model_id or "").strip().lower().replace(".", "-")


def supports_guidance_scale(model_id: str) -> bool:
    """Whether the target model supports Volcengine `guidance_scale`."""
    mid = _normalize_model_id(model_id)
    if "seedream-3-0" in mid and "t2i" in mid:
        return True
    if "seededit-3-0" in mid and "i2i" in mid:
        return True
    return False


def coerce_guidance_scale(value: Any) -> float | None:
    """Coerce cfg_scale/guidance_scale into Ark guidance_scale range [1, 10]."""
    if value is None:
        return None
    try:
        scale = float(value)
    except (TypeError, ValueError):
        return None
    if scale < 1:
        return 1.0
    if scale > 10:
        return 10.0
    return float(scale)
