from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.story import story_novel_export_ai, story_novel_task_generation
from app.services.story.story_novel_v3_prompts import prose_blocks_prompt
from fastapi import HTTPException


def _revision():
    return SimpleNamespace(
        business_id="revision-v3",
        model="deepseek:test",
        temperature=0.2,
        generation_plan={
            "model_policy": {
                "planning_model": "deepseek:test",
                "prose_model": "deepseek:test",
                "audit_model": "deepseek:test",
            }
        },
    )


@pytest.mark.asyncio
async def test_v3_stage_rejects_unmanaged_prompt_before_provider(monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr(
        story_novel_task_generation, "generate_story_novel_text", provider
    )

    with pytest.raises(HTTPException, match="缺少 PromptManager"):
        await story_novel_task_generation.generate_task_text(
            _revision(), "inline prompt", max_tokens=16000, stage="prose.1"
        )

    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_v3_template_fingerprint_is_passed_before_provider_failure(monkeypatch):
    captured = {}

    async def fail(**kwargs):
        captured.update(kwargs)
        raise HTTPException(status_code=502, detail="provider failed")

    monkeypatch.setattr(story_novel_task_generation, "generate_story_novel_text", fail)
    prompt = prose_blocks_prompt({"chapter_brief": {"beats": []}})

    with pytest.raises(HTTPException, match="provider failed"):
        await story_novel_task_generation.generate_task_text(
            _revision(), prompt, max_tokens=16000, stage="prose.1"
        )

    assert captured["require_managed_invocation"] is True
    assert captured["prompt_template"]["template"] == "story_novel_prose_blocks_v3"
    assert (
        captured["prompt_template"]["system_prompt"]["template"]
        == "story_novel_system_v3"
    )


@pytest.mark.asyncio
async def test_v3_call_rejects_legacy_fallback_when_manager_is_unavailable(
    monkeypatch,
):
    legacy = AsyncMock(return_value="legacy text")
    monkeypatch.setattr(
        story_novel_export_ai,
        "ai_service",
        SimpleNamespace(ai_manager=None, _call_text_generation_service=legacy),
    )

    with pytest.raises(HTTPException, match="禁止 legacy fallback"):
        await story_novel_export_ai.generate_story_novel_text(
            prompt="prompt",
            system_prompt="system",
            model="test",
            prefer_provider="deepseek",
            temperature=0.0,
            max_tokens=16000,
            require_managed_invocation=True,
        )

    legacy.assert_not_awaited()
