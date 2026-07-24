import json

from app.services.story.story_novel_ai_prompts import (
    chapter_gate_repair_prompt,
    chapter_length_repair_prompt,
    chapter_prompt,
)
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_generation_context import build_chapter_context
from app.services.story.story_novel_hard_context import build_hard_constraints
from tests.unit.test_story_novel_canon_state import _v2_revision
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_empty_canon_refs_keep_all_world_rules_without_future_canon(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    current = {**_plan_row(1), "canon_refs": []}
    future = {
        **_plan_row(2),
        "title": "FUTURE_CHAPTER_SECRET",
        "character_focus": ["FUTURE_ENTITY_SECRET"],
        "key_events": ["第二日 FUTURE_TIMELINE_SECRET"],
        "canon_refs": ["char-a", "time-future"],
        "timeline_event_bindings": {"time-future": "event-2"},
    }
    raw = _canon()
    raw["world_rules"] = [
        {
            "id": "rule-one",
            "statement": "KEEP_GLOBAL_WORLD_RULE_ONE",
            "exceptions": [],
        },
        {
            "id": "rule-two",
            "statement": "KEEP_GLOBAL_WORLD_RULE_TWO",
            "exceptions": [],
        },
    ]
    raw["timeline"].append(
        {
            "id": "time-future",
            "label": "第二日 FUTURE_TIMELINE_SECRET",
            "order": 2,
            "story_time": "第二日",
            "immutable": True,
            "source_chapter_position": 2,
            "source_key_event": "第二日 FUTURE_TIMELINE_SECRET",
        }
    )
    raw["entities"].append(
        {
            "id": "char-future",
            "kind": "character",
            "name": "FUTURE_ENTITY_SECRET",
            "aliases": [],
            "attributes": {},
        }
    )
    raw["milestones"].append(
        {
            "id": "milestone-future",
            "label": "FUTURE_MILESTONE_SECRET",
            "planned_position": 2,
            "repeatable": True,
            "outcomes": [],
        }
    )
    raw["character_arcs"][0]["checkpoints"] = [
        {"position": 2, "state": "FUTURE_ARC_SECRET"}
    ]
    canon = normalize_canon(raw)
    _v2_revision(revision, current)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [current, future],
    }
    revision.chapter_count = 2
    db_session.commit()

    context = build_chapter_context(service, revision, 1, current)["context"]
    compiled = context["hard_constraints"]["compiled_canon"]
    assert [item["id"] for item in compiled["world_rules"]] == [
        "rule-one",
        "rule-two",
    ]
    prompt = json.dumps(context, ensure_ascii=False)
    assert "KEEP_GLOBAL_WORLD_RULE_ONE" in prompt
    assert "KEEP_GLOBAL_WORLD_RULE_TWO" in prompt
    for secret in (
        "FUTURE_CHAPTER_SECRET",
        "FUTURE_TIMELINE_SECRET",
        "FUTURE_ENTITY_SECRET",
        "FUTURE_MILESTONE_SECRET",
        "FUTURE_ARC_SECRET",
    ):
        assert secret not in prompt


def test_static_world_context_is_visible_without_future_story_or_entity_fields():
    chapter = {
        **_plan_row(1),
        "canon_refs": ["time-current", "char-a", "loc-gate"],
        "key_events": ["民国二十三年腊月初七开场"],
        "timeline_event_bindings": {"time-current": "event-1"},
    }
    raw = _canon()
    raw["timeline"][0] = {
        "id": "time-current",
        "label": "民国二十三年腊月初七开场",
        "order": 1,
        "story_time": "民国二十三年腊月初七",
        "immutable": True,
        "source_chapter_position": 1,
        "source_key_event": "民国二十三年腊月初七开场",
    }
    raw["entities"][0]["attributes"] = {
        "age": 32,
        "occupation": "守桥人",
        "type": "人类",
        "hidden_identity": "FUTURE_HIDDEN_IDENTITY",
        "terminal_state": "FUTURE_TERMINAL_STATE",
    }
    canon = normalize_canon(raw)
    snapshot = {
        "title": "盐梁旧事",
        "genre": "历史悬疑",
        "setting_time": "民国二十三年冬",
        "setting_location": "西北盐梁镇",
        "target_audience": "成年读者",
        "story_format": "长篇小说",
        "premise": "FUTURE_PREMISE",
        "outline": "FUTURE_OUTLINE",
        "outline_text": "FUTURE_OUTLINE_TEXT",
        "structured_outline": {"chapters": ["FUTURE_STRUCTURED_OUTLINE"]},
        "central_conflict": "FUTURE_CENTRAL_CONFLICT",
        "main_conflict": "FUTURE_MAIN_CONFLICT",
        "ending_direction": "FUTURE_ENDING_DIRECTION",
        "resolution": "FUTURE_RESOLUTION",
        "story_seed": {
            "content_constraints": ["不得出现现代电子设备"],
            "premise": "FUTURE_SEED_PREMISE",
            "outline": "FUTURE_SEED_OUTLINE",
            "structured_outline": {"chapters": ["FUTURE_SEED_STRUCTURE"]},
            "central_conflict": "FUTURE_SEED_CONFLICT",
            "ending_direction": "FUTURE_SEED_ENDING",
        },
    }
    hard = build_hard_constraints(
        snapshot=snapshot,
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={"subjects": {}},
    )
    invariants = hard["story_invariants"]
    assert invariants == {
        "title": "盐梁旧事",
        "genre": "历史悬疑",
        "target_audience": "成年读者",
        "story_format": "长篇小说",
        "story_seed": {
            "content_constraints": ["不得出现现代电子设备"],
            "constraint_scope": "current_visible_only",
            "future_constraint_count_excluded": 0,
        },
    }
    entity = next(
        item for item in hard["compiled_canon"]["entities"] if item["id"] == "char-a"
    )
    assert entity["attributes"] == {
        "age": 32,
        "occupation": "守桥人",
        "type": "人类",
    }

    context = {"hard_constraints": hard}
    prompts = [
        chapter_prompt(context_pack=context, target_chars=4000),
        chapter_length_repair_prompt(
            context_pack=context,
            prior_result={"content_text": "旧稿", "plot_delta": {}},
            actual_chars=2,
            target_chars=4000,
        ),
        chapter_gate_repair_prompt(
            context_pack=context,
            prior_result=None,
            actual_chars=2,
            target_chars=4000,
            violations=[],
        ),
    ]
    future_secrets = (
        "FUTURE_PREMISE",
        "FUTURE_OUTLINE",
        "FUTURE_OUTLINE_TEXT",
        "FUTURE_STRUCTURED_OUTLINE",
        "FUTURE_CENTRAL_CONFLICT",
        "FUTURE_MAIN_CONFLICT",
        "FUTURE_ENDING_DIRECTION",
        "FUTURE_RESOLUTION",
        "FUTURE_SEED_PREMISE",
        "FUTURE_SEED_OUTLINE",
        "FUTURE_SEED_STRUCTURE",
        "FUTURE_SEED_CONFLICT",
        "FUTURE_SEED_ENDING",
        "FUTURE_HIDDEN_IDENTITY",
        "FUTURE_TERMINAL_STATE",
    )
    for prompt in prompts:
        assert "西北盐梁镇" not in prompt
        assert "民国二十三年冬" not in prompt
        assert "城门" in prompt
        assert "历史悬疑" in prompt
        assert "不得出现现代电子设备" in prompt
        assert "民国二十三年腊月初七" in prompt
        assert "不能据此推演或预告当前合同之外" in prompt
        assert "禁止自造未授权环境或未来目的地" in prompt
        assert "story_time 必须逐项原样写入正文" in prompt
        for secret in future_secrets:
            assert secret not in prompt


def test_global_time_and_location_are_excluded_from_chapter_context():
    chapter = {
        **_plan_row(1),
        "canon_refs": ["time-current"],
        "key_events": ["2174年8月3日，裴衡宣布九月二十日后季风窗口永久关闭"],
        "timeline_event_bindings": {"time-current": "event-1"},
    }
    raw = _canon()
    raw["timeline"][0] = {
        "id": "time-current",
        "label": "2174年8月3日，裴衡宣布九月二十日后季风窗口永久关闭",
        "order": 1,
        "story_time": "2174年8月3日",
        "immutable": True,
        "source_chapter_position": 1,
        "source_key_event": "2174年8月3日，裴衡宣布九月二十日后季风窗口永久关闭",
    }
    canon = normalize_canon(raw)
    hard = build_hard_constraints(
        snapshot={
            "title": "极昼邮路",
            "genre": "科幻",
            "setting_time": "2174年8月3日至9月21日，固定日历连续推进",
            "setting_location": "旱海六城",
            "story_seed": {"content_constraints": []},
        },
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={"subjects": {}},
    )

    serialized = json.dumps(hard, ensure_ascii=False)
    assert "setting_time" not in hard["story_invariants"]
    assert "setting_location" not in hard["story_invariants"]
    assert "9月21日" not in serialized
    assert "旱海六城" not in serialized
    assert "2174年8月3日" in serialized


def test_visible_subject_keeps_current_location_without_a_movement_contract():
    chapter = {**_plan_row(1), "canon_refs": ["char-a", "loc-gate"]}
    canon = normalize_canon(_canon())

    hard = build_hard_constraints(
        snapshot={"title": "当前章", "story_seed": {}},
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={
            "subjects": {
                "char-a": {
                    "location": "loc-gate",
                    "knowledge": [],
                    "hidden_identity": "FUTURE_SECRET",
                }
            }
        },
    )

    assert hard["current_state"]["subjects"]["char-a"] == {"location": "loc-gate"}
    assert hard["compiled_canon"]["initial_state"]["char-a"]["location"] == "loc-gate"
