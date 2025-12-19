"""
OpenAI service provider.

Supports GPT text generation and DALL-E image generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from ..base import (
    AIModelType,
    AIResponse,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from .models import (
    fallback_models,
    get_available_models,
    infer_capabilities,
    infer_model_type,
)
from . import image as image_module
from . import text as text_module


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
                models.append(
                    ModelInfo(
                        model_id=mid,
                        name=item.get("name") or mid,
                        description=item.get("description") or f"OpenAI model {mid}",
                        model_type=mtype,
                        capabilities=infer_capabilities(mid),
                    )
                )
            return models or fallback
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
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
        **kwargs,
    ) -> AIResponse:
        """Generate images using DALL-E."""
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
        model: str = "dall-e-2",
        size: str = "1024x1024",
        n: int = 1,
        **kwargs,
    ) -> AIResponse:
        """DALL-E image variation (DALL-E 2 only)."""
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
