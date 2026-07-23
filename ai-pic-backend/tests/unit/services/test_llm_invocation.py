from __future__ import annotations

import json
from types import SimpleNamespace

from app.models.llm_invocation import LLMInvocation
from app.services import llm_invocation


def _inferred_scene() -> str:
    return llm_invocation.infer_call_scene()


def test_infers_call_scene_from_business_caller() -> None:
    assert _inferred_scene() == f"{__name__}._inferred_scene"


def test_persists_complete_prompt_response_and_normalized_tokens(
    test_db, monkeypatch
) -> None:
    monkeypatch.setattr(llm_invocation, "SessionLocal", test_db)
    prompt = "输入" * 40000
    response_text = "输出" * 40000

    handle = llm_invocation.begin_llm_invocation(
        call_scene="app.services.story.story_generation",
        provider="openai",
        model="gpt-5",
        attempt_index=2,
        prompt=prompt,
        system_prompt="完整系统提示",
        request_parameters={"temperature": 0.2},
    )
    llm_invocation.finish_llm_invocation(
        handle,
        response=SimpleNamespace(
            success=True,
            data=response_text,
            error=None,
            usage={
                "prompt_tokens": 120,
                "completion_tokens": 30,
                "prompt_tokens_details": {"cached_tokens": 80},
            },
            metadata={"finish_reason": "stop"},
        ),
    )

    with test_db() as session:
        row = session.query(LLMInvocation).one()
        assert row.prompt == prompt
        assert row.system_prompt == "完整系统提示"
        assert row.response == response_text
        assert row.call_scene == "app.services.story.story_generation"
        assert row.model == "gpt-5"
        assert row.attempt_index == 2
        assert row.status == "succeeded"
        assert row.input_tokens == 120
        assert row.cache_tokens == 80
        assert row.output_tokens == 30
        assert row.finished_at is not None


def test_persists_failed_invocation(test_db, monkeypatch) -> None:
    monkeypatch.setattr(llm_invocation, "SessionLocal", test_db)
    handle = llm_invocation.begin_llm_invocation(
        call_scene="app.services.scoring.script_score",
        provider="deepseek",
        model="deepseek-v4",
        attempt_index=1,
        prompt="score",
        system_prompt=None,
        request_parameters={},
    )

    llm_invocation.finish_llm_invocation(handle, error="provider timeout")

    with test_db() as session:
        row = session.query(LLMInvocation).one()
        assert row.status == "failed"
        assert row.error == "provider timeout"
        assert row.response is None


def test_media_invocation_tracks_submission_and_final_assets(
    test_db, monkeypatch
) -> None:
    monkeypatch.setattr(llm_invocation, "SessionLocal", test_db)
    handle = llm_invocation.begin_llm_invocation(
        invocation_type="image_to_video",
        call_scene="app.services.video.submit",
        provider="google",
        model="veo-3",
        attempt_index=1,
        original_prompt="原始视频提示词",
        prompt="增强后的视频提示词",
        system_prompt=None,
        input_references=[
            {
                "role": "start_image",
                "url": "https://cdn.example.com/start.png",
                "object_key": "references/start.png",
                "persisted": True,
            }
        ],
        request_parameters={"duration": 5},
    )
    llm_invocation.finish_llm_invocation(
        handle,
        response=SimpleNamespace(
            success=True,
            data={"task_id": "provider-task-1"},
            error=None,
            usage={},
            metadata={},
            provider="google",
            model="veo-3",
        ),
        status="submitted",
        provider_task_id="provider-task-1",
        complete=False,
    )

    with test_db() as session:
        submitted = session.query(LLMInvocation).one()
        invocation_id = submitted.id
        assert submitted.invocation_type == "image_to_video"
        assert submitted.original_prompt == "原始视频提示词"
        assert submitted.prompt == "增强后的视频提示词"
        assert submitted.input_references[0]["object_key"] == "references/start.png"
        assert submitted.provider_task_id == "provider-task-1"
        assert submitted.status == "submitted"
        assert submitted.finished_at is None

    output_assets = [
        {
            "media_type": "video",
            "role": "video",
            "url": "https://cdn.example.com/final.mp4",
            "object_key": "videos/final.mp4",
            "persisted": True,
        }
    ]
    llm_invocation.complete_llm_invocation(
        invocation_id,
        status="succeeded",
        response_data={"video_url": "https://cdn.example.com/final.mp4"},
        output_assets=output_assets,
    )

    with test_db() as session:
        completed = session.query(LLMInvocation).one()
        assert completed.status == "succeeded"
        assert completed.output_assets == output_assets
        assert json.loads(completed.response)["video_url"].endswith("final.mp4")
        assert completed.finished_at is not None
        assert completed.latency_ms is not None


def test_normalizes_google_cached_tokens() -> None:
    assert llm_invocation.normalize_token_usage(
        {},
        {
            "raw": {
                "usageMetadata": {
                    "promptTokenCount": 90,
                    "cachedContentTokenCount": 50,
                    "candidatesTokenCount": 12,
                }
            }
        },
    ) == (90, 50, 12)


def test_preserves_zero_token_counts() -> None:
    assert llm_invocation.normalize_token_usage(
        {"prompt_tokens": 0, "completion_tokens": 0}
    ) == (0, None, 0)
