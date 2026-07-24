from types import SimpleNamespace
from unittest.mock import AsyncMock

import anyio
import pytest
from app.services.story import story_novel_export_ai
from fastapi import HTTPException


def _service(finish_reason: str | None):
    response = SimpleNamespace(
        success=True,
        data="完整输出",
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
