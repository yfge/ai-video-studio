"""
MiniMax service provider.

Supports text generation, text-to-speech, and video generation.

API documentation:
- POST /v1/video_generation (create task)
- GET /v1/query/video_generation (query status)
- GET /v1/files/retrieve (get video file)
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

from app.services.minimax_client import MinimaxClient

from ..base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from . import text as text_module
from . import tts as tts_module
from . import video as video_module
from . import video_tasks as video_tasks_module
from .models import get_available_models


class MinimaxProvider(BaseProvider):
    """MiniMax service provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = MinimaxClient(
            api_key=config.api_key or "",
            group_id=config.group_id,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self.base_url = self.client.base_url
        self.group_id = config.group_id

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_SPEECH,
            AIModelType.IMAGE_TO_VIDEO,
            AIModelType.TEXT_TO_VIDEO,
        ]

    @property
    def available_models(self) -> List[ModelInfo]:
        return get_available_models()

    async def _initialize_client(self):
        """Initialize HTTP client."""
        await self.get_client()

    async def get_client(self):
        client = await self.client.get_client()
        try:
            self._loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            self._loop_id = None
        self._client = client
        return client

    async def generate_text(
        self,
        prompt: str,
        model: str = "abab6.5-chat",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str = None,
        **kwargs,
    ) -> AIResponse:
        """Generate text using MiniMax."""
        return await text_module.generate_text(
            client=self.client,
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
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """MiniMax does not support image generation."""
        return AIResponse(
            success=False,
            error="MiniMax暂不支持图像生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def text_to_speech(
        self,
        text: str,
        model: str = "speech-2.6-hd",
        voice_id: str = "Chinese (Mandarin)_Lyrical_Voice",
        speed: float = 1.0,
        pitch: float = 0.0,
        emotion: Optional[str] = None,
        format: str = "mp3",
        output_format: str = "url",
        stream: bool = False,
        **kwargs,
    ) -> AIResponse:
        """MiniMax text-to-speech."""
        return await tts_module.text_to_speech(
            client=self.client,
            provider_name=self.name,
            text=text,
            model=model,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch,
            emotion=emotion,
            format=format,
            output_format=output_format,
            stream=stream,
            format_error=self.format_error,
            **kwargs,
        )

    async def get_voices(self) -> AIResponse:
        """Get available voice list."""
        return await tts_module.get_voices(
            client=self.client,
            provider_name=self.name,
            format_error=self.format_error,
        )

    async def generate_video(
        self,
        first_frame_image: Optional[str] = None,
        prompt: Optional[str] = None,
        last_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-2.3",
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        fast_pretreatment: bool = False,
        aigc_watermark: bool = False,
        # Unified ai_manager pipeline aliases (generate_video passes image_url/
        # end_image_url); keep the MiniMax-native names as the primary API.
        image_url: Optional[str] = None,
        end_image_url: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate video from image(s) using MiniMax video generation API."""
        first_frame_image = first_frame_image or image_url
        last_frame_image = last_frame_image or end_image_url
        if not first_frame_image:
            return AIResponse(
                success=False,
                error="MiniMax video generation requires a first frame image",
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )
        kwargs.pop("fps", None)
        return await video_module.generate_video(
            client=self.client,
            provider_name=self.name,
            first_frame_image=first_frame_image,
            prompt=prompt,
            last_frame_image=last_frame_image,
            model=model,
            duration=duration,
            resolution=resolution,
            prompt_optimizer=prompt_optimizer,
            fast_pretreatment=fast_pretreatment,
            aigc_watermark=aigc_watermark,
            format_error=self.format_error,
            **kwargs,
        )

    async def submit_video_task(
        self,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        end_image_url: Optional[str] = None,
        first_frame_image: Optional[str] = None,
        last_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-2.3",
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        fast_pretreatment: bool = False,
        aigc_watermark: bool = False,
        **kwargs,
    ) -> AIResponse:
        """Submit async video generation task to MiniMax."""
        primary_image = first_frame_image or image_url
        tail_image = last_frame_image or end_image_url
        if not primary_image:
            return AIResponse(
                success=False,
                error="first_frame_image is required for MiniMax video",
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )
        return await video_tasks_module.submit_video_task(
            client=self.client,
            provider_name=self.name,
            first_frame_image=primary_image,
            prompt=prompt,
            last_frame_image=tail_image,
            model=model,
            duration=duration,
            resolution=resolution,
            prompt_optimizer=prompt_optimizer,
            fast_pretreatment=fast_pretreatment,
            aigc_watermark=aigc_watermark,
            format_error=self.format_error,
            **kwargs,
        )

    async def fetch_video_task_status(self, task_id: str) -> AIResponse:
        """Fetch async video task status from MiniMax."""
        return await video_tasks_module.fetch_video_task_status(
            client=self.client,
            provider_name=self.name,
            task_id=task_id,
            format_error=self.format_error,
        )
