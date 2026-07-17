from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.services.providers.base import AIModelType, AIResponse
from app.services.video.video_capabilities import resolve_video_duration
from app.services.video.video_task_dispatch_helpers import (
    DISPATCHER_PROVIDER,
    build_failure_response,
    log_submission,
    resolve_model_type,
)
from app.services.video.video_task_duration_adapter import (
    attach_duration_resolution,
    copy_duration_resolution,
)
from app.services.video.video_task_provider_candidates import (
    resolve_video_provider_candidates,
)
from app.services.video.video_task_provider_resolver import resolve_provider_model
from app.services.video.video_task_provider_submission import submit_to_video_provider


class VideoTaskDispatcher:
    def __init__(self, ai_manager: Any):
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
        model_type = resolve_model_type(image_url, kwargs)
        available, prefer_provider, model = resolve_video_provider_candidates(
            self.ai_manager,
            model,
            prefer_provider,
            model_type,
            image_url=image_url,
            end_image_url=end_image_url,
            request_kwargs=kwargs,
        )
        if not available:
            return build_failure_response(
                "没有可用的视频生成提供商",
                DISPATCHER_PROVIDER,
                model,
                model_type,
            )
        log_submission(
            self.ai_manager,
            prompt=prompt,
            image_url=image_url,
            prefer_provider=prefer_provider,
            model=model,
            duration=duration,
            fps=fps,
            resolution=resolution,
            model_type=model_type,
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
        last_response: Optional[AIResponse] = None
        errors: list[str] = []
        retry_limit = self.ai_manager.config.max_retries
        if self.ai_manager.config.enable_fallback:
            retry_limit = max(retry_limit, len(available))
        for _ in range(retry_limit):
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
            last_response = response
            if provider_model:
                last_model_used = provider_model
            if not response.success:
                errors.append(f"{provider_name}: {response.error or 'unknown error'}")
            if response.success or not self.ai_manager.config.enable_fallback:
                return response
            if provider_name in available:
                available.remove(provider_name)
            if not available:
                break
        if last_response:
            if errors and self.ai_manager.config.enable_fallback:
                error_details = self.ai_manager._truncate("; ".join(errors), 800)
                failure = build_failure_response(
                    f"所有视频生成提供商都失败了: {error_details}",
                    last_response.provider or DISPATCHER_PROVIDER,
                    last_model_used,
                    model_type,
                )
                return copy_duration_resolution(last_response, failure)
            return last_response
        return build_failure_response(
            "所有视频生成提供商都失败了",
            DISPATCHER_PROVIDER,
            last_model_used,
            model_type,
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
        target_duration_seconds = kwargs.pop("target_duration_seconds", None)
        provider_name = self.ai_manager._select_provider(available, prefer_provider)
        if not provider_name:
            return None
        provider = self.ai_manager.providers[provider_name]
        self.ai_manager._update_request_count(provider_name)
        try:
            provider_model = await resolve_provider_model(
                self.ai_manager, provider, model_type, model
            )
            duration_match = (
                resolve_video_duration(
                    provider=provider_name,
                    model=provider_model,
                    target_duration_seconds=target_duration_seconds,
                    resolution=resolution,
                )
                if target_duration_seconds is not None
                else None
            )
            if duration_match and duration_match.needs_split:
                response = build_failure_response(
                    "Timeline target duration exceeds provider capability",
                    provider_name,
                    provider_model,
                    model_type,
                )
                response = attach_duration_resolution(response, duration_match)
                self.ai_manager._log_response(
                    task="submit_video_task",
                    provider=provider_name,
                    model=provider_model,
                    response=response,
                )
                return response, provider_model, provider_name
            response = await submit_to_video_provider(
                provider_name=provider_name,
                provider=provider,
                provider_model=provider_model,
                prompt=prompt,
                image_url=image_url,
                end_image_url=end_image_url,
                duration=(
                    duration_match.provider_duration_seconds
                    if duration_match is not None
                    else duration
                ),
                fps=fps,
                resolution=resolution,
                model_type=model_type,
                **kwargs,
            )
            if duration_match is not None:
                response = attach_duration_resolution(response, duration_match)
        except Exception as exc:
            self.logger.warning(
                "submit_video_task failed for provider %s: %s",
                provider_name,
                exc,
            )
            provider_model = model
            response = build_failure_response(
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
