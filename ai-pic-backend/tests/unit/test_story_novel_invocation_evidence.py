from types import SimpleNamespace
from unittest.mock import AsyncMock

import anyio
import pytest
from app.services.story import story_novel_export_ai, story_novel_invocation_evidence
from fastapi import HTTPException


class _Session:
    def commit(self):
        pass

    def close(self):
        pass


def _row(row_id: int, response: str):
    return SimpleNamespace(
        id=row_id,
        call_scene="story_novel.revision.prose.1",
        status="succeeded",
        response=response,
        provider="deepseek",
        model="deepseek-chat",
        input_tokens=11,
        cache_tokens=2,
        output_tokens=7,
        response_metadata={"finish_reason": "stop"},
        latency_ms=19,
    )


def test_invocation_evidence_binds_exact_response_not_latest_scene(monkeypatch):
    rows = [_row(10, "\n expected \n"), _row(11, "concurrent-other-response")]
    monkeypatch.setattr(story_novel_invocation_evidence, "SessionLocal", _Session)
    monkeypatch.setattr(
        story_novel_invocation_evidence,
        "LLMInvocationRepository",
        lambda _session: SimpleNamespace(
            get_by_id=lambda row_id: next(item for item in rows if item.id == row_id)
        ),
    )

    evidence = story_novel_invocation_evidence.latest_invocation_evidence(
        "story_novel.revision.prose.1", "expected", invocation_id=10
    )
    assert evidence["invocation_id"] == 10
    assert evidence["finish_reason"] == "stop"
    assert evidence["call_scene"] == "story_novel.revision.prose.1"
    assert evidence["response_hash"]
    assert evidence["raw_response_hash"] != evidence["response_hash"]


def test_product_rejection_updates_only_the_exact_empty_invocation(monkeypatch):
    rows = [_row(10, " \n"), _row(11, "")]

    class _Repository:
        def get_by_id(self, row_id):
            return next(item for item in rows if item.id == row_id)

        def update(self, row, **values):
            for key, value in values.items():
                setattr(row, key, value)

    monkeypatch.setattr(story_novel_invocation_evidence, "SessionLocal", _Session)
    monkeypatch.setattr(
        story_novel_invocation_evidence,
        "LLMInvocationRepository",
        lambda _session: _Repository(),
    )

    marked = story_novel_invocation_evidence.mark_invocation_product_rejected(
        "story_novel.revision.prose.1",
        "",
        invocation_id=10,
        reason="empty_model_content",
    )

    assert marked["invocation_id"] == 10
    assert rows[0].response_metadata["product_status"] == "rejected"
    assert "product_status" not in rows[1].response_metadata


def test_audited_novel_call_fails_closed_when_invocation_is_missing(monkeypatch):
    response = SimpleNamespace(
        success=True,
        data="完整输出",
        error=None,
        provider="deepseek",
        model="deepseek-chat",
        metadata={"finish_reason": "stop"},
    )
    monkeypatch.setattr(
        story_novel_export_ai,
        "ai_service",
        SimpleNamespace(
            ai_manager=SimpleNamespace(generate_text=AsyncMock(return_value=response))
        ),
    )
    monkeypatch.setattr(
        story_novel_export_ai,
        "latest_invocation_evidence",
        lambda *_args, **_kwargs: {},
    )

    async def run():
        return await story_novel_export_ai.generate_story_novel_text(
            prompt="prompt",
            system_prompt="system",
            model="deepseek-chat",
            prefer_provider="deepseek",
            temperature=0,
            max_tokens=16000,
            call_scene="story_novel.revision.prose.1",
        )

    with pytest.raises(HTTPException, match="调用审计证据缺失"):
        anyio.run(run)
