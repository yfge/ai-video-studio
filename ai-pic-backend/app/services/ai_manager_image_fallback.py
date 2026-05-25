"""Image fallback helpers for AI manager image-to-image paths."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.services.ai_manager_logging import truncate

from .providers.base import AIModelType, AIResponse, AITaskType

GenerateImageCallable = Callable[..., Awaitable[AIResponse]]


@dataclass
class ImageFallbackResult:
    response: AIResponse | None = None
    last_error: str | None = None
    last_provider: str | None = None
    last_model: str | None = None


def infer_image_provider_from_model(model: str | None) -> str | None:
    if not model:
        return None
    lower = model.lower()
    if (
        lower.startswith("seedream")
        or lower.startswith("volcengine")
        or "doubao" in lower
        or "seedream" in lower
    ):
        return "volcengine"
    if lower.startswith("deepseek"):
        return "deepseek"
    if lower.startswith("keling") or lower.startswith("kling"):
        return "keling"
    if lower.startswith("jimeng"):
        return "jimeng"
    if lower.startswith(("dall-e", "dalle", "gpt-image", "img-gen")):
        return "openai"
    if lower.startswith("gemini"):
        return "google"
    return None


def fallback_prompt_for_image_to_image(prompt: str | None) -> str:
    return prompt or "为当前角色生成不同视角/姿态的图像，例如背面照或全身照"


async def fallback_image_to_image_as_text_to_image(
    generate_image: GenerateImageCallable,
    *,
    prompt: str | None,
    model: str | None,
    prefer_provider: str | None,
    image_url: str,
    count: int | None,
    legacy_style: str,
    style_preset_id: str | None,
    style_spec: Any | None,
    logger: Any,
) -> ImageFallbackResult:
    """Fallback image-to-image to text-to-image while preserving trace metadata."""
    try:
        inferred_provider = infer_image_provider_from_model(model)
        fallback_prompt = fallback_prompt_for_image_to_image(prompt)
        logger.warning(
            "image_to_image fallback: using text-to-image without reference | model=%s provider_hint=%s image_url=%s",
            model,
            inferred_provider or prefer_provider,
            truncate(image_url, 256),
        )

        text_resp = await generate_image(
            prompt=fallback_prompt,
            model=model,
            prefer_provider=inferred_provider or prefer_provider,
            prompt_override=fallback_prompt,
            style=legacy_style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            n=count or 1,
        )
        if text_resp and text_resp.success:
            meta = dict(text_resp.metadata or {})
            meta.update(
                {
                    "fallback_mode": "text_to_image_without_reference",
                    "fallback_from": "image_to_image",
                    "original_image_url": image_url,
                }
            )
            text_resp.metadata = meta
            text_resp.model_type = AIModelType.IMAGE_TO_IMAGE
            text_resp.task_type = AITaskType.SCENE_GENERATION
            return ImageFallbackResult(response=text_resp)

        if text_resp and not text_resp.success:
            error_value = (text_resp.error or "").strip() or "未知错误"
            return ImageFallbackResult(
                last_error=error_value,
                last_provider=text_resp.provider,
                last_model=text_resp.model,
            )
    except Exception as e:
        logger.error("image_to_image fallback failed: %s", e)
        return ImageFallbackResult(last_error=str(e).strip() or repr(e))

    return ImageFallbackResult()
