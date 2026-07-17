"""Timeline target-duration adaptation across video providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.providers.base import AIModelType
from app.services.video.video_task_dispatcher import VideoTaskDispatcher
from tests.unit.services.video.test_video_task_dispatcher import (
    _DummyManager,
    _failure_response,
    _success_response,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_name", "provider_model", "target", "expected", "allowed"),
    [
        ("google", "veo-3.1-generate", 7.0, 8, [4, 6, 8]),
        ("volcengine", "doubao-seedance", 7.0, 8, [4, 6, 8]),
        ("keling", "kling-v2", 7.0, 10, [5, 10]),
        ("minimax", "hailuo-2.3", 5.2, 6, [6, 10]),
    ],
)
async def test_timeline_target_duration_is_adapted_per_provider_attempt(
    provider_name,
    provider_model,
    target,
    expected,
    allowed,
):
    provider = MagicMock()
    provider.submit_video_task = AsyncMock(
        return_value=_success_response(
            provider=provider_name,
            model_type=AIModelType.TEXT_TO_VIDEO,
        )
    )
    dispatcher = VideoTaskDispatcher(
        _DummyManager(providers={provider_name: provider}, max_retries=1)
    )

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(return_value=provider_model),
    ):
        response = await dispatcher.submit_video_task(
            prompt="test",
            image_url=None,
            end_image_url=None,
            model=None,
            prefer_provider=None,
            duration=6,
            target_duration_seconds=target,
            fps=24,
            resolution="720p",
        )

    assert provider.submit_video_task.await_args.kwargs["duration"] == expected
    assert response.data["target_duration_seconds"] == target
    assert response.data["provider_duration_seconds"] == expected
    assert response.data["allowed_durations"] == allowed
    assert response.data["capability_source"]


@pytest.mark.asyncio
async def test_fallback_recomputes_provider_duration_for_each_provider():
    google = MagicMock()
    google.submit_video_task = AsyncMock(
        return_value=_failure_response(provider="google", error="quota exceeded")
    )
    keling = MagicMock()
    keling.submit_video_task = AsyncMock(
        return_value=_success_response(
            provider="keling",
            model_type=AIModelType.TEXT_TO_VIDEO,
        )
    )
    dispatcher = VideoTaskDispatcher(
        _DummyManager(
            providers={"google": google, "keling": keling},
            max_retries=2,
        )
    )

    with patch(
        "app.services.video.video_task_dispatcher.resolve_provider_model",
        new=AsyncMock(side_effect=["veo-3.1-generate", "kling-v2"]),
    ):
        response = await dispatcher.submit_video_task(
            prompt="test",
            image_url=None,
            end_image_url=None,
            model=None,
            prefer_provider=None,
            duration=7,
            target_duration_seconds=7.0,
            fps=24,
            resolution="720p",
        )

    assert google.submit_video_task.await_args.kwargs["duration"] == 8
    assert keling.submit_video_task.await_args.kwargs["duration"] == 10
    assert response.success is True
    assert response.data["provider_duration_seconds"] == 10
    assert response.data["capability_source"] == "keling/kling"
