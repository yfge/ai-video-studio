"""Submit one already-resolved video request to a provider."""

from __future__ import annotations

from typing import Any, Optional

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
    **kwargs: Any,
) -> AIResponse:
    if not hasattr(provider, "submit_video_task"):
        return build_failure_response(
            f"提供商 {provider_name} 不支持视频任务提交",
            provider_name,
            provider_model,
            model_type,
        )
    return await provider.submit_video_task(
        prompt=prompt,
        image_url=image_url,
        end_image_url=end_image_url,
        model=provider_model,
        duration=duration,
        fps=fps,
        resolution=resolution,
        **kwargs,
    )
