from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.prompts.template_audit import build_prompt_template_audit
from app.services.image_gen.coerce import (
    clean_str,
    coerce_str_list,
    maybe_int,
    value_from_payload,
)


@dataclass(frozen=True, slots=True)
class EnvironmentTextToImageRequest:
    prompt: str | None
    model: str | None
    count: int | None
    size: str | None
    aspect_ratio: str | None
    style: str | None
    style_preset_id: str | None
    style_spec: Any | None


@dataclass(frozen=True, slots=True)
class EnvironmentImageVariantRequest:
    base_image: str | None
    prompt: str | None
    model: str | None
    count: int | None
    size: str | None
    aspect_ratio: str | None
    style: str | None
    style_preset_id: str | None
    style_spec: Any | None
    reference_images: list[str]


def resolve_environment_text_to_image_request(
    payload: Mapping[str, Any],
    *,
    prompt: str | None,
    model: str | None,
    count: int | None,
    size: str | None,
    aspect_ratio: str | None,
) -> EnvironmentTextToImageRequest:
    extra_prompt = clean_str(value_from_payload(payload, "prompt", prompt))
    selected_model = clean_str(value_from_payload(payload, "model", model))
    count_int = maybe_int(value_from_payload(payload, "count", count))
    size_value = clean_str(value_from_payload(payload, "size", size))
    aspect_ratio_value = clean_str(
        value_from_payload(payload, "aspect_ratio", aspect_ratio)
    )

    style_hint = clean_str(payload.get("style")) or "realistic"
    style_preset_id_value = clean_str(payload.get("style_preset_id"))
    style_spec_value = payload.get("style_spec")

    return EnvironmentTextToImageRequest(
        prompt=extra_prompt,
        model=selected_model,
        count=count_int,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        style=style_hint,
        style_preset_id=style_preset_id_value,
        style_spec=style_spec_value,
    )


def resolve_environment_image_variant_request(
    payload: Mapping[str, Any],
    *,
    base_image: str | None,
    fallback_base_image: str | None,
    prompt: str | None,
    model: str | None,
    count: int | None,
    size: str | None,
    aspect_ratio: str | None,
) -> EnvironmentImageVariantRequest:
    base_value = clean_str(value_from_payload(payload, "base_image", base_image))
    if not base_value:
        base_value = clean_str(fallback_base_image)

    extra_prompt = clean_str(value_from_payload(payload, "prompt", prompt))
    selected_model = clean_str(value_from_payload(payload, "model", model))
    count_int = maybe_int(value_from_payload(payload, "count", count))
    size_value = clean_str(value_from_payload(payload, "size", size))
    aspect_ratio_value = clean_str(
        value_from_payload(payload, "aspect_ratio", aspect_ratio)
    )

    style_hint = clean_str(payload.get("style")) or "realistic"
    style_preset_id_value = clean_str(payload.get("style_preset_id"))
    style_spec_value = payload.get("style_spec")

    reference_images = coerce_str_list(payload.get("reference_images") or [])

    return EnvironmentImageVariantRequest(
        base_image=base_value,
        prompt=extra_prompt,
        model=selected_model,
        count=count_int,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        style=style_hint,
        style_preset_id=style_preset_id_value,
        style_spec=style_spec_value,
        reference_images=reference_images,
    )


def build_environment_text_to_image_task_payload(
    *,
    env_id: int,
    request: EnvironmentTextToImageRequest,
) -> dict[str, Any]:
    """Build Celery payload for environment text-to-image.

    Uses `extra_prompt` key for backward compatibility with older workers/endpoints.
    """
    payload: dict[str, Any] = {
        "env_id": env_id,
        "extra_prompt": request.prompt,
        "model": request.model,
        "count": request.count,
        "size": request.size,
        "aspect_ratio": request.aspect_ratio,
        "style": request.style,
        "style_preset_id": request.style_preset_id,
        "style_spec": request.style_spec,
        "prompt_template": build_prompt_template_audit("environment_image"),
    }
    return {k: v for k, v in payload.items() if v is not None}


def build_environment_variant_task_payload(
    *,
    env_id: int,
    request: EnvironmentImageVariantRequest,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "env_id": env_id,
        "base_image": request.base_image,
        "prompt": request.prompt,
        "model": request.model,
        "count": request.count,
        "size": request.size,
        "aspect_ratio": request.aspect_ratio,
        "style": request.style,
        "style_preset_id": request.style_preset_id,
        "style_spec": request.style_spec,
        "reference_images": request.reference_images,
        "prompt_template": build_prompt_template_audit("environment_image"),
    }
    return {k: v for k, v in payload.items() if v is not None}
