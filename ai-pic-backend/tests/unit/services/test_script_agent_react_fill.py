from types import SimpleNamespace

import pytest

from app.services.script_agent_react_fill import try_fill_pending_scenes_after_react
from app.services.duration_orchestrator.state import SceneBudget


@pytest.mark.asyncio
async def test_try_fill_pending_scenes_after_react_accepts_dict_response():
    async def _generate_text(**_: object):
        return SimpleNamespace(
            success=True,
            data={
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "你好"},
                    {"scene_number": 1, "character": "A", "content": "我们继续往前。"},
                    {"scene_number": 2, "character": "B", "content": "不应该出现"},
                ],
                "stage_directions": [
                    {"scene_number": 1, "timing": "mid", "content": "动作", "type": "action"}
                ],
            },
        )

    ai_manager = SimpleNamespace(generate_text=_generate_text)
    pending_budgets = [
        SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=2,
            target_word_count=10,
            min_duration_seconds=1,
            max_duration_seconds=3,
            attempt_count=3,
        )
    ]

    def _constraints(_: list[SceneBudget], __: list[dict]) -> str:
        return ""

    filled = await try_fill_pending_scenes_after_react(
        ai_manager=ai_manager,
        episode={"title": "ep"},
        story={"title": "story"},
        scenes=[{"scene_number": 1, "summary": "s1"}, {"scene_number": 2, "summary": "s2"}],
        pending_budgets=pending_budgets,
        dialogue_style="natural",
        language="zh",
        format_type="short_video",
        temperature=0.7,
        model=None,
        prefer_provider=None,
        existing_dialogues=[],
        existing_stage_directions=[],
        build_word_count_constraints=_constraints,
    )

    assert filled is not None
    merged_dialogues, merged_stage, pending_scene_numbers = filled
    assert pending_scene_numbers == [1]
    assert len(merged_dialogues) == 2
    assert merged_dialogues[0]["scene_number"] == 1
    assert merged_dialogues[1]["scene_number"] == 1
    assert merged_stage and merged_stage[0]["scene_number"] == 1


@pytest.mark.asyncio
async def test_try_fill_pending_scenes_after_react_returns_none_when_constraints_not_met():
    calls = 0

    async def _generate_text(**_: object):
        nonlocal calls
        calls += 1
        return SimpleNamespace(
            success=True,
            data={
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "太短"},
                    {"scene_number": 1, "character": "B", "content": "仍然短"},
                ],
                "stage_directions": [],
            },
        )

    ai_manager = SimpleNamespace(generate_text=_generate_text)
    pending_budgets = [
        SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=10,
            target_word_count=45,
            min_duration_seconds=8,
            max_duration_seconds=12,
            attempt_count=3,
        )
    ]

    def _constraints(_: list[SceneBudget], __: list[dict]) -> str:
        return ""

    filled = await try_fill_pending_scenes_after_react(
        ai_manager=ai_manager,
        episode={"title": "ep"},
        story={"title": "story"},
        scenes=[{"scene_number": 1, "summary": "s1"}],
        pending_budgets=pending_budgets,
        dialogue_style="natural",
        language="zh",
        format_type="short_video",
        temperature=0.7,
        model=None,
        prefer_provider=None,
        existing_dialogues=[],
        existing_stage_directions=[],
        build_word_count_constraints=_constraints,
    )

    assert filled is None
    assert calls == 3
