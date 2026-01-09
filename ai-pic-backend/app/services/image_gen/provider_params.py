from __future__ import annotations

from typing import Any, Dict

from app.services.providers.image_param_utils import size_to_dimensions
from app.utils.model_utils import normalize_openai_image_style

from .types import ImageGenMode, ImageGenNormalized


def build_ai_manager_call(normalized: ImageGenNormalized) -> Dict[str, Any]:
    """Build an AIServiceManager call dict with provider-safe kwargs.

    This does not execute the call; it only standardizes parameters and filters
    unsafe kwargs. The return payload can be used as:
    - ai_manager.generate_image(**payload) for text-to-image
    - ai_manager.image_to_image(**payload) for image-to-image
    """
    provider = (normalized.provider or "").lower()
    model_id = normalized.model_id

    common: Dict[str, Any] = {
        "prompt": normalized.prompt,
        "model": model_id,
        "prefer_provider": normalized.provider,
        "style": normalized.style,
        "style_preset_id": normalized.style_preset_id,
        "style_spec": normalized.style_spec,
    }

    if normalized.mode == ImageGenMode.TEXT_TO_IMAGE:
        payload: Dict[str, Any] = {
            **common,
            "n": normalized.count,
            "width": normalized.width,
            "height": normalized.height,
            "size": normalized.size,
            "aspect_ratio": normalized.aspect_ratio,
        }
        return _filter_text_to_image(provider, payload)

    payload = {
        **common,
        "image_url": normalized.base_image_url,
        "count": normalized.count,
        "size": normalized.size,
        "aspect_ratio": normalized.aspect_ratio,
        "extra_images": list(normalized.extra_images or []),
    }
    return _filter_image_to_image(provider, payload)


def _filter_text_to_image(provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if provider == "openai":
        payload["style"] = normalize_openai_image_style(payload.get("style"))
        return _keep(
            payload, {"prompt", "model", "prefer_provider", "n", "size", "style"}
        )

    if provider == "jimeng":
        dims = size_to_dimensions(payload.get("size") or "")
        if dims:
            payload["width"], payload["height"] = dims
        allowed = {
            "prompt",
            "model",
            "prefer_provider",
            "width",
            "height",
            "steps",
            "cfg_scale",
            "seed",
            "negative_prompt",
            "style",
        }
        return _keep(payload, allowed)

    if provider == "keling":
        allowed = {
            "prompt",
            "model",
            "prefer_provider",
            "n",
            "size",
            "aspect_ratio",
            "style",
            "style_preset_id",
            "style_spec",
            "negative_prompt",
            "image",
            "image_reference",
            "image_fidelity",
            "human_fidelity",
        }
        return _keep(payload, allowed)

    if provider == "volcengine":
        allowed = {
            "prompt",
            "model",
            "prefer_provider",
            "n",
            "size",
            "style",
            "style_preset_id",
            "style_spec",
            "watermark",
            "reference_images",
        }
        return _keep(payload, allowed)

    if provider == "google":
        allowed = {
            "prompt",
            "model",
            "prefer_provider",
            "aspect_ratio",
            "size",
            "reference_images",
            "extra_images",
            "base64_images",
            "response_modalities",
            "responseModalities",
            "image_size",
            "imageSize",
            "aspectRatio",
        }
        return _keep(payload, allowed)

    # Fallback: keep safe common subset
    return _keep(
        payload,
        {"prompt", "model", "prefer_provider", "n", "size", "aspect_ratio", "style"},
    )


def _filter_image_to_image(provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if provider == "openai":
        return _keep(
            payload,
            {"image_url", "prompt", "model", "prefer_provider", "count", "size"},
        )

    if provider == "jimeng":
        allowed = {
            "image_url",
            "prompt",
            "model",
            "prefer_provider",
            "strength",
            "steps",
            "cfg_scale",
            "seed",
        }
        return _keep(payload, allowed)

    if provider == "keling":
        allowed = {
            "image_url",
            "prompt",
            "model",
            "prefer_provider",
            "count",
            "size",
            "aspect_ratio",
            "style",
            "style_preset_id",
            "style_spec",
            "extra_images",
            "image_reference",
            "image_fidelity",
            "human_fidelity",
            "negative_prompt",
        }
        return _keep(payload, allowed)

    if provider == "volcengine":
        allowed = {
            "image_url",
            "prompt",
            "model",
            "prefer_provider",
            "count",
            "size",
            "style",
            "style_preset_id",
            "style_spec",
            "extra_images",
            "watermark",
        }
        return _keep(payload, allowed)

    if provider == "google":
        allowed = {
            "image_url",
            "prompt",
            "model",
            "prefer_provider",
            "aspect_ratio",
            "size",
            "reference_images",
            "extra_images",
            "base64_images",
            "response_modalities",
            "responseModalities",
            "image_size",
            "imageSize",
            "aspectRatio",
        }
        return _keep(payload, allowed)

    return _keep(
        payload,
        {
            "image_url",
            "prompt",
            "model",
            "prefer_provider",
            "count",
            "size",
            "extra_images",
        },
    )


def _keep(payload: Dict[str, Any], allowed_keys: set[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in allowed_keys:
        if key not in payload:
            continue
        value = payload.get(key)
        if value is None:
            continue
        out[key] = value
    return out
