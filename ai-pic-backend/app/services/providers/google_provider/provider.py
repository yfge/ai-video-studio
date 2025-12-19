"""
Google AI / Gemini service provider.

Supports Gemini text generation and image generation (text-to-image, image-to-image).

Documentation:
- Text generation: docs/api/google-text-api.md
- Image generation: https://ai.google.dev/gemini-api/docs/image-generation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import get_logger

from ..base import (
    AIModelType,
    AIResponse,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from .models import (
    dedupe,
    fallback_models,
    from_payload,
    get_available_models,
)
from . import image as image_module
from . import text as text_module

logger = get_logger(__name__)


class GoogleProvider(BaseProvider):
    """Google Gemini text and image generation provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Support custom base_url for proxy gateways
        self.base_url = (
            config.base_url or "https://generativelanguage.googleapis.com"
        ).rstrip("/")
        self.default_model = config.default_model or "gemini-3-pro-preview"

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
        ]

    @property
    def available_models(self) -> List[ModelInfo]:
        return get_available_models(self.default_model)

    def _fallback_models(self, model_type: Optional[AIModelType]) -> List[ModelInfo]:
        return fallback_models(self.available_models, model_type)

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """Fetch models from Google's Generative Language API, fallback to static list."""
        fallback = self._fallback_models(model_type)
        if not self.config.api_key:
            return fallback

        client = await self.get_client()
        if client is None:
            return fallback

        google_base = self.base_url or "https://generativelanguage.googleapis.com"
        try:
            resp = await client.get(
                f"{google_base.rstrip('/')}/v1beta/models",
                params={"key": self.config.api_key},
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
            models = from_payload(server_models, model_type, self.supported_model_types)
            return dedupe(models) or fallback
        except Exception as exc:
            logger.debug("GoogleProvider list models exception: %s", exc)
            return fallback

    async def _initialize_client(self):
        """Initialize HTTP client."""
        if not self.config.api_key:
            self._client = None  # type: ignore[assignment]
            return

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.config.api_key,
            "x-goog-api-client": "ai-video-studio-gemini",
        }
        self._client = httpx.AsyncClient(timeout=self.config.timeout, headers=headers)

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: str | None = None,
        json_schema: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate text using Gemini models."""
        client = await self.get_client()
        return await text_module.generate_text(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            default_model=self.default_model,
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            json_schema=json_schema,
            format_error=self.format_error,
            **kwargs,
        )

    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate images using Gemini (text-to-image)."""
        client = await self.get_client()
        return await image_module.generate_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            prompt=prompt,
            model=model,
            format_error=self.format_error,
            **kwargs,
        )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str = None,
        model: str = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate images using Gemini (image-to-image with reference)."""
        client = await self.get_client()
        return await image_module.image_to_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            image_url=image_url,
            prompt=prompt,
            model=model,
            format_error=self.format_error,
            **kwargs,
        )
