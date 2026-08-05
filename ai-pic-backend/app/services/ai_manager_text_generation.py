"""Text generation fallback orchestration for AI service manager."""

from __future__ import annotations

import asyncio
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
    call_scene: str,
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
    begin_invocation: Callable[..., Any],
    finish_invocation: Callable[..., None],
) -> AIResponse:
    """Generate text with provider fallback and default model resolution."""
    invocation_input_references = provider_kwargs.pop(
        "invocation_input_references", None
    )
    available_providers = get_available_providers(
        model_type=AIModelType.TEXT_GENERATION
    )
    prefer_provider, model = resolve_prefer_provider_and_model(model, prefer_provider)
    if prefer_provider:
        available_providers = [p for p in available_providers if p == prefer_provider]

    original_model = model
    last_model_used = original_model
    model_providers = {
        provider_name
        for provider_name in available_providers
        if original_model
        and any(
            item.model_id == original_model
            and item.model_type == AIModelType.TEXT_GENERATION
            for item in getattr(providers[provider_name], "available_models", [])
        )
    }
    if model_providers and not prefer_provider:
        available_providers = [
            *[name for name in available_providers if name in model_providers],
            *[name for name in available_providers if name not in model_providers],
        ]
    last_error: str | None = None
    last_provider: str | None = None

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

    for attempt_index in range(max_retries):
        provider_name = select_provider(available_providers, prefer_provider)
        if not provider_name:
            break

        provider = providers[provider_name]
        update_request_count(provider_name)
        requested_model = (
            original_model
            if provider_name in model_providers
            or (not model_providers and attempt_index == 0)
            else None
        )
        provider_model = await model_resolution.resolve_text_model(
            provider,
            requested_model,
            get_models_for_type,
        )
        last_model_used = provider_model
        invocation = begin_invocation(
            call_scene=call_scene,
            provider=provider_name,
            model=provider_model,
            attempt_index=attempt_index + 1,
            prompt=prompt,
            system_prompt=system_prompt,
            request_parameters={
                **params,
                "json_schema": json_schema,
                "provider_kwargs": provider_kwargs,
            },
            input_references=invocation_input_references,
        )
        if invocation_input_references and invocation is None:
            raise RuntimeError(
                "required LLM invocation audit could not be persisted before provider call"
            )

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
            invocation_id = (
                invocation.get("row_id")
                if isinstance(invocation, dict)
                else getattr(invocation, "row_id", None)
            )
            if invocation_id is not None:
                response.metadata = {
                    **dict(response.metadata or {}),
                    "llm_invocation_id": int(invocation_id),
                }
            log_response(
                task="generate_text",
                provider=provider_name,
                model=provider_model,
                response=response,
            )
            finish_invocation(invocation, response=response)
            if not response.success and response.error:
                last_error = response.error
                last_provider = provider_name
            if response.success or not enable_fallback:
                return response
        except asyncio.CancelledError:
            finish_invocation(invocation, error="provider call cancelled")
            raise
        except Exception as exc:
            finish_invocation(invocation, error=str(exc))
            last_error = str(exc)
            last_provider = provider_name
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

    return failure_responses.terminal_failure_response(
        default_error="所有文本生成提供商都失败了",
        last_error=last_error,
        last_provider=last_provider,
        model=last_model_used or "unknown",
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
