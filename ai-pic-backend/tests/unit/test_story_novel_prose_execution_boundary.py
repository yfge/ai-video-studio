import json

from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_v3_context import build_v3_prose_input


def test_new_prose_contract_exposes_exhaustive_current_effects_and_phases():
    chapter = _chapter()
    state = {
        "subjects": {
            "char-a": {"location": "loc-county"},
            "char-b": {"location": "loc-county"},
        },
        "threads": {},
    }
    context = _context(chapter, state, boundary_version=1)

    result = build_v3_prose_input(context, _brief(), chapter)
    boundary = result["current_chapter_context"]["typed_execution_boundary"]

    assert boundary == {
        "schema": "story_novel_prose_execution_boundary.v1",
        "effects_are_exhaustive": True,
        "free_text_conflict_rule": "typed_effects_and_action_phase_win",
        "action_phase_semantics": {
            "instant": "本章发生该瞬时事件，不扩写后续结果",
            "start": "本章只启动行动，不得写成完成、到达或取得最终结果",
            "progress": "本章只推进过程，不得写成完成或取得最终结果",
            "complete": "本章完整完成事件，但不得追加合同外后果",
        },
        "state_transitions": [],
        "entity_introductions": [],
        "location_transitions": [],
        "knowledge_grants": chapter["knowledge_grants"],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "unchanged_location_subject_ids": ["char-a", "char-b"],
    }
    assert result["current_chapter_context"]["events"][1]["execution"] == {
        "action_phase": "start",
        "actor_ids": ["char-a", "char-b"],
    }
    surface = json.dumps(result, ensure_ascii=False)
    assert "future-event" not in surface


def test_location_transition_removes_only_the_moving_actor_from_stay_boundary():
    chapter = _chapter()
    chapter["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-county",
            "to_location_id": "loc-village",
            "means": "乘车",
        }
    ]
    state = {
        "subjects": {
            "char-a": {"location": "loc-county"},
            "char-b": {"location": "loc-county"},
        },
        "threads": {},
    }

    boundary = build_v3_prose_input(
        _context(chapter, state, boundary_version=1), _brief(), chapter
    )["current_chapter_context"]["typed_execution_boundary"]

    assert boundary["location_transitions"] == chapter["location_transitions"]
    assert boundary["unchanged_location_subject_ids"] == ["char-b"]


def test_historical_prose_contract_does_not_retroactively_change_prompt_hash():
    chapter = _chapter()
    state = {
        "subjects": {
            "char-a": {"location": "loc-county"},
            "char-b": {"location": "loc-county"},
        },
        "threads": {},
    }

    result = build_v3_prose_input(_context(chapter, state), _brief(), chapter)

    assert "typed_execution_boundary" not in result["current_chapter_context"]


def _context(chapter, state, boundary_version=0):
    brief_input = {
        "hard_constraints": {"story_invariants": {"genre": "剧情"}},
        "expected_delta": compile_expected_delta(chapter, state),
    }
    if boundary_version:
        brief_input["prose_execution_boundary_version"] = boundary_version
    hard = {
        "compiled_canon": {
            "entities": [
                {"id": "char-a", "kind": "character", "name": "甲"},
                {"id": "char-b", "kind": "character", "name": "乙"},
            ],
            "world_rules": [],
        },
        "current_state": state,
    }
    return {"brief_input": brief_input, "hard_constraints": hard}


def _chapter():
    return {
        "position": 23,
        "required_event_ids": ["event-23-1", "event-23-2"],
        "key_events": ["县吏提高证据门槛", "二人开始准备回村取证"],
        "character_focus": ["甲", "乙"],
        "execution_contracts": [
            {
                "event_id": "event-23-1",
                "action_phase": "instant",
                "actor_ids": ["char-a", "char-b"],
            },
            {
                "event_id": "event-23-2",
                "action_phase": "start",
                "actor_ids": ["char-a", "char-b"],
            },
        ],
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [
            {
                "character_id": "char-a",
                "fact_id": "fact-evidence-threshold",
                "source_event_id": "event-23-1",
            }
        ],
        "milestones_consumed": [],
        "open_threads": [],
        "payoffs_due": [],
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
    }


def _brief():
    return {
        "beats": [
            {
                "beat_id": "B01",
                "allowed_entity_ids": ["char-a", "char-b"],
            }
        ],
        "character_motivations": [],
    }
