"""Google AI / Gemini provider for text/image and Veo video generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from app.core.logging import get_logger

from ..base import AIModelType, AIResponse, BaseProvider, ModelInfo, ProviderConfig
from . import image_routing as image_routing_module
from . import text as text_module
from . import video as video_module
from . import video_tasks as video_tasks_module
from .model_fetcher import fetch_remote_models as fetch_google_remote_models
from .models import fallback_models, get_available_models
from .vertex_auth import build_vertex_access_token_provider

logger = get_logger(__name__)


class GoogleProvider(BaseProvider):
    """Google Gemini text and image generation provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = (
            config.base_url or "https://generativelanguage.googleapis.com"
        ).rstrip("/")
        self.video_base_url = (config.video_base_url or self.base_url).rstrip("/")
        self.default_model = config.default_model or "gemini-3-pro-preview"
        self.vertex_project_id = config.vertex_project_id
        self.vertex_location = config.vertex_location
        self.vertex_access_token = config.vertex_access_token
        self.vertex_api_key = config.vertex_api_key
        self._vertex_token_provider = build_vertex_access_token_provider(
            service_account_json=config.vertex_service_account_json,
            service_account_path=config.vertex_service_account_path,
            logger=logger,
        )

    def _should_use_vertex(self) -> bool:
        return bool(self.vertex_project_id and self.vertex_location)

    async def _get_vertex_access_token(self) -> Optional[str]:
        if self.vertex_access_token:
            return self.vertex_access_token
        if not self._should_use_vertex():
            return None
        if not self._vertex_token_provider:
            return None
        return await self._vertex_token_provider.get_token()

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.IMAGE_TO_VIDEO,
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
        fallback = self._fallback_models(model_type)
        client = await self.get_client()
        return await fetch_google_remote_models(
            client=client,
            base_url=self.base_url,
            api_key=self.config.api_key,
            provider_name=self.name,
            model_type=model_type,
            supported_model_types=self.supported_model_types,
            fallback=fallback,
            logger=logger,
        )

    async def _initialize_client(self):
        """Initialize HTTP client."""
        has_vertex_auth = bool(
            self.vertex_access_token
            or self.vertex_api_key
            or self._vertex_token_provider
        )
        if not self.config.api_key and not has_vertex_auth:
            self._client = None  # type: ignore[assignment]
            return

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-client": "ai-video-studio-gemini",
        }
        if self.config.api_key:
            headers["x-goog-api-key"] = self.config.api_key
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
        """Generate images (text-to-image). Prefer Vertex AI when configured."""
        client = await self.get_client()
        access_token = await self._get_vertex_access_token()
        return await image_routing_module.generate_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            prompt=prompt,
            model=model,
            vertex_project_id=self.vertex_project_id,
            vertex_location=self.vertex_location,
            access_token=access_token,
            vertex_api_key=self.vertex_api_key,
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
        """Generate images (image-to-image). Prefer Vertex AI when configured."""
        client = await self.get_client()
        access_token = await self._get_vertex_access_token()
        return await image_routing_module.image_to_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            image_url=image_url,
            prompt=prompt,
            model=model,
            vertex_project_id=self.vertex_project_id,
            vertex_location=self.vertex_location,
            access_token=access_token,
            vertex_api_key=self.vertex_api_key,
            format_error=self.format_error,
            **kwargs,
        )

    async def generate_video(
        self,
        prompt: str = None,
        image_url: str = None,
        model: str = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Generate videos using Veo (text-to-video / image-to-video)."""
        client = await self.get_client()
        access_token = await self._get_vertex_access_token()
        return await video_module.generate_video(
            client=client,
            base_url=self.video_base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            prompt=prompt,
            image_url=image_url,
            model=model,
            vertex_project_id=self.vertex_project_id,
            vertex_location=self.vertex_location,
            access_token=access_token,
            vertex_api_key=self.vertex_api_key,
            format_error=self.format_error,
            **kwargs,
        )

    async def submit_video_task(
        self,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        end_image_url: Optional[str] = None,
        model: Optional[str] = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "720p",
        ratio: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """Submit async Veo task and return a provider task_id for polling."""
        client = await self.get_client()
        access_token = await self._get_vertex_access_token()
        return await video_tasks_module.submit_video_task(
            client=client,
            base_url=self.video_base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            config_timeout=self.config.timeout,
            prompt=prompt,
            image_url=image_url,
            end_image_url=end_image_url,
            model=model,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            vertex_project_id=self.vertex_project_id,
            vertex_location=self.vertex_location,
            access_token=access_token,
            vertex_api_key=self.vertex_api_key,
            format_error=self.format_error,
            **kwargs,
        )

    async def fetch_video_task_status(self, task_id: str) -> AIResponse:
        """Fetch async video task status from Google Veo."""
        client = await self.get_client()
        access_token = await self._get_vertex_access_token()
        return await video_tasks_module.fetch_video_task_status(
            client=client,
            base_url=self.video_base_url,
            provider_name=self.name,
            api_key=self.config.api_key,
            task_id=task_id,
            access_token=access_token,
            vertex_api_key=self.vertex_api_key,
            format_error=self.format_error,
        )
