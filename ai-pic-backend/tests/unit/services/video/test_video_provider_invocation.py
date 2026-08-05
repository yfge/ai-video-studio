from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.llm_invocation import LLMInvocation
from app.services import ai_manager_video_invocation as video_invocation
from app.services import llm_invocation
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_task_provider_submission import submit_to_video_provider
from app.services.video.video_task_submission_persistence import (
    persist_submitted_video_task,
)


@pytest.mark.asyncio
async def test_video_submission_records_invocation_and_exposes_link(
    test_db, monkeypatch
) -> None:
    monkeypatch.setattr(llm_invocation, "SessionLocal", test_db)
    provider = MagicMock()
    provider.submit_video_task = AsyncMock(
        return_value=AIResponse(
            success=True,
            data={"task_id": "provider-task-1", "duration": 5},
            provider="google",
            model="veo-3",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
            metadata={
                "status_url": "https://provider.example.com/task?token=secret",
                "inline": "data:video/mp4;base64,secret",
            },
        )
    )

    response = await submit_to_video_provider(
        provider_name="google",
        provider=provider,
        provider_model="veo-3",
        prompt="完整视频提示词",
        image_url=None,
        end_image_url=None,
        duration=5,
        fps=24,
        resolution="720p",
        model_type=AIModelType.IMAGE_TO_VIDEO,
        call_scene="tests.video.submit",
    )

    with test_db() as session:
        row = session.query(LLMInvocation).one()
        assert row.invocation_type == "image_to_video"
        assert row.call_scene == "tests.video.submit"
        assert row.prompt == "完整视频提示词"
        assert row.provider_task_id == "provider-task-1"
        assert row.status == "submitted"
        assert row.response_metadata["status_url"] == (
            "https://provider.example.com/task"
        )
        assert row.response_metadata["inline"] == "<inline-media-omitted>"
        assert response.metadata["llm_invocation_id"] == row.id


def test_video_task_persistence_links_invocation() -> None:
    repo = MagicMock()
    response = SimpleNamespace(
        data={"task_id": "provider-task-1"},
        provider="google",
        model="veo-3",
        metadata={"llm_invocation_id": 42},
    )

    persist_submitted_video_task(
        repo,
        task=SimpleNamespace(id=9, user_id=7),
        script_id=11,
        frame_index=2,
        response=response,
        prompt="prompt",
        start_url="https://cdn.example.com/start.png",
        end_url=None,
        reference_images=None,
        target_duration_seconds=5,
        provider_duration_seconds=5,
        opts={},
    )

    assert repo.create.call_args.kwargs["llm_invocation_id"] == 42


def test_missing_provider_task_id_finalizes_invocation(test_db, monkeypatch) -> None:
    monkeypatch.setattr(llm_invocation, "SessionLocal", test_db)
    handle = video_invocation.begin_attempt(
        invocation_type="text_to_video",
        call_scene="tests.video.missing_task",
        provider="google",
        model="veo-3",
        attempt_index=1,
        prompt="prompt",
        input_references=[],
        request_parameters={},
    )
    response = AIResponse(
        success=True,
        data={},
        provider="google",
        model="veo-3",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=AIModelType.TEXT_TO_VIDEO,
    )
    video_invocation.finish_attempt(handle, response)
    video_invocation.fail_submitted_response(response, "未返回任务ID")

    with test_db() as session:
        row = session.query(LLMInvocation).one()
        assert row.status == "failed"
        assert row.error == "未返回任务ID"
        assert row.finished_at is not None
