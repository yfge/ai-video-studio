from __future__ import annotations

from dataclasses import replace

from app.services.providers.image_param_utils import (
    normalize_image_params,
    size_to_dimensions,
)
from app.utils.model_utils import infer_provider_from_model, parse_model_and_provider

from .policies import get_policy
from .refs import normalize_reference_images, resolve_base_image
from .types import ImageGenAudit, ImageGenMode, ImageGenNormalized, ImageGenRequest


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

    count = _clamp_count(req.count, audit=audit)

    clean_model, provider_hint = parse_model_and_provider(req.model)
    provider = (
        req.prefer_provider
        or provider_hint
        or (infer_provider_from_model(clean_model or "") if clean_model else None)
    )
    provider = provider.lower() if provider else None

    size_value = _clean_optional_str(req.size)
    aspect_ratio_value = _clean_optional_str(req.aspect_ratio)

    normalized_size, normalized_ratio = _normalize_size_ratio(
        provider=provider,
        model_id=clean_model,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        strict=strict,
        audit=audit,
    )

    width, height = _resolve_dimensions(
        width=req.width,
        height=req.height,
        size=normalized_size,
        audit=audit,
    )

    backend_base = (req.backend_base or "").rstrip("/") or None
    extra_images = (
        normalize_reference_images(
            req.reference_images, backend_base=backend_base or ""
        )
        if backend_base
        else []
    )
    if req.reference_images and not backend_base:
        audit.warnings.append(
            "backend_base is missing; reference_images not normalized"
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

    return ImageGenNormalized(
        domain=req.domain,
        mode=req.mode,
        provider=provider,
        model_id=clean_model,
        prompt=prompt,
        style=style,
        style_preset_id=_clean_optional_str(req.style_preset_id),
        style_spec=req.style_spec if policy.allow_style_spec else None,
        size=normalized_size,
        aspect_ratio=normalized_ratio,
        width=width,
        height=height,
        count=count,
        base_image_url=base_image_url,
        extra_images=extra_images,
        audit=audit,
    )


def _apply_overrides(request: ImageGenRequest, overrides: dict) -> ImageGenRequest:
    if not overrides:
        return request
    return replace(request, **overrides)


def _clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _clamp_count(value: int | None, *, audit: ImageGenAudit) -> int:
    if value is None:
        audit.defaults_applied["count"] = 1
        return 1
    try:
        num = int(value)
    except (TypeError, ValueError):
        audit.warnings.append(f"invalid count '{value}', defaulting to 1")
        audit.defaults_applied["count"] = 1
        return 1
    if num < 1:
        audit.warnings.append("count < 1, clamped to 1")
        return 1
    if num > 4:
        audit.warnings.append("count > 4, clamped to 4")
        return 4
    return num


def _normalize_size_ratio(
    *,
    provider: str | None,
    model_id: str | None,
    size: str | None,
    aspect_ratio: str | None,
    strict: bool,
    audit: ImageGenAudit,
) -> tuple[str | None, str | None]:
    if not provider or not model_id:
        return size, aspect_ratio
    try:
        normalized_size, normalized_ratio, _ = normalize_image_params(
            provider, model_id, size, aspect_ratio, strict=strict
        )
        return normalized_size, normalized_ratio
    except ValueError as exc:
        if strict:
            raise
        audit.warnings.append(str(exc))
        # Conservative fallback: keep size, drop ratio
        return size, None


def _resolve_dimensions(
    *,
    width: int | None,
    height: int | None,
    size: str | None,
    audit: ImageGenAudit,
) -> tuple[int, int]:
    width_value = width
    height_value = height
    if width_value is None or height_value is None:
        dims = size_to_dimensions(size or "")
        if dims:
            width_value, height_value = dims
            audit.defaults_applied["width_height_from_size"] = size
    if width_value is None:
        width_value = 1024
        audit.defaults_applied["width"] = 1024
    if height_value is None:
        height_value = 1024
        audit.defaults_applied["height"] = 1024
    return int(width_value), int(height_value)
