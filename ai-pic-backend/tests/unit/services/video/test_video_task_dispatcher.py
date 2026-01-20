"""Unit tests for VideoTaskDispatcher error reporting."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_task_dispatcher import VideoTaskDispatcher


class _DummyManager:
    def __init__(
        self,
        *,
        providers: dict[str, object],
        max_retries: int = 1,
        enable_fallback: bool = True,
    ) -> None:
        self.config = SimpleNamespace(
            max_retries=max_retries,
            enable_fallback=enable_fallback,
        )
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


@pytest.mark.asyncio
async def test_submit_video_task_single_provider_includes_real_error():
    provider = MagicMock()
    provider.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="google", error="429 Too Many Requests")
    )
    manager = _DummyManager(providers={"google": provider}, max_retries=1)
    dispatcher = VideoTaskDispatcher(manager)

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(return_value="google:veo"),
    ):
        response = await dispatcher.submit_video_task(
            prompt="test",
            image_url=None,
            end_image_url=None,
            model="google:veo",
            prefer_provider="google",
            duration=5,
            fps=24,
            resolution="720p",
        )

    assert response.success is False
    assert response.error
    assert "429" in response.error
    assert "google" in response.error


@pytest.mark.asyncio
async def test_submit_video_task_multiple_providers_aggregates_errors():
    google = MagicMock()
    google.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="google", error="quota exceeded")
    )
    keling = MagicMock()
    keling.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="keling", error="invalid prompt")
    )

    manager = _DummyManager(
        providers={"google": google, "keling": keling},
        max_retries=2,
    )
    dispatcher = VideoTaskDispatcher(manager)

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(return_value="test-model"),
    ):
        response = await dispatcher.submit_video_task(
            prompt="test",
            image_url=None,
            end_image_url=None,
            model=None,
            prefer_provider=None,
            duration=5,
            fps=24,
            resolution="720p",
        )

    assert response.success is False
    assert response.error
    assert "google" in response.error
    assert "quota exceeded" in response.error
    assert "keling" in response.error
    assert "invalid prompt" in response.error


@pytest.mark.asyncio
async def test_submit_video_task_fallback_disabled_returns_first_error():
    google = MagicMock()
    google.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="google", error="quota exceeded")
    )
    keling = MagicMock()
    keling.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="keling", error="invalid prompt")
    )

    manager = _DummyManager(
        providers={"google": google, "keling": keling},
        max_retries=2,
        enable_fallback=False,
    )
    dispatcher = VideoTaskDispatcher(manager)

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(return_value="test-model"),
    ):
        response = await dispatcher.submit_video_task(
            prompt="test",
            image_url=None,
            end_image_url=None,
            model=None,
            prefer_provider=None,
            duration=5,
            fps=24,
            resolution="720p",
        )

    assert response.success is False
    assert response.error == "quota exceeded"
