"""Reference media provider-selection tests for VideoTaskDispatcher."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.providers.base import AIModelType, AIResponse, AITaskType, ModelInfo
from app.services.video.video_task_dispatcher import VideoTaskDispatcher


class _DummyManager:
    def __init__(self, *, providers: dict[str, object], max_retries: int = 1) -> None:
        self.config = SimpleNamespace(max_retries=max_retries, enable_fallback=True)
        self.providers = providers

    def get_available_providers(self, *, model_type: AIModelType) -> list[str]:
        return list(self.providers.keys())

    def _resolve_prefer_provider_and_model(self, model, prefer_provider):
        return prefer_provider, model

    def _select_provider(self, available, prefer_provider):
        if prefer_provider and prefer_provider in available:
            return prefer_provider
        return available[0] if available else None

    def _update_request_count(self, provider_name: str) -> None:  # noqa: ARG002
        return None

    def _log_request(self, **_kwargs) -> None:
        return None

    def _log_prompt(self, *_args, **_kwargs) -> None:
        return None

    def _log_response(self, **_kwargs) -> None:
        return None

    def _truncate(self, text: str, limit: int) -> str:
        return text[:limit]


def _failure_response(*, provider: str, error: str) -> AIResponse:
    return AIResponse(
        success=False,
        error=error,
        provider=provider,
        model="test-model",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=AIModelType.TEXT_TO_VIDEO,
    )


def _success_response(*, provider: str, model_type: AIModelType) -> AIResponse:
    return AIResponse(
        success=True,
        data={"task_id": "provider-task-1", "duration": 5},
        provider=provider,
        model="test-model",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=model_type,
    )


def _video_model(
    model_id: str,
    model_type: AIModelType,
    capabilities: list[str],
) -> ModelInfo:
    return ModelInfo(
        model_id=model_id,
        name=model_id,
        description=model_id,
        model_type=model_type,
        capabilities=capabilities,
    )


@pytest.mark.asyncio
async def test_submit_video_task_reference_only_filters_start_frame_providers():
    keling = MagicMock()
    keling.available_models = [
        _video_model(
            "keling-i2v",
            AIModelType.IMAGE_TO_VIDEO,
            ["image_to_video", "image_to_video_start_frame"],
        )
    ]
    keling.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="keling", error="image required")
    )
    volcengine = MagicMock()
    volcengine.available_models = [
        _video_model(
            "doubao-seedance-2-0-260128",
            AIModelType.TEXT_TO_VIDEO,
            ["text_to_video", "image_to_video", "reference_images"],
        )
    ]
    volcengine.submit_video_task = AsyncMock(
        return_value=_success_response(
            provider="volcengine",
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )
    )

    manager = _DummyManager(providers={"keling": keling, "volcengine": volcengine})
    dispatcher = VideoTaskDispatcher(manager)

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(return_value="doubao-seedance-2-0-260128"),
    ):
        response = await dispatcher.submit_video_task(
            prompt="Use panel 4 only",
            image_url=None,
            end_image_url=None,
            model=None,
            prefer_provider=None,
            duration=10,
            fps=24,
            resolution="720p",
            reference_images=["https://cdn.example.com/storyboard-grid.png"],
        )

    assert response.success is True
    keling.submit_video_task.assert_not_awaited()
    volcengine.submit_video_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_video_task_fallback_tries_all_reference_capable_providers():
    google = MagicMock()
    google.available_models = [
        _video_model(
            "veo-3.1-generate-preview",
            AIModelType.IMAGE_TO_VIDEO,
            ["image_to_video", "reference_images"],
        )
    ]
    google.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="google", error="model not found")
    )
    volcengine = MagicMock()
    volcengine.available_models = [
        _video_model(
            "doubao-seedance-2-0-260128",
            AIModelType.TEXT_TO_VIDEO,
            ["text_to_video", "image_to_video", "reference_images"],
        )
    ]
    volcengine.submit_video_task = AsyncMock(
        return_value=_success_response(
            provider="volcengine",
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )
    )

    manager = _DummyManager(providers={"google": google, "volcengine": volcengine})
    dispatcher = VideoTaskDispatcher(manager)

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(return_value="test-model"),
    ):
        response = await dispatcher.submit_video_task(
            prompt="Use panel 5 only",
            image_url=None,
            end_image_url=None,
            model=None,
            prefer_provider=None,
            duration=10,
            fps=24,
            resolution="720p",
            reference_images=["https://cdn.example.com/storyboard-grid.png"],
        )

    assert response.success is True
    google.submit_video_task.assert_awaited_once()
    volcengine.submit_video_task.assert_awaited_once()
