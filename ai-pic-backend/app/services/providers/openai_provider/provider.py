"""
OpenAI service provider.

Supports GPT text generation and OpenAI image generation.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import httpx
from app.utils.model_utils import DEFAULT_OPENAI_IMAGE_MODEL

from ..base import AIModelType, AIResponse, BaseProvider, ModelInfo, ProviderConfig
from ..image_param_utils import compute_image_ui as compute_image_ui_rules
from . import image as image_module
from . import text as text_module
from .models import (
    fallback_models,
    get_available_models,
    infer_capabilities,
    infer_model_type,
)


class OpenAIProvider(BaseProvider):
    """OpenAI service provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Normalize base_url to avoid // paths
        self.base_url = (config.base_url or "https://api.openai.com/v1").rstrip("/")

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_UNDERSTANDING,
            AIModelType.IMAGE_TO_IMAGE,
        ]

    @property
    def available_models(self) -> List[ModelInfo]:
        return get_available_models()

    def _fallback_models(self, model_type: Optional[AIModelType]) -> List[ModelInfo]:
        return fallback_models(self.available_models, model_type)

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """
        Use OpenAI's official /v1/models endpoint as information source.

        Infer types from model IDs and return the latest list.
        """
        fallback = self._fallback_models(model_type)
        fallback_lookup = {model.model_id: model for model in fallback}
        try:
            client = await self.get_client()
            if client is None:
                return fallback
            resp = await client.get(f"{self.base_url}/models")
            resp.raise_for_status()
            data = resp.json()
            server_models = data.get("data", []) if isinstance(data, dict) else []
            models: List[ModelInfo] = []
            for item in server_models:
                if not isinstance(item, dict):
                    continue
                mid = item.get("id")
                if not mid:
                    continue
                mtype = infer_model_type(mid)
                if model_type and mtype != model_type:
                    continue
                caps = infer_capabilities(mid)
                metadata = {}
                fallback_model = fallback_lookup.get(mid)
                if fallback_model:
                    metadata = dict(getattr(fallback_model, "metadata", {}) or {})
                if not metadata and mtype in (
                    AIModelType.TEXT_TO_IMAGE,
                    AIModelType.IMAGE_TO_IMAGE,
                ):
                    rules = compute_image_ui_rules(self.name, mid)
                    if rules.size_options or rules.supports_aspect_ratio:
                        supports_reference_image = (
                            "image_to_image" in caps or "dall-e-2" in mid.lower()
                        )
                        ui_meta = {
                            "size_options": rules.size_options,
                            "aspect_ratio_options": rules.aspect_ratio_options,
                            "supports_aspect_ratio": rules.supports_aspect_ratio,
                            "default_size": rules.default_size,
                            "default_aspect_ratio": rules.default_aspect_ratio,
                            "supports_reference_image": supports_reference_image,
                        }
                        metadata = {
                            "ui": {
                                key: value
                                for key, value in ui_meta.items()
                                if value is not None
                            }
                        }
                models.append(
                    ModelInfo(
                        model_id=mid,
                        name=item.get("name") or mid,
                        description=item.get("description") or f"OpenAI model {mid}",
                        model_type=mtype,
                        capabilities=caps,
                        metadata=metadata,
                    )
                )
            if models:
                alias_models = [
                    model
                    for model in fallback
                    if (model.metadata or {}).get("alias_for")
                    and model.model_id not in {m.model_id for m in models}
                ]
                return [*models, *alias_models]
            return fallback
        except Exception:
            return fallback

    async def _initialize_client(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        json_schema: Optional[Dict] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate text using GPT models."""
        client = await self.get_client()
        return await text_module.generate_text(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
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
        model: str = DEFAULT_OPENAI_IMAGE_MODEL,
        size: str = "1024x1024",
        quality: str = "auto",
        style: str = "vivid",
        n: int = 1,
        **kwargs,
    ) -> AIResponse:
        """Generate images using OpenAI image models."""
        client = await self.get_client()
        return await image_module.generate_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            style=style,
            n=n,
            format_error=self.format_error,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            **kwargs,
        )

    async def understand_image(
        self,
        image_url: str,
        question: str = "请描述这张图片",
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AIResponse:
        """Understand image using GPT-4V."""
        client = await self.get_client()
        return await image_module.understand_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            image_url=image_url,
            question=question,
            model=model,
            max_tokens=max_tokens,
            format_error=self.format_error,
            **kwargs,
        )

    async def image_to_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        model: str = DEFAULT_OPENAI_IMAGE_MODEL,
        size: str = "1024x1024",
        n: int = 1,
        **kwargs,
    ) -> AIResponse:
        """Edit images using GPT Image, or create DALL-E 2 variations."""
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
            size=size,
            n=n,
            format_error=self.format_error,
            **kwargs,
        )
