"""Text-to-image fallback orchestration for AI service manager."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.services import ai_manager_failure_responses as failure_responses
from app.services import ai_manager_image_invocation as image_invocation
from app.services import ai_manager_image_style as image_style
from app.services import ai_manager_model_resolution as model_resolution
from app.services.ai_manager_logging import AI_MANAGER_PROVIDER
from app.services.media.invocation_references import collect_input_references
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
)
from app.utils.model_utils import normalize_openai_image_style


async def generate_image_with_fallback(
    *,
    prompt: str,
    model: str | None,
    prefer_provider: str | None,
    width: int,
    height: int,
    style: str,
    style_preset_id: str | None,
    style_spec: Any | None,
    call_scene: str,
    provider_kwargs: dict[str, Any],
    providers: dict[str, BaseProvider],
    max_retries: int,
    enable_fallback: bool,
    logger: Any,
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
    """Generate images with style resolution, provider fallback, and OSS upload."""
    original_prompt = prompt
    style_state = image_style.resolve_text_to_image_style(
        prompt=prompt,
        legacy_style=style,
        style_preset_id=style_preset_id,
        style_spec=style_spec,
    )
    prompt = style_state.prompt
    style = style_state.legacy_style
    openai_style_override = style_state.openai_style_override
    resolved_style_spec = style_state.resolved_style_spec
    style_resolution_meta = style_state.resolution_meta

    available_providers = get_available_providers(model_type=AIModelType.TEXT_TO_IMAGE)
    prefer_provider, model = resolve_prefer_provider_and_model(model, prefer_provider)
    if prefer_provider:
        available_providers = [p for p in available_providers if p == prefer_provider]

    original_model = model
    last_model_used = original_model

    if not available_providers:
        return failure_responses.manager_failure_response(
            error="没有可用的图像生成提供商",
            model=model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    log_request(
        task="generate_image",
        provider=prefer_provider,
        model=model,
        params={"width": width, "height": height, "style": style},
    )
    log_prompt(provider_kwargs.get("prompt_override", prompt))

    last_error: str | None = None
    last_provider: str | None = None
    last_model: str | None = None
    references = collect_input_references(provider_kwargs=provider_kwargs)
    input_references: list[dict[str, Any]] | None = None

    for attempt_index in range(1, max_retries + 1):
        provider_name = select_provider(available_providers, prefer_provider)
        if not provider_name:
            break

        provider = providers[provider_name]
        update_request_count(provider_name)
        provider_model = await model_resolution.resolve_image_model(
            provider,
            original_model,
            get_models_for_type,
        )
        last_model_used = provider_model
        if input_references is None:
            input_references = await image_invocation.persist_inputs(
                references,
                provider=provider_name,
                model=provider_model,
                logger=logger,
            )
        invocation = image_invocation.begin_attempt(
            invocation_type="text_to_image",
            call_scene=call_scene,
            provider=provider_name,
            model=provider_model,
            attempt_index=attempt_index,
            original_prompt=original_prompt,
            effective_prompt=str(provider_kwargs.get("prompt_override") or prompt),
            input_references=input_references,
            request_parameters={
                "width": width,
                "height": height,
                "style": _provider_style(provider_name, style, openai_style_override),
                "style_preset_id": style_preset_id,
                "style_spec": resolved_style_spec,
                "provider_kwargs": provider_kwargs,
            },
        )

        try:
            response = await provider.generate_image(
                prompt=prompt,
                model=provider_model,
                width=width,
                height=height,
                style=_provider_style(
                    provider_name,
                    style,
                    openai_style_override,
                ),
                **provider_kwargs,
            )
            image_style.attach_style_metadata(
                response,
                resolved_style_spec,
                style_resolution_meta,
            )
            log_response(
                task="generate_image",
                provider=provider_name,
                model=provider_model,
                response=response,
            )
            if not response.success and response.error:
                last_error = response.error
                last_provider = provider_name
                last_model = provider_model
            await image_invocation.finish_attempt(
                invocation,
                response,
                provider=provider_name,
                model=provider_model,
                prefix="ai-generated/text-to-image",
                logger=logger,
            )
            if response.success or not enable_fallback:
                return response
        except Exception as exc:
            image_invocation.fail_attempt(invocation, str(exc))
            last_error = str(exc)
            last_provider = provider_name
            last_model = provider_model
            if not enable_fallback:
                return failure_responses.exception_failure_response(
                    action="图像生成失败",
                    exc=exc,
                    provider=provider_name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                )

        if provider_name in available_providers:
            available_providers.remove(provider_name)

    if last_error:
        return failure_responses.failure_response(
            error=failure_responses.provider_prefixed_error(
                last_error,
                last_provider,
            ),
            provider=last_provider or AI_MANAGER_PROVIDER,
            model=last_model or last_model_used or model or "unknown",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    return failure_responses.manager_failure_response(
        error="所有图像生成提供商都失败了",
        model=last_model_used,
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
    )


def _provider_style(
    provider_name: str,
    style: str,
    openai_style_override: str | None,
) -> str:
    if provider_name != "openai":
        return style
    return normalize_openai_image_style(openai_style_override or style)
