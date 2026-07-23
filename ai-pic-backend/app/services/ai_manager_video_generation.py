"""Video generation fallback orchestration for AI service manager."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.services import ai_manager_failure_responses as failure_responses
from app.services import ai_manager_model_resolution as model_resolution
from app.services import ai_manager_video_invocation as video_invocation
from app.services.media.invocation_references import collect_input_references
from app.services.providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
)


async def generate_video_with_fallback(
    *,
    prompt: str | None,
    image_url: str | None,
    model: str | None,
    prefer_provider: str | None,
    duration: int,
    fps: int,
    resolution: str,
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
    truncate: Callable[[Any, int], str],
) -> AIResponse:
    """Generate video with provider fallback and terminal failure details."""
    model_type = AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
    available_providers = get_available_providers(model_type=model_type)

    prefer_provider, model = resolve_prefer_provider_and_model(model, prefer_provider)
    if prefer_provider:
        available_providers = [p for p in available_providers if p == prefer_provider]

    original_model = model
    last_model_used = original_model
    last_error: str | None = None
    last_provider: str | None = None
    references = collect_input_references(
        image_url=image_url,
        end_image_url=provider_kwargs.get("end_image_url"),
        provider_kwargs=provider_kwargs,
    )
    input_references: list[dict[str, Any]] | None = None

    if not available_providers:
        return failure_responses.manager_failure_response(
            error="没有可用的视频生成提供商",
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type,
        )

    log_request(
        task="generate_video",
        provider=prefer_provider,
        model=model,
        params={
            "duration": duration,
            "fps": fps,
            "resolution": resolution,
            "mode": ("image_to_video" if image_url else "text_to_video"),
        },
    )
    log_prompt(prompt if not image_url else f"<image_url>: {truncate(image_url, 256)}")

    for attempt_index in range(1, max_retries + 1):
        provider_name = select_provider(available_providers, prefer_provider)
        if not provider_name:
            break

        provider = providers[provider_name]
        update_request_count(provider_name)
        invocation = None

        try:
            provider_model = await model_resolution.resolve_video_model(
                provider,
                original_model,
                model_type,
                get_models_for_type,
            )
            last_model_used = provider_model
            if input_references is None:
                input_references = await video_invocation.persist_inputs(
                    references,
                    provider=provider_name,
                    model=provider_model,
                    logger=logger,
                )
            invocation = video_invocation.begin_attempt(
                invocation_type=model_type.value,
                call_scene=call_scene,
                provider=provider_name,
                model=provider_model,
                attempt_index=attempt_index,
                prompt=prompt,
                input_references=input_references,
                request_parameters={
                    "duration": duration,
                    "fps": fps,
                    "resolution": resolution,
                    "provider_kwargs": provider_kwargs,
                },
            )
            response = await _call_provider_generate_video(
                provider,
                provider_name=provider_name,
                prompt=prompt,
                image_url=image_url,
                model=provider_model,
                duration=duration,
                fps=fps,
                resolution=resolution,
                model_type=model_type,
                provider_kwargs=provider_kwargs,
            )
            log_response(
                task="generate_video",
                provider=provider_name,
                model=provider_model,
                response=response,
            )
            video_invocation.finish_attempt(invocation, response)
            if not response.success and response.error:
                last_error = response.error
                last_provider = provider_name
            if response.success or not enable_fallback:
                return response
        except Exception as exc:
            video_invocation.fail_attempt(invocation, str(exc))
            last_error = str(exc)
            last_provider = provider_name
            if not enable_fallback:
                return failure_responses.exception_failure_response(
                    action="视频生成失败",
                    exc=exc,
                    provider=provider_name,
                    model=last_model_used or "unknown",
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=model_type,
                )

        if provider_name in available_providers:
            available_providers.remove(provider_name)

    return failure_responses.terminal_failure_response(
        default_error="所有视频生成提供商都失败了",
        last_error=last_error,
        last_provider=last_provider,
        model=last_model_used or "unknown",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=model_type,
    )


async def _call_provider_generate_video(
    provider: BaseProvider,
    *,
    provider_name: str,
    prompt: str | None,
    image_url: str | None,
    model: str | None,
    duration: int,
    fps: int,
    resolution: str,
    model_type: AIModelType,
    provider_kwargs: dict[str, Any],
) -> AIResponse:
    if hasattr(provider, "generate_video"):
        return await provider.generate_video(
            prompt=prompt,
            image_url=image_url,
            model=model,
            duration=duration,
            fps=fps,
            resolution=resolution,
            **provider_kwargs,
        )
    return AIResponse(
        success=False,
        error=f"提供商 {provider_name} 不支持视频生成",
        provider=provider_name,
        model=model or "unknown",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=model_type,
    )
