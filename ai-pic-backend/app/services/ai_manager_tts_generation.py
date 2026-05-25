"""Text-to-speech fallback orchestration for AI service manager."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.services import ai_manager_failure_responses as failure_responses
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
)


async def text_to_speech_with_fallback(
    *,
    text: str,
    model: str | None,
    prefer_provider: str | None,
    voice_type: str | None,
    speed: float,
    provider_kwargs: dict[str, Any],
    providers: dict[str, BaseProvider],
    max_retries: int,
    enable_fallback: bool,
    get_available_providers: Callable[..., list[str]],
    select_provider: Callable[[list[str], str | None], str | None],
    update_request_count: Callable[[str], None],
    log_request: Callable[..., None],
    log_prompt: Callable[[str | None], None],
    log_response: Callable[..., None],
) -> AIResponse:
    """Generate speech with provider fallback and terminal failure details."""
    available_providers = get_available_providers(model_type=AIModelType.TEXT_TO_SPEECH)
    last_error: str | None = None
    last_provider: str | None = None

    if not available_providers:
        return failure_responses.manager_failure_response(
            error="没有可用的语音合成提供商",
            model=model,
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )

    log_request(
        task="text_to_speech",
        provider=prefer_provider,
        model=model,
        params={"voice_type": voice_type, "speed": speed},
    )
    log_prompt(text)

    for _ in range(max_retries):
        provider_name = select_provider(available_providers, prefer_provider)
        if not provider_name:
            break

        provider = providers[provider_name]
        update_request_count(provider_name)

        try:
            response = await _call_provider_text_to_speech(
                provider,
                provider_name=provider_name,
                text=text,
                model=model,
                voice_type=voice_type,
                speed=speed,
                provider_kwargs=provider_kwargs,
            )
            log_response(
                task="text_to_speech",
                provider=provider_name,
                model=model,
                response=response,
            )
            if not response.success and response.error:
                last_error = response.error
                last_provider = provider_name
            if response.success or not enable_fallback:
                return response
        except Exception as exc:
            last_error = str(exc)
            last_provider = provider_name
            if not enable_fallback:
                return failure_responses.exception_failure_response(
                    action="语音合成失败",
                    exc=exc,
                    provider=provider_name,
                    model=model or "unknown",
                    task_type=AITaskType.VOICE_GENERATION,
                    model_type=AIModelType.TEXT_TO_SPEECH,
                )

        if provider_name in available_providers:
            available_providers.remove(provider_name)

    return failure_responses.terminal_failure_response(
        default_error="所有语音合成提供商都失败了",
        last_error=last_error,
        last_provider=last_provider,
        model=model or "unknown",
        task_type=AITaskType.VOICE_GENERATION,
        model_type=AIModelType.TEXT_TO_SPEECH,
    )


async def _call_provider_text_to_speech(
    provider: BaseProvider,
    *,
    provider_name: str,
    text: str,
    model: str | None,
    voice_type: str | None,
    speed: float,
    provider_kwargs: dict[str, Any],
) -> AIResponse:
    if hasattr(provider, "text_to_speech"):
        return await provider.text_to_speech(
            text=text,
            model=model,
            voice_type=voice_type,
            speed=speed,
            **provider_kwargs,
        )
    return AIResponse(
        success=False,
        error=f"提供商 {provider_name} 不支持语音合成",
        provider=provider_name,
        model=model or "unknown",
        task_type=AITaskType.VOICE_GENERATION,
        model_type=AIModelType.TEXT_TO_SPEECH,
    )
