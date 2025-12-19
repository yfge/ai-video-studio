"""
Volcengine (火山引擎) service provider.

Supports text generation, image generation, video generation, and TTS.
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
from . import tts as tts_module
from . import video as video_module


class VolcengineProvider(BaseProvider):
    """Volcengine service provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self.region = config.region if hasattr(config, "region") else "cn-beijing"

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
            AIModelType.IMAGE_TO_VIDEO,
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.TEXT_TO_SPEECH,
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
        Call Volcengine Ark /models endpoint, filter with local whitelist,
        fallback to static list on failure.
        """
        fallback = self._fallback_models(model_type)
        client = await self.get_client()
        if client is None:
            return fallback

        try:
            resp = await client.get(f"{self.base_url}/models")
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("data") or payload.get("models") or payload
            models: List[ModelInfo] = []
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                mid = item.get("id") or item.get("model") or item.get("model_id")
                if not mid:
                    continue
                mtype = infer_model_type(mid, item)
                if mtype not in self.supported_model_types:
                    continue
                if model_type and mtype != model_type:
                    continue
                models.append(
                    ModelInfo(
                        model_id=mid,
                        name=item.get("name") or item.get("model_name") or mid,
                        description=item.get("description")
                        or item.get("desc")
                        or f"Volcengine model {mid}",
                        model_type=mtype,
                        capabilities=infer_capabilities(mtype, item),
                    )
                )
            return models or fallback
        except Exception:
            return fallback

    async def _initialize_client(self):
        """Initialize HTTP client."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        if self.region:
            headers["X-Region"] = self.region

        self._client = httpx.AsyncClient(timeout=self.config.timeout, headers=headers)

    async def generate_text(
        self,
        prompt: str,
        model: str = "doubao-pro-4k",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate text using Doubao models."""
        client = await self.get_client()
        return await text_module.generate_text(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            system_prompt=system_prompt,
            format_error=self.format_error,
            **kwargs,
        )

    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        style: Optional[str] = None,
        style_preset_id: Optional[str] = None,
        style_spec: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate images using Seedream API (text-to-image)."""
        client = await self.get_client()
        return await image_module.generate_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            format_error=self.format_error,
            initialize_client=self._initialize_client,
            **kwargs,
        )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str,
        model: Optional[str] = None,
        count: int = 1,
        size: Optional[str] = None,
        style: Optional[str] = None,
        style_preset_id: Optional[str] = None,
        style_spec: Optional[str] = None,
        extra_images: Optional[List[str]] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate image variants using Seedream API (image-to-image)."""
        client = await self.get_client()
        return await image_module.image_to_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            image_url=image_url,
            prompt=prompt,
            model=model,
            count=count,
            size=size,
            style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            extra_images=extra_images,
            format_error=self.format_error,
            initialize_client=self._initialize_client,
            **kwargs,
        )

    async def generate_video(
        self,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        model: Optional[str] = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "720p",
        end_image_url: Optional[str] = None,
        ratio: Optional[str] = None,
        watermark: Optional[bool] = None,
        seed: Optional[int] = None,
        camera_fixed: Optional[bool] = None,
        service_tier: Optional[str] = None,
        execution_expires_after: Optional[int] = None,
        return_last_frame: Optional[bool] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate video using Volcengine Ark Video Generation API (Seedance)."""
        client = await self.get_client()
        return await video_module.generate_video(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            prompt=prompt,
            image_url=image_url,
            model=model,
            duration=duration,
            fps=fps,
            resolution=resolution,
            end_image_url=end_image_url,
            ratio=ratio,
            watermark=watermark,
            seed=seed,
            camera_fixed=camera_fixed,
            service_tier=service_tier,
            execution_expires_after=execution_expires_after,
            return_last_frame=return_last_frame,
            format_error=self.format_error,
            **kwargs,
        )

    async def text_to_speech(
        self,
        text: str,
        model: str = "volcengine-tts-v1",
        voice_type: str = "BV001_streaming",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "neutral",
        format: str = "mp3",
        **kwargs,
    ) -> AIResponse:
        """Generate speech from text using Volcengine TTS."""
        client = await self.get_client()
        return await tts_module.text_to_speech(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            text=text,
            model=model,
            voice_type=voice_type,
            speed=speed,
            volume=volume,
            pitch=pitch,
            emotion=emotion,
            format=format,
            format_error=self.format_error,
            **kwargs,
        )

    async def get_voice_types(self) -> AIResponse:
        """Get available voice types."""
        return tts_module.get_voice_types(self.name)
