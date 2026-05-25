"""Model resolution helpers for AI manager provider calls."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Optional

from .providers.base import AIModelType, BaseProvider, ModelInfo

ModelFetcher = Callable[
    [BaseProvider, Optional[AIModelType]],
    Awaitable[Sequence[ModelInfo]],
]


def _static_models(provider: BaseProvider, model_type: AIModelType) -> list[ModelInfo]:
    return [
        model
        for model in getattr(provider, "available_models", [])
        if model.model_type == model_type
    ]


async def _resolve_static_or_remote_model(
    provider: BaseProvider,
    requested_model: Optional[str],
    model_type: AIModelType,
    get_models_for_type: ModelFetcher,
) -> str:
    if requested_model:
        return requested_model

    static_models = _static_models(provider, model_type)
    if static_models:
        return static_models[0].model_id

    available_models = await get_models_for_type(provider, model_type)
    if available_models:
        return available_models[0].model_id

    return getattr(provider, "default_model", "default")


async def resolve_text_model(
    provider: BaseProvider,
    requested_model: Optional[str],
    get_models_for_type: ModelFetcher,
) -> str:
    return await _resolve_static_or_remote_model(
        provider,
        requested_model,
        AIModelType.TEXT_GENERATION,
        get_models_for_type,
    )


async def resolve_image_model(
    provider: BaseProvider,
    requested_model: Optional[str],
    get_models_for_type: ModelFetcher,
) -> str:
    return await _resolve_static_or_remote_model(
        provider,
        requested_model,
        AIModelType.TEXT_TO_IMAGE,
        get_models_for_type,
    )


async def resolve_image_to_image_model(
    provider: BaseProvider,
    requested_model: Optional[str],
    get_models_for_type: ModelFetcher,
) -> str:
    if requested_model:
        return requested_model

    img2img_models = await get_models_for_type(provider, AIModelType.IMAGE_TO_IMAGE)
    if img2img_models:
        return img2img_models[0].model_id

    text_to_image_models = await get_models_for_type(
        provider,
        AIModelType.TEXT_TO_IMAGE,
    )
    return text_to_image_models[0].model_id if text_to_image_models else "default"


async def resolve_video_model(
    provider: BaseProvider,
    requested_model: Optional[str],
    model_type: AIModelType,
    get_models_for_type: ModelFetcher,
) -> str:
    if requested_model:
        return requested_model

    static_models = _static_models(provider, model_type)
    if not static_models and model_type == AIModelType.IMAGE_TO_VIDEO:
        static_models = _static_models(provider, AIModelType.TEXT_TO_VIDEO)
    if static_models:
        return static_models[0].model_id

    available_models = await get_models_for_type(provider, model_type)
    if not available_models and model_type == AIModelType.IMAGE_TO_VIDEO:
        available_models = await get_models_for_type(
            provider,
            AIModelType.TEXT_TO_VIDEO,
        )

    if available_models:
        return available_models[0].model_id
    return getattr(provider, "default_model", "default")
