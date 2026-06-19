from __future__ import annotations

from typing import Any, Optional


def filter_reference_media_candidates(
    ai_manager: Any,
    available: list[str],
    *,
    image_url: Optional[str],
    end_image_url: Optional[str],
    request_kwargs: dict[str, Any],
) -> list[str]:
    if image_url or end_image_url or not _has_reference_media(request_kwargs):
        return available
    capable = [
        provider_name
        for provider_name in available
        if _provider_supports_reference_media(ai_manager, provider_name)
    ]
    return capable or available


def _provider_supports_reference_media(ai_manager: Any, provider_name: str) -> bool:
    provider = ai_manager.providers.get(provider_name)
    if provider is None:
        return False
    for model_info in getattr(provider, "available_models", []) or []:
        capabilities = set(getattr(model_info, "capabilities", []) or [])
        if capabilities.intersection(
            {"reference_images", "reference_video", "reference_audio"}
        ):
            return True
        ui = (getattr(model_info, "metadata", {}) or {}).get("ui") or {}
        if ui.get("supports_reference_images") or ui.get("supports_reference_video"):
            return True
    return False


def _has_reference_media(request_kwargs: dict[str, Any]) -> bool:
    for key in (
        "reference_images",
        "reference_image_urls",
        "reference_videos",
        "video_urls",
        "reference_audios",
        "audio_urls",
    ):
        value = request_kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and any(
            _reference_item_has_url(item) for item in value
        ):
            return True
    return False


def _reference_item_has_url(item: Any) -> bool:
    if isinstance(item, str):
        return bool(item.strip())
    if not isinstance(item, dict):
        return False
    for key in ("url", "image_url", "video_url", "audio_url"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False
