"""Text generation fallback orchestration for AI service manager."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.services import ai_manager_failure_responses as failure_responses
from app.services import ai_manager_model_resolution as model_resolution
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
)


async def generate_text_with_fallback(
    *,
    prompt: str,
    model: str | None,
    prefer_provider: str | None,
    system_prompt: str | None,
    max_tokens: int | None,
    temperature: float,
    json_schema: dict | None,
    stream: bool,
    provider_kwargs: dict[str, Any],
    providers: dict[str, BaseProvider],
    max_retries: int,
    enable_fallback: bool,
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
    """Generate text with provider fallback and default model resolution."""
    available_providers = get_available_providers(
        model_type=AIModelType.TEXT_GENERATION
    )
    prefer_provider, model = resolve_prefer_provider_and_model(model, prefer_provider)
    if prefer_provider:
        available_providers = [p for p in available_providers if p == prefer_provider]

    original_model = model
    last_model_used = original_model

    if not available_providers:
        return failure_responses.manager_failure_response(
            error="没有可用的文本生成提供商",
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    params: dict[str, Any] = {
        "temperature": temperature,
        "json_schema": True if json_schema else False,
        "stream": stream,
    }
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    log_request(
        task="generate_text",
        provider=prefer_provider,
        model=model,
        params=params,
    )
    log_prompt(prompt)

    for _ in range(max_retries):
        provider_name = select_provider(available_providers, prefer_provider)
        if not provider_name:
            break

        provider = providers[provider_name]
        update_request_count(provider_name)
        provider_model = await model_resolution.resolve_text_model(
            provider,
            original_model,
            get_models_for_type,
        )
        last_model_used = provider_model

        try:
            response = await provider.generate_text(
                **_provider_text_kwargs(
                    prompt=prompt,
                    model=provider_model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    json_schema=json_schema,
                    stream=stream,
                    max_tokens=max_tokens,
                    provider_kwargs=provider_kwargs,
                )
            )
            log_response(
                task="generate_text",
                provider=provider_name,
                model=provider_model,
                response=response,
            )
            if response.success or not enable_fallback:
                return response
        except Exception as exc:
            if not enable_fallback:
                return failure_responses.exception_failure_response(
                    action="文本生成失败",
                    exc=exc,
                    provider=provider_name,
                    model=model,
                    task_type=AITaskType.STORY_GENERATION,
                    model_type=AIModelType.TEXT_GENERATION,
                )

        if provider_name in available_providers:
            available_providers.remove(provider_name)

    return failure_responses.manager_failure_response(
        error="所有文本生成提供商都失败了",
        model=last_model_used,
        task_type=AITaskType.STORY_GENERATION,
        model_type=AIModelType.TEXT_GENERATION,
    )


def _provider_text_kwargs(
    *,
    prompt: str,
    model: str | None,
    system_prompt: str | None,
    temperature: float,
    json_schema: dict | None,
    stream: bool,
    max_tokens: int | None,
    provider_kwargs: dict[str, Any],
) -> dict[str, Any]:
    kwargs = {
        "prompt": prompt,
        "model": model,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "json_schema": json_schema,
        "stream": stream,
        **provider_kwargs,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return kwargs
