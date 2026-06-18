"""Request helpers for storyboard image generation."""

from __future__ import annotations

from typing import Any, Sequence

from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)
from app.services.image_gen.provider_params import supported_ai_manager_keys
from app.utils.model_utils import infer_provider_from_model, parse_model_and_provider

CODEX_OVERLOAD_FALLBACK_MODEL = "volcengine:doubao-seedream-4-5-251128"


def normalize_storyboard_request(
    *,
    prompt: str,
    refs: Sequence[str],
    model: str | None,
    generation_profile: str | None,
    count: int | None,
    size: str | None,
    aspect_ratio: str | None,
    width: int | None,
    height: int | None,
    style: str | None,
    style_preset_id: str | None,
    style_spec: Any | None,
    seed: int | None,
    steps: int | None,
    cfg_scale: float | None,
    negative_prompt: str | None,
    strength: float | None,
    backend: str,
):
    provider = _resolve_provider(model)
    supports_t2i_refs = _supports_text_to_image_reference_images(provider)
    if refs and strength is None and supports_t2i_refs:
        mode = ImageGenMode.TEXT_TO_IMAGE
        base_image = None
        extra_images = refs
    else:
        mode = ImageGenMode.IMAGE_TO_IMAGE if refs else ImageGenMode.TEXT_TO_IMAGE
        base_image = refs[0] if refs else None
        extra_images = refs[1:] if len(refs) > 1 else []
    return (
        normalize_image_gen_request(
            ImageGenRequest(
                domain=ImageGenDomain.STORYBOARD,
                mode=mode,
                prompt=prompt,
                model=model,
                generation_profile=generation_profile,
                style=style,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
                count=count,
                size=size,
                aspect_ratio=aspect_ratio,
                width=width,
                height=height,
                seed=seed,
                steps=steps,
                cfg_scale=cfg_scale,
                negative_prompt=negative_prompt,
                strength=strength,
                base_image=base_image,
                reference_images=extra_images,
                backend_base=backend,
            ),
            strict=False,
        ),
        mode,
    )


async def generate_with_normalized_request(*, ai_service: Any, normalized, mode):
    call = build_ai_manager_call(normalized)
    if mode == ImageGenMode.IMAGE_TO_IMAGE:
        if not call.get("image_url"):
            raise RuntimeError("Storyboard img2img missing base image URL")
        return await ai_service.ai_manager.image_to_image(**call)
    return await ai_service.ai_manager.generate_image(**call)


def is_codex_overload(model: str | None, error: str | None) -> bool:
    return (
        isinstance(model, str)
        and model.lower().startswith("codex:")
        and "overloaded" in (error or "").lower()
    )


def _supports_text_to_image_reference_images(provider: str | None) -> bool:
    keys = supported_ai_manager_keys(provider or "", ImageGenMode.TEXT_TO_IMAGE)
    return "reference_images" in keys or "extra_images" in keys


def _resolve_provider(model: str | None) -> str | None:
    clean_model, provider_hint = parse_model_and_provider(model)
    provider = provider_hint or (
        infer_provider_from_model(clean_model or "") if clean_model else None
    )
    return provider.lower() if provider else None
