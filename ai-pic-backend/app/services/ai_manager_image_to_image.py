"""Image-to-image fallback orchestration for AI service manager."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.services import ai_manager_failure_responses as failure_responses
from app.services import ai_manager_image_assets as image_assets
from app.services import ai_manager_image_fallback as image_fallback
from app.services import ai_manager_image_style as image_style
from app.services import ai_manager_model_resolution as model_resolution
from app.services.ai_manager_logging import AI_MANAGER_PROVIDER
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
)


async def image_to_image_with_fallback(
    *,
    image_url: str,
    prompt: str | None,
    model: str | None,
    prefer_provider: str | None,
    count: int | None,
    style_preset_id: str | None,
    style_spec: Any | None,
    provider_kwargs: dict[str, Any],
    providers: dict[str, BaseProvider],
    max_retries: int,
    enable_fallback: bool,
    default_timeout: float,
    logger: Any,
    generate_image: Callable[..., Awaitable[AIResponse]],
    resolve_prefer_provider_and_model: Callable[
        [str | None, str | None],
        tuple[str | None, str | None],
    ],
    get_available_providers: Callable[..., list[str]],
    select_provider: Callable[[list[str], str | None], str | None],
    update_request_count: Callable[[str], None],
    get_models_for_type: Callable[
        [BaseProvider, AIModelType | None],
        Awaitable[list[ModelInfo]],
    ],
    log_request: Callable[..., None],
    log_prompt: Callable[[str | None], None],
    log_response: Callable[..., None],
) -> AIResponse:
    """Generate image variants with reference preload and text-to-image fallback."""
    legacy_style = str(provider_kwargs.get("style") or "realistic")
    style_state = image_style.resolve_image_to_image_style(
        prompt=prompt,
        legacy_style=legacy_style,
        style_preset_id=style_preset_id,
        style_spec=style_spec,
    )
    prompt = style_state.prompt
    legacy_style = style_state.legacy_style
    resolved_style_spec = style_state.resolved_style_spec
    style_resolution_meta = style_state.resolution_meta
    if resolved_style_spec is not None:
        provider_kwargs["style"] = legacy_style

    available_providers = get_available_providers(model_type=AIModelType.IMAGE_TO_IMAGE)
    prefer_provider, model = resolve_prefer_provider_and_model(model, prefer_provider)
    if prefer_provider:
        available_providers = [p for p in available_providers if p == prefer_provider]

    if not available_providers:
        return failure_responses.manager_failure_response(
            error="没有可用的图生图提供商",
            model=model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )

    log_request(
        task="image_to_image",
        provider=prefer_provider,
        model=model,
        params={"image_url": image_url},
    )
    log_prompt(prompt)

    base64_images = await image_assets.preload_image_references_as_data_urls(
        image_url=image_url,
        extra_images=list(provider_kwargs.get("extra_images") or []),
        prefer_provider=prefer_provider,
        available_providers=available_providers,
        timeout=default_timeout,
        logger=logger,
    )
    if base64_images:
        provider_kwargs["base64_images"] = base64_images

    last_error: str | None = None
    last_provider: str | None = None
    last_model: str | None = None

    for _ in range(max_retries):
        provider_name = select_provider(available_providers, prefer_provider)
        if not provider_name:
            break

        provider = providers[provider_name]
        update_request_count(provider_name)
        effective_model = await model_resolution.resolve_image_to_image_model(
            provider,
            model,
            get_models_for_type,
        )

        try:
            response = await provider.image_to_image(
                image_url=image_url,
                prompt=prompt,
                model=effective_model,
                n=count or 1,
                **provider_kwargs,
            )
            log_response(
                task="image_to_image",
                provider=provider_name,
                model=effective_model,
                response=response,
            )
            image_style.attach_style_metadata(
                response,
                resolved_style_spec,
                style_resolution_meta,
            )
            if not response.success:
                last_error = (response.error or "").strip() or "未知错误"
                last_provider = provider_name
                last_model = effective_model
            if response.success or not enable_fallback:
                await _convert_success_images_to_oss(response, logger)
                return response
        except Exception as exc:
            last_error = str(exc).strip() or repr(exc)
            last_provider = provider_name
            last_model = effective_model
            if not enable_fallback:
                return failure_responses.exception_failure_response(
                    action="图生图失败",
                    exc=exc,
                    provider=provider_name,
                    model=effective_model,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.IMAGE_TO_IMAGE,
                )

        if provider_name in available_providers:
            available_providers.remove(provider_name)

    if enable_fallback:
        fallback_result = await image_fallback.fallback_image_to_image_as_text_to_image(
            generate_image,
            prompt=prompt,
            model=model,
            prefer_provider=prefer_provider,
            image_url=image_url,
            count=count,
            legacy_style=legacy_style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            logger=logger,
        )
        if fallback_result.response:
            return fallback_result.response
        if fallback_result.last_error is not None:
            last_error = fallback_result.last_error
            last_provider = fallback_result.last_provider
            last_model = fallback_result.last_model

    if last_error is not None:
        return failure_responses.failure_response(
            error=failure_responses.provider_prefixed_error(
                last_error,
                last_provider,
            ),
            provider=last_provider or AI_MANAGER_PROVIDER,
            model=last_model or model or "unknown",
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )

    return failure_responses.manager_failure_response(
        error="所有图生图提供商都失败了（未捕获到具体错误信息）",
        model=model,
        task_type=AITaskType.SCENE_GENERATION,
        model_type=AIModelType.IMAGE_TO_IMAGE,
    )


async def _convert_success_images_to_oss(response: AIResponse, logger: Any) -> None:
    if not response.success or not response.data or "images" not in response.data:
        return
    converted_images = await image_assets.convert_base64_images_to_oss(
        response.data["images"],
        prefix="ai-generated/image-to-image",
        logger=logger,
    )
    response.data["images"] = converted_images
