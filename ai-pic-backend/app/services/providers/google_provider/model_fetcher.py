"""Google model listing helpers.

This module keeps GoogleProvider itself smaller and focuses on listing models
from the Generative Language API with a safe static fallback.
"""

from __future__ import annotations

from typing import Any, List, Optional

from ..base import AIModelType, ModelInfo
from ..image_param_utils import compute_image_ui as compute_image_ui_rules
from .models import dedupe, from_payload


async def fetch_remote_models(
    *,
    client: Any,
    base_url: str,
    api_key: Optional[str],
    provider_name: str,
    model_type: Optional[AIModelType],
    supported_model_types: List[AIModelType],
    fallback: List[ModelInfo],
    logger: Any,
) -> List[ModelInfo]:
    """Fetch models from Google's Generative Language API, fallback to static list."""
    if not api_key or client is None:
        return fallback

    google_base = base_url or "https://generativelanguage.googleapis.com"
    try:
        resp = await client.get(
            f"{google_base.rstrip('/')}/v1beta/models",
            params={"key": api_key},
        )
        body_preview = resp.text[:500]
        if resp.status_code >= 400:
            logger.debug(
                "GoogleProvider GLM list models failed status=%s url=%s body=%s",
                resp.status_code,
                f"{google_base.rstrip('/')}/v1beta/models",
                body_preview,
            )
            return fallback

        payload = resp.json()
        server_models = payload.get("models") or []
        models = from_payload(server_models, model_type, supported_model_types)
        for model in models:
            if model.model_type not in (
                AIModelType.TEXT_TO_IMAGE,
                AIModelType.IMAGE_TO_IMAGE,
            ):
                continue
            if model.metadata:
                continue
            rules = compute_image_ui_rules(provider_name, model.model_id)
            if not (rules.size_options or rules.supports_aspect_ratio):
                continue
            supports_reference_image = (
                "image_to_image" in (model.capabilities or [])
                or model.model_type == AIModelType.IMAGE_TO_IMAGE
            )
            ui_meta = {
                "size_options": rules.size_options,
                "aspect_ratio_options": rules.aspect_ratio_options,
                "supports_aspect_ratio": rules.supports_aspect_ratio,
                "default_size": rules.default_size,
                "default_aspect_ratio": rules.default_aspect_ratio,
                "supports_reference_image": supports_reference_image,
            }
            model.metadata = {
                "ui": {
                    key: value for key, value in ui_meta.items() if value is not None
                }
            }

        return dedupe(models) or fallback
    except Exception as exc:  # noqa: BLE001
        logger.debug("GoogleProvider list models exception: %s", exc)
        return fallback
