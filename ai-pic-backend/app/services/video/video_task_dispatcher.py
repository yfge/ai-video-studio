from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.services.ai_service_manager import AIServiceManager
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_task_provider_resolver import resolve_provider_model


class VideoTaskDispatcher:
    def __init__(self, ai_manager: AIServiceManager):
        self.ai_manager = ai_manager
        self.logger = get_logger("video_task_dispatcher")

    async def submit_video_task(
        self,
        *,
        prompt: Optional[str],
        image_url: Optional[str],
        end_image_url: Optional[str],
        model: Optional[str],
        prefer_provider: Optional[str],
        duration: int,
        fps: int,
        resolution: str,
        **kwargs: Any,
    ) -> AIResponse:
        model_type = self._resolve_model_type(image_url)
        available, prefer_provider, model = self._resolve_candidates(
            model, prefer_provider, model_type
        )
        if not available:
            return self._build_failure_response(
                "没有可用的视频生成提供商", "ai_service_manager", model, model_type
            )
        self._log_submission(
            prompt, image_url, prefer_provider, model, duration, fps, resolution
        )
        return await self._submit_with_fallback(
            available,
            prefer_provider,
            prompt,
            image_url,
            end_image_url,
            model_type,
            model,
            duration,
            fps,
            resolution,
            **kwargs,
        )

    async def _submit_with_fallback(
        self,
        available: list[str],
        prefer_provider: Optional[str],
        prompt: Optional[str],
        image_url: Optional[str],
        end_image_url: Optional[str],
        model_type: AIModelType,
        model: Optional[str],
        duration: int,
        fps: int,
        resolution: str,
        **kwargs: Any,
    ) -> AIResponse:
        last_model_used = model
        for _ in range(self.ai_manager.config.max_retries):
            result = await self._submit_once(
                available,
                prefer_provider,
                prompt,
                image_url,
                end_image_url,
                model_type,
                model,
                duration,
                fps,
                resolution,
                **kwargs,
            )
            if not result:
                break
            response, provider_model, provider_name = result
            if provider_model:
                last_model_used = provider_model
            if response.success or not self.ai_manager.config.enable_fallback:
                return response
            if provider_name in available:
                available.remove(provider_name)
        return self._build_failure_response(
            "所有视频生成提供商都失败了", "ai_service_manager", last_model_used, model_type
        )

    def _resolve_model_type(self, image_url: Optional[str]) -> AIModelType:
        return AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO

    def _resolve_candidates(
        self,
        model: Optional[str],
        prefer_provider: Optional[str],
        model_type: AIModelType,
    ) -> tuple[list[str], Optional[str], Optional[str]]:
        available = self.ai_manager.get_available_providers(model_type=model_type)
        prefer_provider, model = self.ai_manager._resolve_prefer_provider_and_model(
            model, prefer_provider
        )
        if prefer_provider:
            available = [p for p in available if p == prefer_provider]
        return available, prefer_provider, model

    def _log_submission(
        self,
        prompt: Optional[str],
        image_url: Optional[str],
        prefer_provider: Optional[str],
        model: Optional[str],
        duration: int,
        fps: int,
        resolution: str,
    ) -> None:
        self.ai_manager._log_request(
            task="submit_video_task",
            provider=prefer_provider,
            model=model,
            params={
                "duration": duration,
                "fps": fps,
                "resolution": resolution,
                "mode": ("image_to_video" if image_url else "text_to_video"),
            },
        )
        self.ai_manager._log_prompt(
            prompt
            if not image_url
            else f"<image_url>: {self.ai_manager._truncate(image_url, 256)}"
        )

    async def _submit_once(
        self,
        available: list[str],
        prefer_provider: Optional[str],
        prompt: Optional[str],
        image_url: Optional[str],
        end_image_url: Optional[str],
        model_type: AIModelType,
        model: Optional[str],
        duration: int,
        fps: int,
        resolution: str,
        **kwargs: Any,
    ) -> Optional[tuple[AIResponse, Optional[str], str]]:
        provider_name = self.ai_manager._select_provider(available, prefer_provider)
        if not provider_name:
            return None
        provider = self.ai_manager.providers[provider_name]
        self.ai_manager._update_request_count(provider_name)
        try:
            provider_model = await resolve_provider_model(
                self.ai_manager, provider, model_type, model
            )
            response = await self._submit_to_provider(
                provider_name,
                provider,
                provider_model,
                prompt,
                image_url,
                end_image_url,
                duration,
                fps,
                resolution,
                model_type,
                **kwargs,
            )
        except Exception as exc:
            self.logger.warning(
                "submit_video_task failed for provider %s: %s",
                provider_name,
                exc,
            )
            provider_model = model
            response = self._build_failure_response(
                f"视频任务提交失败: {exc}",
                provider_name,
                provider_model,
                model_type,
            )
        self.ai_manager._log_response(
            task="submit_video_task",
            provider=provider_name,
            model=provider_model,
            response=response,
        )
        return response, provider_model, provider_name

    async def _submit_to_provider(
        self,
        provider_name: str,
        provider: Any,
        provider_model: str,
        prompt: Optional[str],
        image_url: Optional[str],
        end_image_url: Optional[str],
        duration: int,
        fps: int,
        resolution: str,
        model_type: AIModelType,
        **kwargs: Any,
    ) -> AIResponse:
        if not hasattr(provider, "submit_video_task"):
            return AIResponse(
                success=False,
                error=f"提供商 {provider_name} 不支持视频任务提交",
                provider=provider_name,
                model=provider_model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=model_type,
            )
        return await provider.submit_video_task(
            prompt=prompt,
            image_url=image_url,
            end_image_url=end_image_url,
            model=provider_model,
            duration=duration,
            fps=fps,
            resolution=resolution,
            **kwargs,
        )

    def _build_failure_response(
        self,
        message: str,
        provider: str,
        model: Optional[str],
        model_type: AIModelType,
    ) -> AIResponse:
        return AIResponse(
            success=False,
            error=message,
            provider=provider,
            model=model or "unknown",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type,
        )
