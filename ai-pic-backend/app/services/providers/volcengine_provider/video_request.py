"""Build Volcengine Ark video generation requests."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..base import AIModelType
from .video_models import (
    SEEDANCE_10_FAST_MODEL,
    SEEDANCE_10_LITE_I2V_MODEL,
    SEEDANCE_10_PRO_MODEL,
    SEEDANCE_15_PRO_MODEL,
    SEEDANCE_20_FAST_MODEL,
    SEEDANCE_20_MODEL,
)
from .video_request_params import (
    apply_generation_params,
    apply_task_params,
    supports_reference_media,
)


def _normalize_model(model: Optional[str]) -> str:
    """Normalize UI aliases to Ark model IDs."""
    raw = (model or "").strip()
    normalized = raw.lower() if raw else ""
    if not normalized:
        return SEEDANCE_20_MODEL

    aliases = {
        "volcengine-video": SEEDANCE_20_MODEL,
        "seedance-2": SEEDANCE_20_MODEL,
        "seedance-2.0": SEEDANCE_20_MODEL,
        "seedance-2.0-i2v": SEEDANCE_20_MODEL,
        "seedance-2-0": SEEDANCE_20_MODEL,
        "doubao-seedance-2-0": SEEDANCE_20_MODEL,
        "seedance-2.0-fast": SEEDANCE_20_FAST_MODEL,
        "seedance-2.0-fast-i2v": SEEDANCE_20_FAST_MODEL,
        "seedance-2-0-fast": SEEDANCE_20_FAST_MODEL,
        "doubao-seedance-2-0-fast": SEEDANCE_20_FAST_MODEL,
        "seedance-1.5-pro": SEEDANCE_15_PRO_MODEL,
        "seedream-i2v-fast": SEEDANCE_10_FAST_MODEL,
        "seedream-i2v-pro-fast": SEEDANCE_10_FAST_MODEL,
        "seedream-i2v-lite": SEEDANCE_10_LITE_I2V_MODEL,
        "seedream-i2v-pro": SEEDANCE_10_PRO_MODEL,
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized.startswith("seedream-i2v"):
        return SEEDANCE_10_PRO_MODEL
    return raw


def build_video_request(
    *,
    prompt: Optional[str],
    image_url: Optional[str],
    end_image_url: Optional[str],
    model: Optional[str],
    duration: int,
    fps: int,
    resolution: str,
    ratio: Optional[str],
    watermark: Optional[bool],
    seed: Optional[int],
    camera_fixed: Optional[bool],
    service_tier: Optional[str],
    execution_expires_after: Optional[int],
    return_last_frame: Optional[bool],
    extra_kwargs: Dict[str, Any],
) -> tuple[str, AIModelType, Dict[str, Any], Dict[str, Any]]:
    """Return normalized model, model type, request body, and metadata."""
    ark_model = _normalize_model(model)
    final_prompt = (prompt or "").strip() or "生成一段符合描述的视频"
    content = _build_content(
        final_prompt,
        image_url,
        end_image_url,
        ark_model,
        extra_kwargs,
    )
    media_mode = any(item["type"] != "text" for item in content)
    request_data: Dict[str, Any] = {"model": ark_model, "content": content}

    resolved = apply_generation_params(
        request_data,
        ark_model=ark_model,
        duration=duration,
        fps=fps,
        resolution=resolution,
        ratio=ratio,
        watermark=watermark,
        seed=seed,
        camera_fixed=camera_fixed,
    )
    apply_task_params(
        request_data,
        ark_model=ark_model,
        service_tier=service_tier,
        execution_expires_after=execution_expires_after,
        return_last_frame=return_last_frame,
        extra_kwargs=extra_kwargs,
    )
    model_type = AIModelType.IMAGE_TO_VIDEO if media_mode else AIModelType.TEXT_TO_VIDEO
    return ark_model, model_type, request_data, resolved


def has_visual_reference(extra_kwargs: Dict[str, Any]) -> bool:
    for key in (
        "reference_images",
        "reference_image_urls",
        "reference_videos",
        "video_urls",
    ):
        if _coerce_urls(extra_kwargs.get(key)):
            return True
    return False


def _build_content(
    prompt: str,
    image_url: Optional[str],
    end_image_url: Optional[str],
    ark_model: str,
    extra_kwargs: Dict[str, Any],
) -> list[Dict[str, Any]]:
    content: list[Dict[str, Any]] = []
    first_last_mode = bool(image_url or end_image_url)
    if image_url:
        content.append(_media_item("image", image_url, "first_frame"))
    if end_image_url:
        content.append(_media_item("image", end_image_url, "last_frame"))
    content.append({"type": "text", "text": prompt})
    if first_last_mode:
        return content

    if supports_reference_media(ark_model):
        ref_images = extra_kwargs.get("reference_images") or extra_kwargs.get(
            "reference_image_urls"
        )
        ref_videos = extra_kwargs.get("reference_videos") or extra_kwargs.get(
            "video_urls"
        )
        ref_audios = extra_kwargs.get("reference_audios") or extra_kwargs.get(
            "audio_urls"
        )
        for url in _coerce_urls(ref_images)[:9]:
            content.append(_media_item("image", url, "reference_image"))
        for url in _coerce_urls(ref_videos)[:3]:
            content.append(_media_item("video", url, "reference_video"))
        has_visual_ref = any(
            item["type"] in {"image_url", "video_url"} for item in content
        )
        if has_visual_ref:
            for url in _coerce_urls(ref_audios)[:3]:
                content.append(_media_item("audio", url, "reference_audio"))
    return content


def _media_item(kind: str, url: str, role: str) -> Dict[str, Any]:
    key = f"{kind}_url"
    return {"type": key, key: {"url": url}, "role": role}


def _coerce_urls(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, list):
        return []
    urls: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            urls.append(item)
        elif isinstance(item, dict):
            url = (
                item.get("url")
                or item.get("image_url")
                or item.get("video_url")
                or item.get("audio_url")
            )
            if isinstance(url, str) and url.strip():
                urls.append(url)
    return urls
