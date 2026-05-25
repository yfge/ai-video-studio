"""Model listing aggregation for AI service manager."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.services import ai_manager_model_cache as model_cache
from app.services.providers.base import AIModelType, BaseProvider, ModelInfo


async def list_models(
    *,
    providers: dict[str, BaseProvider],
    provider_weights: dict[str, Any],
    models_cache: dict[str, tuple[float, list[dict[str, Any]]]],
    cache_ttl: float,
    model_type: AIModelType | None,
    source: str,
    get_models_for_type: Callable[
        [BaseProvider, AIModelType | None],
        Awaitable[list[ModelInfo]],
    ],
) -> list[dict[str, Any]]:
    """Aggregate model metadata from enabled providers."""
    cache_key = model_cache.model_cache_key(source, model_type)
    cached_models = model_cache.get_cached_models(
        models_cache,
        cache_ttl=cache_ttl,
        cache_key=cache_key,
    )
    if cached_models is not None:
        return cached_models

    models: list[dict[str, Any]] = []
    for provider_name, provider in providers.items():
        weight = provider_weights.get(provider_name)
        if weight and not weight.enabled:
            continue

        try:
            infos = await _fetch_provider_models(
                provider,
                model_type=model_type,
                source=source,
                get_models_for_type=get_models_for_type,
            )
        except Exception:
            continue

        for model_info in infos or []:
            if not _supports_model_type(model_info, model_type):
                continue
            models.append(_model_info_payload(provider_name, model_info))

    models.sort(key=lambda x: (x["provider"], x.get("name") or x["id"]))
    model_cache.store_cached_models(
        models_cache,
        cache_ttl=cache_ttl,
        cache_key=cache_key,
        models=models,
    )
    return models


async def _fetch_provider_models(
    provider: BaseProvider,
    *,
    model_type: AIModelType | None,
    source: str,
    get_models_for_type: Callable[
        [BaseProvider, AIModelType | None],
        Awaitable[list[ModelInfo]],
    ],
) -> list[ModelInfo]:
    if source == "static":
        return provider.available_models
    if source == "remote":
        return await provider.fetch_remote_models(model_type=model_type)
    return await get_models_for_type(provider, model_type)


def _supports_model_type(
    model_info: ModelInfo,
    model_type: AIModelType | None,
) -> bool:
    if model_type is None:
        return True
    capabilities = [str(item).lower() for item in model_info.capabilities or []]
    supports_capability = (
        model_type == AIModelType.IMAGE_TO_IMAGE and "image_to_image" in capabilities
    ) or (model_type == AIModelType.IMAGE_TO_VIDEO and "image_to_video" in capabilities)
    return supports_capability or model_info.model_type == model_type


def _model_info_payload(provider_name: str, model_info: ModelInfo) -> dict[str, Any]:
    return {
        "provider": provider_name,
        "id": model_info.model_id,
        "name": model_info.name,
        "type": model_info.model_type.value,
        "capabilities": model_info.capabilities,
        "metadata": getattr(model_info, "metadata", {}) or {},
    }
