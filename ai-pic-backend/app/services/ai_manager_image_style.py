"""Style spec helpers for AI manager image generation paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .providers.base import AIResponse


@dataclass
class TextToImageStyleState:
    prompt: str
    legacy_style: str
    openai_style_override: str | None = None
    resolved_style_spec: Any | None = None
    resolution_meta: dict[str, Any] | None = None


@dataclass
class ImageToImageStyleState:
    prompt: str | None
    legacy_style: str
    resolved_style_spec: Any | None = None
    resolution_meta: dict[str, Any] | None = None


def resolve_text_to_image_style(
    *,
    prompt: str,
    legacy_style: str,
    style_preset_id: str | None,
    style_spec: Any | None,
) -> TextToImageStyleState:
    if not style_preset_id and style_spec is None:
        return TextToImageStyleState(prompt=prompt, legacy_style=legacy_style)

    try:
        from app.utils.style_utils import (
            build_style_prompt,
            derive_legacy_image_style,
            derive_openai_image_style,
            resolve_style_spec,
        )

        resolved_style_spec, resolution_meta = resolve_style_spec(
            style_spec=style_spec,
            style_preset_id=style_preset_id,
            legacy_style=legacy_style,
            fill_defaults=True,
        )
        style_prompt = build_style_prompt(resolved_style_spec)
        if style_prompt:
            prompt = f"{prompt.rstrip()}\n\n{style_prompt}"
        legacy_style = derive_legacy_image_style(resolved_style_spec)
        openai_style_override = derive_openai_image_style(
            resolved_style_spec,
            fallback=legacy_style,
        )
        return TextToImageStyleState(
            prompt=prompt,
            legacy_style=legacy_style,
            openai_style_override=openai_style_override,
            resolved_style_spec=resolved_style_spec,
            resolution_meta=resolution_meta,
        )
    except Exception as exc:  # pragma: no cover - defensive parity
        return TextToImageStyleState(
            prompt=prompt,
            legacy_style=legacy_style,
            resolution_meta={"error": str(exc)},
        )


def resolve_image_to_image_style(
    *,
    prompt: str | None,
    legacy_style: str,
    style_preset_id: str | None,
    style_spec: Any | None,
) -> ImageToImageStyleState:
    if not style_preset_id and style_spec is None:
        return ImageToImageStyleState(prompt=prompt, legacy_style=legacy_style)

    try:
        from app.utils.style_utils import (
            build_style_prompt,
            derive_legacy_image_style,
            resolve_style_spec,
        )

        resolved_style_spec, resolution_meta = resolve_style_spec(
            style_spec=style_spec,
            style_preset_id=style_preset_id,
            legacy_style=legacy_style,
            fill_defaults=True,
        )
        style_prompt = build_style_prompt(resolved_style_spec)
        if style_prompt:
            prompt = f"{prompt.rstrip()}\n\n{style_prompt}" if prompt else style_prompt
        legacy_style = derive_legacy_image_style(resolved_style_spec)
        return ImageToImageStyleState(
            prompt=prompt,
            legacy_style=legacy_style,
            resolved_style_spec=resolved_style_spec,
            resolution_meta=resolution_meta,
        )
    except Exception as exc:  # pragma: no cover - defensive parity
        return ImageToImageStyleState(
            prompt=prompt,
            legacy_style=legacy_style,
            resolution_meta={"error": str(exc)},
        )


def attach_style_metadata(
    response: AIResponse,
    resolved_style_spec: Any | None,
    resolution_meta: dict[str, Any] | None,
) -> None:
    if resolved_style_spec is None:
        return
    meta = dict(response.metadata or {})
    meta["style_spec"] = resolved_style_spec.model_dump(
        mode="json",
        exclude_none=True,
    )
    if resolution_meta:
        meta["style_spec_resolution"] = resolution_meta
    response.metadata = meta
