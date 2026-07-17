"""Resolve eligible video providers after model and reference filtering."""

from typing import Any, Optional

from app.services.providers.base import AIModelType
from app.services.video.video_reference_media import filter_reference_media_candidates


def resolve_video_provider_candidates(
    ai_manager: Any,
    model: Optional[str],
    prefer_provider: Optional[str],
    model_type: AIModelType,
    *,
    image_url: Optional[str],
    end_image_url: Optional[str],
    request_kwargs: dict[str, Any],
) -> tuple[list[str], Optional[str], Optional[str]]:
    available = ai_manager.get_available_providers(model_type=model_type)
    prefer_provider, model = ai_manager._resolve_prefer_provider_and_model(
        model, prefer_provider
    )
    available = filter_reference_media_candidates(
        ai_manager,
        available,
        image_url=image_url,
        end_image_url=end_image_url,
        request_kwargs=request_kwargs,
    )
    if prefer_provider:
        available = [provider for provider in available if provider == prefer_provider]
    return available, prefer_provider, model
