from __future__ import annotations

from dataclasses import replace

from app.utils.model_utils import infer_provider_from_model, parse_model_and_provider

from .coerce import clean_str
from .negative_prompts import VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA, merge_negative_prompt
from .normalize_helpers import (
    clamp_count,
    normalize_cfg_scale,
    normalize_seed,
    normalize_size_ratio,
    normalize_steps,
    normalize_strength,
    normalize_unit_float,
    resolve_dimensions,
)
from .policies import get_policy
from .provider_params import supported_ai_manager_keys
from .profiles import resolve_image_gen_profile
from .refs import normalize_reference_images, resolve_base_image
from .types import (
    ImageGenAudit,
    ImageGenDomain,
    ImageGenMode,
    ImageGenNormalized,
    ImageGenRequest,
)


def _append_negative_prompt_to_prompt(prompt: str, negative_prompt: str) -> str:
    cleaned = (negative_prompt or "").strip()
    if not cleaned:
        return prompt
    suffix = f"Avoid: {cleaned}"
    if not prompt.strip():
        return suffix
    return f"{prompt.rstrip()}\n\n{suffix}"


def normalize_image_gen_request(
    request: ImageGenRequest,
    *,
    strict: bool = False,
) -> ImageGenNormalized:
    """Normalize an ImageGenRequest into a stable form for downstream execution."""
    audit = ImageGenAudit()
    policy = get_policy(request.domain)
    overrides = policy.apply(request)
    req = _apply_overrides(request, overrides)

    style = (req.style or "realistic").strip() or "realistic"
    if req.style is None:
        audit.defaults_applied["style"] = style

    count = clamp_count(req.count, audit=audit)

    clean_model, provider_hint = parse_model_and_provider(req.model)
    provider = (
        req.prefer_provider
        or provider_hint
        or (infer_provider_from_model(clean_model or "") if clean_model else None)
    )
    provider = provider.lower() if provider else None

    if (
        req.mode == ImageGenMode.IMAGE_TO_IMAGE
        and provider == "keling"
        and (clean_model or "").strip().lower() in {"kling-v2-1", "kling-image-v2-1"}
    ):
        audit.warnings.append(
            "keling model kling-v2-1 does not support image_to_image; using kling-v2"
        )
        clean_model = "kling-v2"

    size_value = clean_str(req.size)
    aspect_ratio_value = clean_str(req.aspect_ratio)

    requested_profile = clean_str(req.generation_profile)
    profile = resolve_image_gen_profile(
        provider=provider,
        model_id=clean_model,
        mode=req.mode,
        requested_profile=requested_profile,
    )
    generation_profile = profile.id if profile else None
    if profile and requested_profile and profile.id != requested_profile:
        audit.warnings.append(
            f"unknown generation_profile '{requested_profile}', using '{profile.id}'"
        )
    if requested_profile and profile is None:
        audit.warnings.append(
            f"generation_profile '{requested_profile}' ignored (unsupported provider/model)"
        )
    if profile and not requested_profile:
        audit.defaults_applied["generation_profile"] = profile.id

    seed = normalize_seed(req.seed, audit=audit)
    steps_input = req.steps
    if steps_input is None and profile and profile.defaults.steps is not None:
        steps_input = profile.defaults.steps
        audit.defaults_applied["steps"] = steps_input
    steps = normalize_steps(steps_input, audit=audit)
    if steps is None and req.steps is not None and profile and profile.defaults.steps:
        audit.warnings.append("invalid steps; falling back to generation_profile")
        audit.defaults_applied["steps"] = profile.defaults.steps
        steps = normalize_steps(profile.defaults.steps, audit=audit)

    cfg_input = req.cfg_scale
    if cfg_input is None and profile and profile.defaults.cfg_scale is not None:
        cfg_input = profile.defaults.cfg_scale
        audit.defaults_applied["cfg_scale"] = cfg_input
    cfg_scale = normalize_cfg_scale(cfg_input, audit=audit)
    if (
        cfg_scale is None
        and req.cfg_scale is not None
        and profile
        and profile.defaults.cfg_scale is not None
    ):
        audit.warnings.append("invalid cfg_scale; falling back to generation_profile")
        audit.defaults_applied["cfg_scale"] = profile.defaults.cfg_scale
        cfg_scale = normalize_cfg_scale(profile.defaults.cfg_scale, audit=audit)

    negative_prompt_input = clean_str(req.negative_prompt)
    used_profile_negative_prompt = False
    if (
        negative_prompt_input is None
        and profile
        and profile.defaults.negative_prompt is not None
    ):
        negative_prompt_input = clean_str(profile.defaults.negative_prompt)
        if negative_prompt_input is not None:
            used_profile_negative_prompt = True
            audit.defaults_applied["negative_prompt"] = negative_prompt_input
    negative_prompt = negative_prompt_input

    if used_profile_negative_prompt and req.domain == ImageGenDomain.VIRTUAL_IP:
        negative_prompt = merge_negative_prompt(
            negative_prompt, VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA
        )
        audit.defaults_applied["negative_prompt_virtual_ip"] = (
            VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA
        )

    strength = None
    image_reference = None
    image_fidelity = None
    human_fidelity = None
    if req.mode == ImageGenMode.IMAGE_TO_IMAGE:
        strength_input = req.strength
        if strength_input is None and profile and profile.defaults.strength is not None:
            strength_input = profile.defaults.strength
            audit.defaults_applied["strength"] = strength_input
        strength = normalize_strength(strength_input, audit=audit)

        image_reference_input = clean_str(req.image_reference)
        if (
            image_reference_input is None
            and profile
            and profile.defaults.image_reference is not None
        ):
            image_reference_input = clean_str(profile.defaults.image_reference)
            if image_reference_input is not None:
                audit.defaults_applied["image_reference"] = image_reference_input
        image_reference = image_reference_input

        if (
            provider == "keling"
            and image_reference is None
            and (clean_model or "").strip().lower()
            in {"kling-v1-5", "kling-image-v1-5"}
        ):
            image_reference = "subject"
            audit.defaults_applied["image_reference"] = image_reference

        image_fidelity_input = req.image_fidelity
        if (
            image_fidelity_input is None
            and profile
            and profile.defaults.image_fidelity is not None
        ):
            image_fidelity_input = profile.defaults.image_fidelity
            audit.defaults_applied["image_fidelity"] = image_fidelity_input
        image_fidelity = normalize_unit_float(
            image_fidelity_input,
            audit=audit,
            field_name="image_fidelity",
        )

        human_fidelity_input = req.human_fidelity
        if (
            human_fidelity_input is None
            and profile
            and profile.defaults.human_fidelity is not None
        ):
            human_fidelity_input = profile.defaults.human_fidelity
            audit.defaults_applied["human_fidelity"] = human_fidelity_input
        human_fidelity = normalize_unit_float(
            human_fidelity_input,
            audit=audit,
            field_name="human_fidelity",
        )
    elif req.strength is not None:
        audit.dropped_fields.append("strength")
        audit.warnings.append("strength ignored for text_to_image")

    normalized_size, normalized_ratio = normalize_size_ratio(
        provider=provider,
        model_id=clean_model,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        strict=strict,
        audit=audit,
    )

    width, height = resolve_dimensions(
        width=req.width,
        height=req.height,
        size=normalized_size,
        audit=audit,
    )

    backend_base = (req.backend_base or "").rstrip("/") or None
    supports_reference_images = False
    if req.mode == ImageGenMode.TEXT_TO_IMAGE:
        text_keys = supported_ai_manager_keys(provider or "", ImageGenMode.TEXT_TO_IMAGE)
        supports_reference_images = "reference_images" in text_keys or "extra_images" in text_keys
    else:
        image_keys = supported_ai_manager_keys(provider or "", ImageGenMode.IMAGE_TO_IMAGE)
        supports_reference_images = "extra_images" in image_keys or "reference_images" in image_keys

    extra_images: list[str] = []
    if req.reference_images:
        if not backend_base:
            audit.warnings.append(
                "backend_base is missing; reference_images not normalized"
            )
        elif not supports_reference_images:
            audit.warnings.append(
                f"reference_images ignored (unsupported provider '{provider or 'unknown'}')"
            )
            audit.dropped_fields.append("reference_images")
        else:
            extra_images = normalize_reference_images(
                req.reference_images, backend_base=backend_base
            )

    base_image_url = None
    if req.mode == ImageGenMode.IMAGE_TO_IMAGE:
        if not req.base_image:
            if strict:
                raise ValueError("base_image is required for image_to_image")
            audit.warnings.append("base_image missing for image_to_image")
            base_image_url = None
        elif backend_base:
            base_image_url = resolve_base_image(
                req.base_image, backend_base=backend_base
            )
        else:
            base_image_url = req.base_image
            audit.warnings.append("backend_base is missing; base_image not normalized")

    prompt = (req.prompt or "").strip()
    if not prompt:
        audit.warnings.append("empty prompt")

    supports_negative_prompt = "negative_prompt" in supported_ai_manager_keys(
        provider or "", req.mode
    )
    if negative_prompt and not supports_negative_prompt:
        prompt = _append_negative_prompt_to_prompt(prompt, negative_prompt)
        audit.warnings.append(
            f"negative_prompt not supported by provider '{provider or 'unknown'}'; merged into prompt"
        )
        audit.dropped_fields.append("negative_prompt")
        negative_prompt = None

    return ImageGenNormalized(
        domain=req.domain,
        mode=req.mode,
        provider=provider,
        model_id=clean_model,
        generation_profile=generation_profile,
        prompt=prompt,
        style=style,
        style_preset_id=clean_str(req.style_preset_id),
        style_spec=req.style_spec if policy.allow_style_spec else None,
        size=normalized_size,
        aspect_ratio=normalized_ratio,
        width=width,
        height=height,
        count=count,
        seed=seed,
        steps=steps,
        cfg_scale=cfg_scale,
        negative_prompt=negative_prompt,
        strength=strength,
        image_reference=image_reference,
        image_fidelity=image_fidelity,
        human_fidelity=human_fidelity,
        base_image_url=base_image_url,
        extra_images=extra_images,
        audit=audit,
    )


def _apply_overrides(request: ImageGenRequest, overrides: dict) -> ImageGenRequest:
    if not overrides:
        return request
    return replace(request, **overrides)
