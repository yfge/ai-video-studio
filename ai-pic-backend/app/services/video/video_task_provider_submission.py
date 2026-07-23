"""Submit one already-resolved video request to a provider."""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.services import ai_manager_video_invocation as video_invocation
from app.services.media.invocation_references import collect_input_references
from app.services.providers.base import AIModelType, AIResponse
from app.services.video.video_task_dispatch_helpers import build_failure_response


async def submit_to_video_provider(
    *,
    provider_name: str,
    provider: Any,
    provider_model: str,
    prompt: Optional[str],
    image_url: Optional[str],
    end_image_url: Optional[str],
    duration: int,
    fps: int,
    resolution: str,
    model_type: AIModelType,
    call_scene: str | None = None,
    invocation_attempt_index: int = 1,
    **kwargs: Any,
) -> AIResponse:
    references = collect_input_references(
        image_url=image_url,
        end_image_url=end_image_url,
        provider_kwargs=kwargs,
    )
    input_references = await video_invocation.persist_inputs(
        references,
        provider=provider_name,
        model=provider_model,
        logger=get_logger("video_task_provider_submission"),
    )
    invocation = video_invocation.begin_attempt(
        invocation_type=model_type.value,
        call_scene=call_scene or "app.services.video.video_task_dispatcher",
        provider=provider_name,
        model=provider_model,
        attempt_index=invocation_attempt_index,
        prompt=prompt,
        input_references=input_references,
        request_parameters={
            "duration": duration,
            "fps": fps,
            "resolution": resolution,
            "provider_kwargs": kwargs,
        },
    )
    if not hasattr(provider, "submit_video_task"):
        response = build_failure_response(
            f"提供商 {provider_name} 不支持视频任务提交",
            provider_name,
            provider_model,
            model_type,
        )
    else:
        try:
            response = await provider.submit_video_task(
                prompt=prompt,
                image_url=image_url,
                end_image_url=end_image_url,
                model=provider_model,
                duration=duration,
                fps=fps,
                resolution=resolution,
                **kwargs,
            )
        except Exception as exc:
            video_invocation.fail_attempt(invocation, str(exc))
            raise
    video_invocation.finish_attempt(invocation, response)
    return response
