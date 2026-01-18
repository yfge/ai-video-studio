from __future__ import annotations

from typing import Any, TypeVar

from app.services.providers.volcengine_provider.guidance_scale import (
    supports_guidance_scale,
)

from .provider_params import supported_ai_manager_keys
from .types import ImageGenAudit, ImageGenMode


def apply_capability_drops(
    *,
    provider: str | None,
    model_id: str | None,
    mode: ImageGenMode,
    audit: ImageGenAudit,
    seed: int | None,
    steps: int | None,
    cfg_scale: float | None,
    strength: float | None,
    image_reference: str | None,
    image_fidelity: float | None,
    human_fidelity: float | None,
    style_preset_id: str | None,
    style_spec: Any | None,
) -> tuple[
    int | None,
    int | None,
    float | None,
    float | None,
    str | None,
    float | None,
    float | None,
    str | None,
    Any | None,
]:
    """Drop params that the target provider/mode/model cannot honor.

    This keeps normalized metadata aligned with what `build_ai_manager_call()`
    will send downstream, and records human-readable warnings for UX/debugging.
    """
    provider_key = (provider or "").lower()
    supported_keys = supported_ai_manager_keys(provider_key, mode)

    T = TypeVar("T")

    def _drop_if_unsupported(
        field_name: str,
        value: T | None,
        *,
        supported: bool,
        warning: str,
    ) -> T | None:
        if value is None or supported:
            return value
        if field_name not in audit.dropped_fields:
            audit.dropped_fields.append(field_name)
        if warning and warning not in audit.warnings:
            audit.warnings.append(warning)
        return None

    seed = _drop_if_unsupported(
        "seed",
        seed,
        supported=("seed" in supported_keys),
        warning=f"seed ignored (unsupported provider '{provider_key or 'unknown'}')",
    )
    steps = _drop_if_unsupported(
        "steps",
        steps,
        supported=("steps" in supported_keys),
        warning=f"steps ignored (unsupported provider '{provider_key or 'unknown'}')",
    )

    cfg_supported = "cfg_scale" in supported_keys
    if provider_key == "volcengine" and cfg_supported:
        cfg_supported = supports_guidance_scale(model_id or "")
    cfg_scale = _drop_if_unsupported(
        "cfg_scale",
        cfg_scale,
        supported=cfg_supported,
        warning=(
            "cfg_scale ignored (unsupported provider/model "
            f"'{provider_key or 'unknown'}:{model_id or 'unknown'}')"
        ),
    )

    strength = _drop_if_unsupported(
        "strength",
        strength,
        supported=("strength" in supported_keys),
        warning=(
            f"strength ignored (unsupported provider '{provider_key or 'unknown'}')"
        ),
    )
    image_reference = _drop_if_unsupported(
        "image_reference",
        image_reference,
        supported=("image_reference" in supported_keys),
        warning=(
            "image_reference ignored (unsupported provider "
            f"'{provider_key or 'unknown'}')"
        ),
    )
    image_fidelity = _drop_if_unsupported(
        "image_fidelity",
        image_fidelity,
        supported=("image_fidelity" in supported_keys),
        warning=(
            "image_fidelity ignored (unsupported provider "
            f"'{provider_key or 'unknown'}')"
        ),
    )
    human_fidelity = _drop_if_unsupported(
        "human_fidelity",
        human_fidelity,
        supported=("human_fidelity" in supported_keys),
        warning=(
            "human_fidelity ignored (unsupported provider "
            f"'{provider_key or 'unknown'}')"
        ),
    )

    style_preset_id = _drop_if_unsupported(
        "style_preset_id",
        style_preset_id,
        supported=("style_preset_id" in supported_keys),
        warning=(
            "style_preset_id ignored (unsupported provider "
            f"'{provider_key or 'unknown'}')"
        ),
    )
    style_spec = _drop_if_unsupported(
        "style_spec",
        style_spec,
        supported=("style_spec" in supported_keys),
        warning=(
            f"style_spec ignored (unsupported provider '{provider_key or 'unknown'}')"
        ),
    )

    return (
        seed,
        steps,
        cfg_scale,
        strength,
        image_reference,
        image_fidelity,
        human_fidelity,
        style_preset_id,
        style_spec,
    )
