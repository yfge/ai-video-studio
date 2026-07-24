import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_state_validator import validate_state_delta
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _delta(chapter):
    return {
        "occurred_event_ids": list(chapter["required_event_ids"]),
        "premature_future_event_ids": [],
        "state_transitions": list(chapter["state_transitions"]),
        "knowledge_grants": [],
        "location_transitions": list(chapter["location_transitions"]),
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
    }


def test_plan_and_runtime_replay_ordered_non_null_movements():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "loc-vault",
            "kind": "location",
            "name": "档案库",
            "aliases": [],
            "attributes": {},
        }
    )
    canon = normalize_canon(canon_raw)
    chapter = _plan_row(1)
    chapter["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-vault",
            "means": "步行进入档案库",
        },
        {
            "subject_id": "char-a",
            "from_location_id": "loc-vault",
            "to_location_id": "loc-gate",
            "means": "核验后步行返回",
        },
    ]

    validate_generation_plan(canon, [chapter])
    report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert report["status"] == "passed"
    assert state_after["subjects"]["char-a"]["location"] == "loc-gate"


def test_plan_and_runtime_replay_ordered_state_transitions():
    canon = normalize_canon(_canon())
    chapter = _plan_row(1)
    chapter["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "from_value": "守规",
            "to_value": "动摇",
            "reason": "证据冲击信念",
        },
        {
            "subject_id": "char-a",
            "field": "status",
            "from_value": "动摇",
            "to_value": "决断",
            "reason": "选择继续追查",
        },
    ]

    validate_generation_plan(canon, [chapter])
    report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert report["status"] == "passed"
    assert state_after["subjects"]["char-a"]["status"] == "决断"


def test_owner_transfer_location_side_effect_matches_plan_and_runtime():
    canon_raw = _canon()
    canon_raw["entities"].extend(
        [
            {
                "id": "char-b",
                "kind": "character",
                "name": "档案员",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "obj-x",
                "kind": "object",
                "name": "证物",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-vault",
                "kind": "location",
                "name": "档案库",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-final",
                "kind": "location",
                "name": "终档室",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    canon_raw["initial_state"].update(
        {
            "char-a": {
                **canon_raw["initial_state"]["char-a"],
                "possessions": ["obj-x"],
            },
            "char-b": {"location": "loc-vault", "possessions": []},
            "obj-x": {"owner_id": "char-a", "location": "loc-gate"},
        }
    )
    canon = normalize_canon(canon_raw)
    chapter = _plan_row(1)
    chapter["state_transitions"] = [
        {
            "subject_id": "obj-x",
            "field": "owner_id",
            "from_value": "char-a",
            "to_value": "char-b",
            "reason": "证物完成交接",
        }
    ]
    chapter["location_transitions"] = [
        {
            "subject_id": "obj-x",
            "from_location_id": "loc-vault",
            "to_location_id": "loc-final",
            "means": "档案员将证物转入终档室",
        }
    ]

    validate_generation_plan(canon, [chapter])
    report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert report["status"] == "passed"
    assert state_after["subjects"]["obj-x"] == {
        "owner_id": "char-b",
        "location": "loc-final",
    }


def test_noop_owner_transition_cannot_create_an_unplanned_location_change():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "obj-x",
            "kind": "object",
            "name": "证物",
            "aliases": [],
            "attributes": {},
        }
    )
    canon_raw["initial_state"]["char-a"]["possessions"] = ["obj-x"]
    canon_raw["initial_state"]["obj-x"] = {
        "owner_id": "char-a",
        "location": None,
    }
    canon = normalize_canon(canon_raw)
    chapter = _plan_row(1)
    chapter["state_transitions"] = [
        {
            "subject_id": "obj-x",
            "field": "owner_id",
            "from_value": "char-a",
            "to_value": "char-a",
            "reason": "伪造一次无变化交接",
        }
    ]

    with pytest.raises(ValueError, match="状态转移起终值相同"):
        validate_generation_plan(canon, [chapter])
    report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert report["status"] == "failed"
    assert any(item["code"] == "canon_violation" for item in report["violations"])
    assert state_after["subjects"]["obj-x"]["location"] is None
