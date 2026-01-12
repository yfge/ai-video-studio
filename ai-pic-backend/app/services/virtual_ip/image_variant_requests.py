from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.prompts.template_audit import build_prompt_template_audit
from app.services.image_gen.coerce import (
    clean_str,
    coerce_str_list,
    maybe_float,
    maybe_int,
    value_from_payload,
)

DEFAULT_VARIANT_PROMPT = "为当前角色生成不同视角/姿态的图像，如背面照或全身照"


@dataclass(frozen=True, slots=True)
class VirtualIPVariantRequest:
    prompt: str
    model: str | None
    count: int | None
    size: str | None
    aspect_ratio: str | None
    style: str | None
    style_preset_id: str | None
    style_spec: Any | None
    generation_profile: str | None
    seed: int | None
    steps: int | None
    cfg_scale: float | None
    negative_prompt: str | None
    strength: float | None
    reference_images: list[str]


def resolve_virtual_ip_variant_request(
    payload: Mapping[str, Any],
    *,
    prompt: str | None,
    model: str | None,
    model_id: str | None,
    count: int | None,
    size: str | None,
    aspect_ratio: str | None,
    generation_profile: str | None = None,
    seed: int | None = None,
    steps: int | None = None,
    cfg_scale: float | None = None,
    negative_prompt: str | None = None,
    strength: float | None = None,
    base_image_model: str | None,
) -> VirtualIPVariantRequest:
    prompt_value = clean_str(value_from_payload(payload, "prompt", prompt))
    if not prompt_value:
        prompt_value = DEFAULT_VARIANT_PROMPT

    raw_model = clean_str(value_from_payload(payload, "model", model))
    selected_model = clean_str(
        value_from_payload(payload, "model_id", model_id) or raw_model
    ) or clean_str(base_image_model)
    count_int = maybe_int(value_from_payload(payload, "count", count))

    size_value = clean_str(value_from_payload(payload, "size", size))
    aspect_ratio_value = clean_str(
        value_from_payload(payload, "aspect_ratio", aspect_ratio)
    )
    generation_profile_value = clean_str(
        value_from_payload(payload, "generation_profile", generation_profile)
    )
    seed_int = maybe_int(value_from_payload(payload, "seed", seed))
    steps_int = maybe_int(value_from_payload(payload, "steps", steps))
    cfg_scale_value = maybe_float(value_from_payload(payload, "cfg_scale", cfg_scale))
    negative_prompt_value = clean_str(
        value_from_payload(payload, "negative_prompt", negative_prompt)
    )
    strength_value = maybe_float(value_from_payload(payload, "strength", strength))

    style_hint = clean_str(payload.get("style")) or "realistic"
    style_preset_id_value = clean_str(payload.get("style_preset_id"))
    style_spec_value = payload.get("style_spec")

    reference_images = coerce_str_list(payload.get("reference_images") or [])

    return VirtualIPVariantRequest(
        prompt=prompt_value,
        model=selected_model,
        count=count_int,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        style=style_hint,
        style_preset_id=style_preset_id_value,
        style_spec=style_spec_value,
        generation_profile=generation_profile_value,
        seed=seed_int,
        steps=steps_int,
        cfg_scale=cfg_scale_value,
        negative_prompt=negative_prompt_value,
        strength=strength_value,
        reference_images=reference_images,
    )


def build_virtual_ip_variant_task_payload(
    *,
    virtual_ip_id: int,
    virtual_ip_business_id: str | None,
    image_id: int,
    request: VirtualIPVariantRequest,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "virtual_ip_id": virtual_ip_id,
        "virtual_ip_business_id": virtual_ip_business_id,
        "image_id": image_id,
        "prompt": request.prompt,
        "model": request.model,
        "count": request.count,
        "size": request.size,
        "aspect_ratio": request.aspect_ratio,
        "style": request.style,
        "style_preset_id": request.style_preset_id,
        "style_spec": request.style_spec,
        "generation_profile": request.generation_profile,
        "seed": request.seed,
        "steps": request.steps,
        "cfg_scale": request.cfg_scale,
        "negative_prompt": request.negative_prompt,
        "strength": request.strength,
        "reference_images": request.reference_images,
        "prompt_template": build_prompt_template_audit("virtual_ip_image_variant"),
    }
    return {k: v for k, v in payload.items() if v is not None}
