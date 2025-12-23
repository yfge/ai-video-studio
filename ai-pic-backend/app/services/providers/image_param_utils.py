"""
Shared image parameter normalization for providers.

Keeps size/aspect-ratio rules consistent across providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

DEFAULT_ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4"]


@dataclass(frozen=True)
class ImageUiRules:
    size_options: List[str]
    aspect_ratio_options: List[str]
    supports_aspect_ratio: bool
    default_size: Optional[str]
    default_aspect_ratio: Optional[str]


def compute_image_ui(provider: str, model_id: str) -> ImageUiRules:
    provider_key = (provider or "").lower()
    mid = (model_id or "").lower()
    size_options: List[str] = []
    supports_aspect_ratio = False

    if provider_key == "openai":
        if "dall-e-3" in mid:
            size_options = ["1024x1024", "1024x1792", "1792x1024"]
        elif "dall-e-2" in mid:
            size_options = ["256x256", "512x512", "1024x1024"]
    elif provider_key == "volcengine" and "seedream" in mid:
        size_options = ["2K"]
    elif provider_key == "keling" and "kling-image" in mid:
        size_options = ["2k", "1k"]
        supports_aspect_ratio = True
    elif provider_key == "google":
        supports_aspect_ratio = True
    elif provider_key == "jimeng":
        size_options = ["1024x1024"]

    aspect_ratio_options = (
        DEFAULT_ASPECT_RATIOS if supports_aspect_ratio else []
    )

    return ImageUiRules(
        size_options=size_options,
        aspect_ratio_options=aspect_ratio_options,
        supports_aspect_ratio=supports_aspect_ratio,
        default_size=size_options[0] if size_options else None,
        default_aspect_ratio=aspect_ratio_options[0] if aspect_ratio_options else None,
    )


def size_to_dimensions(size: str) -> Optional[Tuple[int, int]]:
    if not size:
        return None
    raw = str(size).strip().lower()
    if not raw:
        return None
    if "x" in raw:
        parts = raw.split("x", 1)
        try:
            width = int(parts[0])
            height = int(parts[1])
        except (TypeError, ValueError):
            return None
        if width > 0 and height > 0:
            return width, height
        return None
    if raw.endswith("k") and raw[:-1].isdigit():
        side = int(raw[:-1]) * 1024
        return side, side
    if raw.isdigit():
        side = int(raw)
        if side > 0:
            return side, side
    return None


def normalize_image_params(
    provider: str,
    model_id: str,
    size: Optional[str],
    aspect_ratio: Optional[str],
    *,
    strict: bool = True,
) -> Tuple[Optional[str], Optional[str], ImageUiRules]:
    rules = compute_image_ui(provider, model_id)
    normalized_size = _normalize_size(size, rules, strict)
    if normalized_size is None and rules.size_options:
        normalized_size = rules.default_size
    normalized_ratio = _normalize_aspect_ratio(aspect_ratio, rules, strict)
    return normalized_size, normalized_ratio, rules


def normalize_keling_resolution(size: Optional[str]) -> Optional[str]:
    if not size:
        return None
    raw = str(size).strip().lower()
    if raw in {"1k", "2k"}:
        return raw
    dims = size_to_dimensions(raw)
    if not dims:
        return None
    max_side = max(dims)
    if max_side >= 2048:
        return "2k"
    if max_side >= 1024:
        return "1k"
    return None


def _normalize_size(
    size: Optional[str],
    rules: ImageUiRules,
    strict: bool,
) -> Optional[str]:
    if not size:
        return None
    if not rules.size_options:
        return str(size).strip()
    matched = _match_option(size, rules.size_options, allow_dimensions=True)
    if matched:
        return matched
    if strict:
        raise ValueError(
            f"unsupported size '{size}', allowed: {', '.join(rules.size_options)}"
        )
    return None


def _normalize_aspect_ratio(
    aspect_ratio: Optional[str],
    rules: ImageUiRules,
    strict: bool,
) -> Optional[str]:
    if not aspect_ratio:
        return None
    if not rules.supports_aspect_ratio:
        if strict:
            raise ValueError("aspect ratio is not supported for this model")
        return None
    matched = _match_option(aspect_ratio, rules.aspect_ratio_options)
    if matched:
        return matched
    if strict:
        raise ValueError(
            "unsupported aspect ratio "
            f"'{aspect_ratio}', allowed: {', '.join(rules.aspect_ratio_options)}"
        )
    return None


def _match_option(
    value: str,
    options: List[str],
    *,
    allow_dimensions: bool = False,
) -> Optional[str]:
    raw = str(value).strip().lower()
    for option in options:
        if raw == option.strip().lower():
            return option
    if allow_dimensions:
        value_dims = size_to_dimensions(raw)
        if value_dims:
            for option in options:
                option_dims = size_to_dimensions(option)
                if option_dims and option_dims == value_dims:
                    return option
    return None
