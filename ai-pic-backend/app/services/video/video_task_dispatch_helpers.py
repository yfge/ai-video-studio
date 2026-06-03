from __future__ import annotations

from typing import Any, Optional

from app.services.providers.base import AIModelType, AIResponse, AITaskType

DISPATCHER_PROVIDER = "video_task_dispatcher"


def resolve_model_type(image_url: Optional[str], kwargs: dict[str, Any]) -> AIModelType:
    if image_url or has_visual_reference(kwargs):
        return AIModelType.IMAGE_TO_VIDEO
    return AIModelType.TEXT_TO_VIDEO


def has_visual_reference(kwargs: dict[str, Any]) -> bool:
    def has_value(value: Any) -> bool:
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, dict):
            return bool(value)
        return isinstance(value, list) and any(has_value(item) for item in value)

    keys = (
        "reference_images",
        "reference_image_urls",
        "reference_videos",
        "video_urls",
    )
    return any(has_value(kwargs.get(key)) for key in keys)


def log_submission(
    ai_manager: Any,
    *,
    prompt: Optional[str],
    image_url: Optional[str],
    prefer_provider: Optional[str],
    model: Optional[str],
    duration: int,
    fps: int,
    resolution: str,
    model_type: AIModelType,
) -> None:
    ai_manager._log_request(
        task="submit_video_task",
        provider=prefer_provider,
        model=model,
        params={
            "duration": duration,
            "fps": fps,
            "resolution": resolution,
            "mode": model_type.value,
        },
    )
    ai_manager._log_prompt(
        prompt
        if not image_url
        else f"<image_url>: {ai_manager._truncate(image_url, 256)}"
    )


def build_failure_response(
    message: str,
    provider: str,
    model: Optional[str],
    model_type: AIModelType,
) -> AIResponse:
    return AIResponse(
        success=False,
        error=message,
        provider=provider,
        model=model or "unknown",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=model_type,
    )
