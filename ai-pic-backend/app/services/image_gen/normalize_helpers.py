from __future__ import annotations

from app.services.providers.image_param_utils import (
    normalize_image_params,
    size_to_dimensions,
)

from .types import ImageGenAudit


def clamp_count(value: int | None, *, audit: ImageGenAudit) -> int:
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


def normalize_seed(value: int | None, *, audit: ImageGenAudit) -> int | None:
    if value is None:
        return None
    try:
        seed_int = int(value)
    except (TypeError, ValueError):
        audit.warnings.append(f"invalid seed '{value}', ignoring")
        audit.dropped_fields.append("seed")
        return None
    if seed_int < 0:
        audit.dropped_fields.append("seed")
        return None
    max_seed = 2**31 - 1
    if seed_int > max_seed:
        audit.warnings.append(f"seed > {max_seed}, clamped")
        return max_seed
    return seed_int


def normalize_steps(value: int | None, *, audit: ImageGenAudit) -> int | None:
    if value is None:
        return None
    try:
        steps_int = int(value)
    except (TypeError, ValueError):
        audit.warnings.append(f"invalid steps '{value}', ignoring")
        audit.dropped_fields.append("steps")
        return None
    if steps_int < 1:
        audit.dropped_fields.append("steps")
        return None
    max_steps = 60
    if steps_int > max_steps:
        audit.warnings.append(f"steps > {max_steps}, clamped")
        return max_steps
    return steps_int


def normalize_cfg_scale(value: float | None, *, audit: ImageGenAudit) -> float | None:
    if value is None:
        return None
    try:
        cfg_value = float(value)
    except (TypeError, ValueError):
        audit.warnings.append(f"invalid cfg_scale '{value}', ignoring")
        audit.dropped_fields.append("cfg_scale")
        return None
    if cfg_value <= 0:
        audit.dropped_fields.append("cfg_scale")
        return None
    max_cfg = 30.0
    if cfg_value > max_cfg:
        audit.warnings.append(f"cfg_scale > {max_cfg}, clamped")
        return max_cfg
    return float(cfg_value)


def normalize_strength(value: float | None, *, audit: ImageGenAudit) -> float | None:
    if value is None:
        return None
    try:
        strength_value = float(value)
    except (TypeError, ValueError):
        audit.warnings.append(f"invalid strength '{value}', ignoring")
        audit.dropped_fields.append("strength")
        return None
    if strength_value < 0:
        audit.warnings.append("strength < 0, clamped")
        return 0.0
    if strength_value > 1:
        audit.warnings.append("strength > 1, clamped")
        return 1.0
    return float(strength_value)


def normalize_unit_float(
    value: float | None,
    *,
    audit: ImageGenAudit,
    field_name: str,
) -> float | None:
    """Normalize a [0,1] float field with audit tracing."""
    if value is None:
        return None
    try:
        float_value = float(value)
    except (TypeError, ValueError):
        audit.warnings.append(f"invalid {field_name} '{value}', ignoring")
        audit.dropped_fields.append(field_name)
        return None
    if float_value < 0:
        audit.warnings.append(f"{field_name} < 0, clamped")
        return 0.0
    if float_value > 1:
        audit.warnings.append(f"{field_name} > 1, clamped")
        return 1.0
    return float(float_value)


def normalize_size_ratio(
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


def resolve_dimensions(
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
