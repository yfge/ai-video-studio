from types import SimpleNamespace
from unittest.mock import AsyncMock

import anyio
import pytest
from app.services.story import story_novel_export_ai
from fastapi import HTTPException


def _service(finish_reason: str | None, *, data: str = "完整输出"):
    response = SimpleNamespace(
        success=True,
        data=data,
        error=None,
        provider="deepseek",
        model="deepseek-v4-pro",
        metadata={"finish_reason": finish_reason} if finish_reason else {},
    )
    return SimpleNamespace(
        ai_manager=SimpleNamespace(generate_text=AsyncMock(return_value=response))
    )


def _generate():
    return story_novel_export_ai.generate_story_novel_text(
        prompt="prompt",
        system_prompt="system",
        model="deepseek-v4-pro",
        prefer_provider="deepseek",
        temperature=0,
        max_tokens=16000,
    )


def test_story_novel_accepts_explicit_stop(monkeypatch):
    monkeypatch.setattr(story_novel_export_ai, "ai_service", _service("stop"))

    assert anyio.run(_generate) == "完整输出"


@pytest.mark.parametrize(
    "finish_reason",
    ["length", "max_tokens", "max_output_tokens", "token_limit", "content_filter"],
)
def test_story_novel_rejects_truncated_finish_reason(monkeypatch, finish_reason):
    monkeypatch.setattr(story_novel_export_ai, "ai_service", _service(finish_reason))

    with pytest.raises(HTTPException, match=f"finish_reason={finish_reason}"):
        anyio.run(_generate)


def test_story_novel_reports_truncation_when_reasoning_consumes_all_output(monkeypatch):
    monkeypatch.setattr(
        story_novel_export_ai,
        "ai_service",
        _service("length", data=""),
    )

    with pytest.raises(HTTPException, match="finish_reason=length"):
        anyio.run(_generate)


def test_story_novel_marks_reasoning_only_stop_as_product_rejected(monkeypatch):
    monkeypatch.setattr(story_novel_export_ai, "ai_service", _service("stop", data=""))
    marked = []
    monkeypatch.setattr(
        story_novel_export_ai,
        "mark_invocation_product_rejected",
        lambda *args, **kwargs: marked.append((args, kwargs))
        or {"invocation_id": 1534},
    )

    async def run():
        return await story_novel_export_ai.generate_story_novel_text(
            prompt="prompt",
            system_prompt="system",
            model="deepseek-v4-pro",
            prefer_provider="deepseek",
            temperature=0,
            max_tokens=16000,
            call_scene="story_novel.revision.planning",
        )

    with pytest.raises(HTTPException, match="reason=empty_model_content"):
        anyio.run(run)

    assert marked[0][1] == {
        "invocation_id": None,
        "reason": "empty_model_content",
    }


def test_truncation_records_product_rejection_without_reclassifying_transport(
    monkeypatch,
):
    monkeypatch.setattr(story_novel_export_ai, "ai_service", _service("length"))
    marked = []
    monkeypatch.setattr(
        story_novel_export_ai,
        "latest_invocation_evidence",
        lambda *_args, **_kwargs: {"invocation_id": 1468, "status": "succeeded"},
    )
    monkeypatch.setattr(
        story_novel_export_ai,
        "mark_invocation_product_rejected",
        lambda *args, **kwargs: marked.append((args, kwargs))
        or {"invocation_id": 1468},
    )

    async def run():
        return await story_novel_export_ai.generate_story_novel_text(
            prompt="prompt",
            system_prompt="system",
            model="deepseek-v4-pro",
            prefer_provider="deepseek",
            temperature=0,
            max_tokens=16000,
            call_scene="story_novel.revision.prose.1",
        )

    with pytest.raises(story_novel_export_ai.TruncatedNovelOutput) as exc:
        anyio.run(run)

    assert exc.value.invocation_evidence == {
        "invocation_id": 1468,
        "status": "succeeded",
        "product_status": "rejected",
    }
    assert marked[0][1] == {"invocation_id": None, "reason": "truncated:length"}
