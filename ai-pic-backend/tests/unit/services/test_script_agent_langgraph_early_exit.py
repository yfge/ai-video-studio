from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.services.duration_orchestrator.state import SceneBudget


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

    with patch(
        "app.services.script_agent.prompt_manager.render_prompt", return_value="prompt"
    ):
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


@pytest.mark.asyncio
async def test_script_agent_clears_react_retry_flag_after_successful_retry():
    from app.services.script_agent import LANGGRAPH_AVAILABLE, ScriptLangGraphAgent

    if not LANGGRAPH_AVAILABLE:
        pytest.skip("langgraph not available")

    calls: list[str] = []
    valid_dialogues = [
        {
            "scene_number": 1,
            "character": "A",
            "content": "我们现在就把方案定下来，先解决眼前的问题，再把后面的风险逐个拆开处理。",
        },
        {
            "scene_number": 1,
            "character": "A",
            "content": "你不用再绕弯子，直接告诉我真正卡住的是预算、人手，还是对结果没有信心。",
        },
    ]

    async def _generate_text(**kwargs: object):
        schema = kwargs.get("json_schema")
        name = schema.get("name") if isinstance(schema, dict) else ""
        calls.append(str(name))
        if name == "script_scenes":
            return SimpleNamespace(
                success=True,
                data={
                    "scenes": [
                        {
                            "scene_number": 1,
                            "slug_line": "INT. OFFICE - DAY",
                            "location": "office",
                            "time_of_day": "day",
                            "summary": "A confronts the plan.",
                        }
                    ]
                },
                provider="test",
                model="test",
                usage=None,
            )
        if name == "script_dialogues" and calls.count("script_dialogues") == 1:
            return SimpleNamespace(
                success=True,
                data={
                    "dialogues": [
                        {
                            "scene_number": 1,
                            "character": "A",
                            "content": "太短了。",
                        }
                    ],
                    "stage_directions": [],
                },
                provider="test",
                model="test",
                usage=None,
            )
        if name == "script_dialogues":
            return SimpleNamespace(
                success=True,
                data={"dialogues": valid_dialogues, "stage_directions": []},
                provider="test",
                model="test",
                usage=None,
            )
        if name == "script_review":
            return SimpleNamespace(
                success=True,
                data={
                    "dialogues": valid_dialogues,
                    "stage_directions": [],
                    "corrections": [],
                },
                provider="test",
                model="test",
                usage=None,
            )
        raise AssertionError(f"unexpected LLM call: {name}")

    service = SimpleNamespace(ai_manager=SimpleNamespace(generate_text=_generate_text))
    agent = ScriptLangGraphAgent(service)
    budget = SceneBudget(
        scene_number=1,
        scene_index=0,
        target_duration_seconds=6,
        target_word_count=28,
        min_duration_seconds=1,
        max_duration_seconds=120,
    )

    with patch(
        "app.services.script_agent.prompt_manager.render_prompt", return_value="prompt"
    ):
        result = await agent.generate(
            episode={"id": 1, "title": "ep", "episode_number": 1},
            story={"id": 1, "title": "story", "characters": [{"name": "A"}]},
            format_type="short_video",
            language="zh",
            dialogue_style="natural",
            scene_detail_level="detailed",
            additional_requirements=None,
            style_preferences=None,
            model=None,
            prefer_provider=None,
            temperature=0.7,
            scene_budgets=[budget],
            duration_minutes=0,
        )

    assert result is not None
    assert calls == [
        "script_scenes",
        "script_dialogues",
        "script_dialogues",
        "script_review",
    ]
