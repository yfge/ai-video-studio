from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.ai import text_generation
from app.services.ai.text_generation import TextGenerationMixin


class _TextService(TextGenerationMixin):
    def __init__(self) -> None:
        self.ai_manager = None
        self.base_url = "https://custom.example"
        self.api_key = "test-key"


@pytest.mark.asyncio
async def test_provider_fallback_routes_through_audited_manager() -> None:
    service = _TextService()
    service.ai_manager = SimpleNamespace(
        generate_text=AsyncMock(
            return_value=SimpleNamespace(success=True, data="complete response")
        )
    )

    result = await service._generate_with_openai_gpt("complete prompt", "story_outline")

    assert result == "complete response"
    service.ai_manager.generate_text.assert_awaited_once()
    kwargs = service.ai_manager.generate_text.await_args.kwargs
    assert kwargs["prompt"] == "complete prompt"
    assert kwargs["call_scene"] == "legacy.story_outline.openai"
    assert kwargs["prefer_provider"] == "openai"


@pytest.mark.asyncio
async def test_custom_fallback_records_complete_attempt(monkeypatch) -> None:
    service = _TextService()
    started: list[dict] = []
    finished: list[tuple[dict, dict]] = []

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "text": "完整输出",
                "model": "custom-v2",
                "usage": {
                    "input_tokens": 10,
                    "cache_tokens": 4,
                    "output_tokens": 3,
                },
            }

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            return _Response()

    def _begin(**payload):
        started.append(payload)
        return payload

    def _finish(handle, **payload):
        finished.append((handle, payload))

    monkeypatch.setattr(text_generation.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(text_generation, "begin_llm_invocation", _begin)
    monkeypatch.setattr(text_generation, "finish_llm_invocation", _finish)

    result = await service._generate_with_custom_service("完整输入", "story_novel")

    assert result == "完整输出"
    assert started[0]["prompt"] == "完整输入"
    assert started[0]["call_scene"] == "legacy.story_novel.custom_service"
    recorded_response = finished[0][1]["response"]
    assert recorded_response.data == "完整输出"
    assert recorded_response.model == "custom-v2"
