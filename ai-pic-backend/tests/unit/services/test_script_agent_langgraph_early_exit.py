from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_script_agent_avoids_extra_llm_calls_when_scene_plan_fails():
    from app.services.script_agent import LANGGRAPH_AVAILABLE, ScriptLangGraphAgent

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    calls = 0

    async def _generate_text(**_: object):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise AssertionError("unexpected extra LLM call after scene plan failure")
        return SimpleNamespace(
            success=False,
            data={},
            provider="test",
            model="test",
            usage=None,
        )

    service = SimpleNamespace(ai_manager=SimpleNamespace(generate_text=_generate_text))
    agent = ScriptLangGraphAgent(service)

    with patch("app.services.script_agent.prompt_manager.render_prompt", return_value="prompt"):
        result = await agent.generate(
            episode={"id": 1, "title": "ep"},
            story={"id": 1, "title": "story", "characters": []},
            format_type="short_video",
            language="zh",
            dialogue_style="natural",
            scene_detail_level="detailed",
            additional_requirements=None,
            style_preferences=None,
            model=None,
            prefer_provider=None,
            temperature=0.7,
        )

    assert result is None
    assert calls == 1

