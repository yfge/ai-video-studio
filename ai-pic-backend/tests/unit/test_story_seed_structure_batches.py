import json

from app.schemas.story_seed import StorySeedStructuredOutline
from app.services.story.story_seed_structure_batches import (
    parse_chapter_batch,
    parse_progression,
)
from app.services.story.story_seed_structure_policy import (
    MAX_STRUCTURE_TOKENS,
    chapter_batch_token_budget,
    progression_token_budget,
    structure_ranges,
)
from app.services.story.story_seed_structure_prompts import (
    structured_arc_chapters_prompt,
)


def test_two_million_character_scale_uses_bounded_outline_batches():
    positions = list(range(1, 801))

    ranges = structure_ranges(positions)

    assert len(ranges) == 25
    assert ranges[0] == list(range(1, 33))
    assert ranges[-1] == list(range(769, 801))
    assert chapter_batch_token_budget(ranges[0]) == 12800
    assert 8192 < progression_token_budget(positions) <= MAX_STRUCTURE_TOKENS
    assert all(
        chapter_batch_token_budget(row) <= MAX_STRUCTURE_TOKENS for row in ranges
    )


def test_progression_curves_are_optional_soft_arc_fields():
    positions = list(range(1, 65))
    payload = {
        "progression_plan": {
            "planning_structure_version": 1,
            "requested_chapter_count": 64,
            "progression_arcs": [
                _arc("arc-001", 1, 32),
                {
                    **_arc("arc-002", 33, 64),
                    "growth": {
                        "cognition": "从只理解本地规则到理解区域协作",
                        "capability": None,
                        "resources": "获得可自主调配的稳定资源",
                        "activity_and_time_scale": "活动范围扩展到周边区域",
                    },
                },
            ],
        }
    }

    parsed, error = parse_progression(
        json.dumps(payload, ensure_ascii=False), positions
    )

    assert error is None
    assert parsed.progression_arcs[0].growth.model_dump() == {
        "cognition": None,
        "capability": None,
        "resources": None,
        "activity_and_time_scale": None,
    }
    assert parsed.progression_arcs[1].growth.capability is None


def test_arc_chapter_prompt_excludes_other_arc_details():
    first = _arc("arc-001", 1, 32)
    first["threads"] = [
        {
            "thread_id": "thread-long",
            "question": "来信来自谁",
            "open_position": 10,
            "payoff_position": 40,
            "payoff_intent": "确认来信来源",
        }
    ]
    second = {**_arc("arc-002", 33, 64), "title": "未来秘密阶段"}

    prompt = structured_arc_chapters_prompt(
        story_seed={"title": "长篇测试", "ending_direction": "完成选择"},
        progression_plan={"progression_arcs": [first, second]},
        arc=first,
        positions=list(range(1, 33)),
        is_final=False,
    )

    assert "thread-long" in prompt
    assert "未来秘密阶段" not in prompt
    assert "不要求每章升级" in prompt


def test_arc_batch_binds_planned_threads_without_kpis():
    first = _arc("arc-001", 1, 2)
    first["threads"] = [
        {
            "thread_id": "thread-letter",
            "question": "信来自谁",
            "open_position": 1,
            "payoff_position": 2,
            "payoff_intent": "确认来信人",
        }
    ]
    plan, error = parse_progression(
        json.dumps(
            {
                "progression_plan": {
                    "planning_structure_version": 1,
                    "requested_chapter_count": 2,
                    "progression_arcs": [first],
                }
            },
            ensure_ascii=False,
        ),
        [1, 2],
    )
    assert error is None
    output = {
        "chapters": [
            _chapter(1, ["thread-letter"], "收到匿名来信"),
            _chapter(2, [], "主角确认来信来自旧友"),
        ],
        "thread_payoffs": [
            {
                "thread_id": "thread-letter",
                "payoff_position": 2,
                "evidence_key_event": "主角确认来信来自旧友",
            }
        ],
    }

    parsed, error = parse_chapter_batch(
        json.dumps(output, ensure_ascii=False), plan.progression_arcs[0], plan
    )

    assert error is None
    chapters, payoffs = parsed
    assert len(chapters) == 2
    outline = StorySeedStructuredOutline.model_validate(
        {
            "status": "draft",
            "version": 1,
            "requested_chapter_count": 2,
            "planning_structure_version": 1,
            "progression_arcs": [first],
            "chapters": chapters,
            "thread_schedule_version": 1,
            "thread_payoffs": payoffs,
        }
    )
    assert outline.progression_arcs[0].growth.cognition is None


def _arc(arc_id: str, start: int, end: int) -> dict:
    return {
        "arc_id": arc_id,
        "title": f"第{start}至{end}章阶段",
        "start_position": start,
        "end_position": end,
        "narrative_goal": "推进当前阶段矛盾",
        "ending_state": "阶段选择发生变化",
        "growth": {
            "cognition": None,
            "capability": None,
            "resources": None,
            "activity_and_time_scale": None,
        },
        "major_entries": [],
        "world_scope_changes": [],
        "threads": [],
    }


def _chapter(position: int, open_threads: list[str], event: str) -> dict:
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": "推进当前选择",
        "key_events": [event],
        "character_focus": ["主角"],
        "open_threads": open_threads,
        "end_state": "形成下一步选择",
    }
