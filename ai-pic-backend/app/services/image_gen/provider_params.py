from __future__ import annotations

from typing import Any, Dict

from app.services.providers.image_param_utils import size_to_dimensions
from app.utils.model_utils import normalize_openai_image_style

from .types import ImageGenMode, ImageGenNormalized

FALLBACK_TEXT_TO_IMAGE_KEYS: set[str] = {
    "prompt",
    "model",
    "prefer_provider",
    "n",
    "size",
    "aspect_ratio",
    "style",
}

FALLBACK_IMAGE_TO_IMAGE_KEYS: set[str] = {
    "image_url",
    "prompt",
    "model",
    "prefer_provider",
    "count",
    "size",
    "extra_images",
}

TEXT_TO_IMAGE_KEYS_BY_PROVIDER: dict[str, set[str]] = {
    "openai": {"prompt", "model", "prefer_provider", "n", "size", "style"},
    "jimeng": {
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
    },
    "keling": {
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
    },
    "volcengine": {
        "prompt",
        "model",
        "prefer_provider",
        "n",
        "size",
        "style",
        "style_preset_id",
        "style_spec",
        "cfg_scale",
        "watermark",
        "reference_images",
    },
    "google": {
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
    },
}

IMAGE_TO_IMAGE_KEYS_BY_PROVIDER: dict[str, set[str]] = {
    "openai": {"image_url", "prompt", "model", "prefer_provider", "count", "size"},
    "jimeng": {
        "image_url",
        "prompt",
        "model",
        "prefer_provider",
        "strength",
        "steps",
        "cfg_scale",
        "seed",
    },
    "keling": {
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
        "image_reference",
        "image_fidelity",
        "human_fidelity",
    },
    "volcengine": {
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
        "cfg_scale",
        "watermark",
    },
    "google": {
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
    },
}


def supported_ai_manager_keys(provider: str, mode: ImageGenMode) -> set[str]:
    """Return supported AIServiceManager kwargs for a provider+mode."""
    provider_key = (provider or "").lower()
    if mode == ImageGenMode.TEXT_TO_IMAGE:
        return set(
            TEXT_TO_IMAGE_KEYS_BY_PROVIDER.get(
                provider_key, FALLBACK_TEXT_TO_IMAGE_KEYS
            )
        )
    return set(
        IMAGE_TO_IMAGE_KEYS_BY_PROVIDER.get(provider_key, FALLBACK_IMAGE_TO_IMAGE_KEYS)
    )


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
        "negative_prompt": normalized.negative_prompt,
    }

    if normalized.mode == ImageGenMode.TEXT_TO_IMAGE:
        payload: Dict[str, Any] = {
            **common,
            "n": normalized.count,
            "width": normalized.width,
            "height": normalized.height,
            "size": normalized.size,
            "aspect_ratio": normalized.aspect_ratio,
            "reference_images": list(normalized.extra_images or []),
            "image_reference": normalized.image_reference,
            "image_fidelity": normalized.image_fidelity,
            "human_fidelity": normalized.human_fidelity,
            "seed": normalized.seed,
            "steps": normalized.steps,
            "cfg_scale": normalized.cfg_scale,
        }
        return _filter_text_to_image(provider, payload)

    payload = {
        **common,
        "image_url": normalized.base_image_url,
        "count": normalized.count,
        "size": normalized.size,
        "aspect_ratio": normalized.aspect_ratio,
        "extra_images": list(normalized.extra_images or []),
        "image_reference": normalized.image_reference,
        "image_fidelity": normalized.image_fidelity,
        "human_fidelity": normalized.human_fidelity,
        "seed": normalized.seed,
        "steps": normalized.steps,
        "cfg_scale": normalized.cfg_scale,
        "strength": normalized.strength,
    }
    return _filter_image_to_image(provider, payload)


def _filter_text_to_image(provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if provider == "openai":
        payload["style"] = normalize_openai_image_style(payload.get("style"))
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.TEXT_TO_IMAGE)
        )

    if provider == "jimeng":
        dims = size_to_dimensions(payload.get("size") or "")
        if dims:
            payload["width"], payload["height"] = dims
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.TEXT_TO_IMAGE)
        )

    if provider == "keling":
        refs = payload.get("reference_images")
        if refs and not payload.get("image"):
            first = None
            if isinstance(refs, list):
                first = refs[0] if refs else None
            elif isinstance(refs, str):
                first = refs
            if isinstance(first, str) and first:
                payload["image"] = first
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.TEXT_TO_IMAGE)
        )

    if provider == "volcengine":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.TEXT_TO_IMAGE)
        )

    if provider == "google":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.TEXT_TO_IMAGE)
        )

    # Fallback: keep safe common subset
    return _keep(payload, FALLBACK_TEXT_TO_IMAGE_KEYS)


def _filter_image_to_image(provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if provider == "openai":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.IMAGE_TO_IMAGE)
        )

    if provider == "jimeng":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.IMAGE_TO_IMAGE)
        )

    if provider == "keling":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.IMAGE_TO_IMAGE)
        )

    if provider == "volcengine":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.IMAGE_TO_IMAGE)
        )

    if provider == "google":
        return _keep(
            payload, supported_ai_manager_keys(provider, ImageGenMode.IMAGE_TO_IMAGE)
        )

    return _keep(payload, FALLBACK_IMAGE_TO_IMAGE_KEYS)


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
