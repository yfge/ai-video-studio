"""Keling (可灵) service provider.

JWT authentication (HS256) + image/video generation endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from ...keling_auth import KelingAuthManager
from ..base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from . import image as image_module
from . import video as video_module
from . import video_tasks as video_tasks_module
from .models import get_available_models


class KelingProvider(BaseProvider):
    """Keling service provider - Updated with JWT authentication"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        def _normalize_base_url(raw: Optional[str]) -> str:
            """Strip trailing version segments to avoid double /v1 when building URLs."""
            base = (raw or "https://api-beijing.klingai.com").strip()
            base = base.rstrip("/")
            if base.endswith("/v1"):
                base = base[: -len("/v1")]
            return base

        # Validate required credentials
        if not config.api_key:
            raise ValueError("Keling Provider requires api_key (AccessKey)")
        if not config.api_secret:
            raise ValueError("Keling Provider requires api_secret (SecretKey)")

        # New official base URL
        self.base_url = _normalize_base_url(config.base_url)

        # Initialize JWT authentication manager
        self.auth_manager = KelingAuthManager(
            access_key=config.api_key,
            secret_key=config.api_secret,
            token_ttl=1800,  # 30 minutes
            refresh_buffer=300,  # Refresh 5 minutes before expiry
        )

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.IMAGE_TO_VIDEO,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
        ]

    @property
    def available_models(self) -> List[ModelInfo]:
        return get_available_models()

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with JWT token"""
        auth_header = self.auth_manager.get_auth_header()
        return {
            **auth_header,
            "Content-Type": "application/json",
            "User-Agent": "ai-video-studio/2.0",
        }

    async def _initialize_client(self):
        """Initialize HTTP client with JWT authentication"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0),  # Video generation requires longer timeout
            headers=self._get_auth_headers(),
        )

    async def generate_text(
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """Keling does not support text generation"""
        return AIResponse(
            success=False,
            error="可灵不支持纯文本生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    async def generate_image(
        self,
        prompt: str,
        model: str = "kling-v2-1",
        negative_prompt: Optional[str] = None,
        image: Optional[str] = None,
        image_reference: Optional[str] = None,
        image_fidelity: Optional[float] = None,
        human_fidelity: Optional[float] = None,
        resolution: str = "1k",
        n: int = 1,
        aspect_ratio: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate images using Keling AI."""
        client = await self.get_client()
        return await image_module.generate_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            prompt=prompt,
            model=model,
            negative_prompt=negative_prompt,
            image=image,
            image_reference=image_reference,
            image_fidelity=image_fidelity,
            human_fidelity=human_fidelity,
            resolution=resolution,
            n=n,
            aspect_ratio=aspect_ratio,
            format_error=self.format_error,
            **kwargs,
        )

    async def image_to_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        model: str = "kling-v2-1",
        n: int = 1,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate image variants using Keling AI (image-to-image)."""
        client = await self.get_client()
        return await image_module.image_to_image(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            image_url=image_url,
            prompt=prompt,
            model=model,
            negative_prompt=negative_prompt,
            resolution=size or "1k",
            n=n,
            aspect_ratio=aspect_ratio,
            format_error=self.format_error,
            **kwargs,
        )

    async def generate_video(
        self,
        prompt: Optional[str] = None,
        image: Optional[str] = None,
        image_url: Optional[str] = None,
        image_tail: Optional[str] = None,
        end_image_url: Optional[str] = None,
        model: str = "kling-v2-1",
        mode: str = "pro",
        duration: int = 5,
        resolution: Optional[str] = None,
        ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        cfg_scale: Optional[float] = None,
        camera_control: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate video from image using Keling AI."""
        client = await self.get_client()
        return await video_module.generate_video(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            prompt=prompt,
            image=image,
            image_url=image_url,
            image_tail=image_tail,
            end_image_url=end_image_url,
            model=model,
            mode=mode,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            negative_prompt=negative_prompt,
            cfg_scale=cfg_scale,
            camera_control=camera_control,
            format_error=self.format_error,
            **kwargs,
        )

    async def submit_video_task(
        self,
        prompt: Optional[str] = None,
        image: Optional[str] = None,
        image_url: Optional[str] = None,
        image_tail: Optional[str] = None,
        end_image_url: Optional[str] = None,
        model: str = "kling-v2-1",
        mode: str = "pro",
        duration: int = 5,
        resolution: Optional[str] = None,
        ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        cfg_scale: Optional[float] = None,
        camera_control: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AIResponse:
        """Submit async video generation task to Keling."""
        client = await self.get_client()
        return await video_tasks_module.submit_video_task(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            prompt=prompt,
            image=image,
            image_url=image_url,
            image_tail=image_tail,
            end_image_url=end_image_url,
            model=model,
            mode=mode,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            negative_prompt=negative_prompt,
            cfg_scale=cfg_scale,
            camera_control=camera_control,
            format_error=self.format_error,
            **kwargs,
        )

    async def fetch_video_task_status(self, task_id: str) -> AIResponse:
        """Fetch async video task status from Keling."""
        client = await self.get_client()
        return await video_tasks_module.fetch_video_task_status(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            task_id=task_id,
            format_error=self.format_error,
        )

    async def generate_video_from_multiple_images(
        self,
        image_list: List[str],
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        mode: str = "pro",
        duration: int = 5,
        aspect_ratio: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate video from multiple images (kling-v1-6 only)."""
        client = await self.get_client()
        return await video_module.generate_video_from_multiple_images(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            image_list=image_list,
            prompt=prompt,
            negative_prompt=negative_prompt,
            mode=mode,
            duration=duration,
            aspect_ratio=aspect_ratio,
            format_error=self.format_error,
            **kwargs,
        )

    async def get_task_status(
        self, task_id: str, task_type: str = "video"
    ) -> AIResponse:
        """Get task status for a given task ID."""
        client = await self.get_client()
        return await video_module.get_task_status(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            get_auth_headers=self._get_auth_headers,
            task_id=task_id,
            task_type=task_type,
            format_error=self.format_error,
        )
