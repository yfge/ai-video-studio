from __future__ import annotations

from typing import Any, Optional

from app.services.ai_service_manager import AIServiceManager
from app.services.providers.base import AIModelType


async def resolve_provider_model(
    ai_manager: AIServiceManager,
    provider: Any,
    model_type: AIModelType,
    original_model: Optional[str],
) -> str:
    if original_model:
        return original_model
    static_models = [
        m for m in getattr(provider, "available_models", []) if m.model_type == model_type
    ]
    if not static_models and model_type == AIModelType.IMAGE_TO_VIDEO:
        static_models = [
            m
            for m in getattr(provider, "available_models", [])
            if m.model_type == AIModelType.TEXT_TO_VIDEO
        ]
    if static_models:
        return static_models[0].model_id

    available_models = await ai_manager._get_models_for_type(provider, model_type)
    if not available_models and model_type == AIModelType.IMAGE_TO_VIDEO:
        available_models = await ai_manager._get_models_for_type(
            provider,
            AIModelType.TEXT_TO_VIDEO,
        )
    if available_models:
        return available_models[0].model_id
    return getattr(provider, "default_model", "default")
