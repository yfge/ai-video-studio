from __future__ import annotations

from dataclasses import replace

from app.utils.model_utils import infer_provider_from_model, parse_model_and_provider

from .coerce import clean_str
from .normalize_helpers import (
    clamp_count,
    normalize_size_ratio,
    resolve_dimensions,
)
from .normalize_profile import resolve_profile_params
from .policies import get_policy
from .provider_params import supported_ai_manager_keys
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

    profile_params = resolve_profile_params(
        provider=provider,
        model_id=clean_model,
        request=req,
        audit=audit,
    )
    generation_profile = profile_params.generation_profile
    seed = profile_params.seed
    steps = profile_params.steps
    cfg_scale = profile_params.cfg_scale
    negative_prompt = profile_params.negative_prompt
    strength = profile_params.strength
    image_reference = profile_params.image_reference
    image_fidelity = profile_params.image_fidelity
    human_fidelity = profile_params.human_fidelity

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
        text_keys = supported_ai_manager_keys(
            provider or "", ImageGenMode.TEXT_TO_IMAGE
        )
        supports_reference_images = (
            "reference_images" in text_keys
            or "extra_images" in text_keys
            or "image" in text_keys
        )
    else:
        image_keys = supported_ai_manager_keys(
            provider or "", ImageGenMode.IMAGE_TO_IMAGE
        )
        supports_reference_images = (
            "extra_images" in image_keys or "reference_images" in image_keys
        )

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

    if (
        provider == "keling"
        and req.mode == ImageGenMode.TEXT_TO_IMAGE
        and extra_images
    ):
        if len(extra_images) > 1:
            audit.warnings.append(
                "keling text_to_image supports only 1 reference image; using the first"
            )
            audit.dropped_fields.append("reference_images")
            extra_images = extra_images[:1]

        if negative_prompt:
            prompt = _append_negative_prompt_to_prompt(prompt, negative_prompt)
            audit.warnings.append(
                "keling text_to_image ignores negative_prompt when reference images are provided; merged into prompt"
            )
            audit.dropped_fields.append("negative_prompt")
            negative_prompt = None

    if (
        provider == "google"
        and req.mode == ImageGenMode.TEXT_TO_IMAGE
        and extra_images
        and len(extra_images) > 4
    ):
        audit.warnings.append(
            "google/gemini text_to_image reference_images limited to 4 to reduce 413 risk; using the first 4"
        )
        audit.dropped_fields.append("reference_images")
        extra_images = extra_images[:4]

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
