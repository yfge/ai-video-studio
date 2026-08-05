import json

import pytest
from app.services.story.story_novel_plan_semantic_audit import (
    _apply_missing_effects,
    _parse_audit,
)
from app.services.story.story_novel_plan_semantic_effects import (
    filter_redundant_audit_effects,
    remove_unsupported_effects,
)
from tests.unit.test_story_novel_plan_semantic_audit import _audit, _canon, _chapter


def test_semantic_audit_unwraps_only_exact_output_skeleton():
    wrapped = {"output_skeleton": _audit()}

    parsed = _parse_audit(json.dumps(wrapped), _canon(), [_chapter()])

    assert [item["event_id"] for item in parsed] == ["evt-ch8-1", "evt-ch8-2"]
    wrapped["comment"] = "extra"
    with pytest.raises(ValueError, match="未返回 events JSON"):
        _parse_audit(json.dumps(wrapped), _canon(), [_chapter()])


def test_semantic_audit_accepts_exact_top_level_event_array():
    parsed = _parse_audit(json.dumps(_audit()["events"]), _canon(), [_chapter()])

    assert [item["event_id"] for item in parsed] == ["evt-ch8-1", "evt-ch8-2"]


def test_semantic_audit_removes_only_exact_existing_unsupported_effects():
    chapter = _chapter()
    unsupported = {
        "subject_id": "char-wangming",
        "field": "status",
        "from_value": None,
        "to_value": "模型推测状态",
        "reason": "无大纲依据",
    }
    chapter["state_transitions"] = [unsupported]
    payload = _audit()
    for event in payload["events"]:
        event["unsupported_effects"] = {
            "knowledge_grants": [],
            "state_transitions": [unsupported],
            "location_transitions": [],
            "milestones_consumed": [],
        }

    parsed = _parse_audit(json.dumps(payload), _canon(), [chapter])
    patched, count = _apply_missing_effects([chapter], parsed)
    patched, removed = remove_unsupported_effects(patched, parsed)

    assert count == 0
    assert removed == 1
    assert patched[0]["state_transitions"] == []


def test_one_event_cannot_remove_a_chapter_level_milestone():
    chapter = _chapter()
    chapter["milestones_consumed"] = ["mile-1"]
    canon = _canon()
    canon["milestones"] = [
        {
            "id": "mile-1",
            "label": "试种权生效",
            "outcomes": [],
            "repeatable": False,
            "planned_position": 1,
        }
    ]
    payload = _audit()
    payload["events"][0]["unsupported_effects"] = {
        "knowledge_grants": [],
        "state_transitions": [],
        "location_transitions": [],
        "milestones_consumed": ["mile-1"],
    }

    parsed = _parse_audit(json.dumps(payload), canon, [chapter])
    patched, removed = remove_unsupported_effects([chapter], parsed)

    assert removed == 0
    assert patched[0]["milestones_consumed"] == ["mile-1"]


def test_same_state_transition_with_different_reason_is_not_added_twice():
    canon = _canon()
    canon["initial_state"]["char-wangming"]["status"] = "idle"
    chapter = _chapter()
    chapter["state_transitions"] = [
        {
            "subject_id": "char-wangming",
            "field": "status",
            "from_value": "idle",
            "to_value": "active",
            "reason": "计划中的原因",
        }
    ]
    payload = _audit()
    payload["events"][0]["missing_effects"]["state_transitions"] = [
        {
            **chapter["state_transitions"][0],
            "reason": "审计改写了原因但没有改变状态效果",
        }
    ]

    parsed = _parse_audit(json.dumps(payload), canon, [chapter])
    filtered = filter_redundant_audit_effects(parsed, canon, [], [chapter])

    assert filtered[0]["missing_effects"]["state_transitions"] == []


def test_event_state_chain_does_not_duplicate_existing_chapter_net_transition():
    canon = _canon()
    canon["entities"].append({"id": "obj-seed", "kind": "object", "name": "种袋"})
    canon["initial_state"]["obj-seed"] = {"status": "not-purchased"}
    chapter = _chapter()
    chapter["state_transitions"] = [
        {
            "subject_id": "obj-seed",
            "field": "status",
            "from_value": "not-purchased",
            "to_value": "purchased-and-sealed",
            "reason": "购入并封样",
        }
    ]
    payload = _audit()
    payload["events"][0]["missing_effects"]["state_transitions"] = [
        {
            "subject_id": "obj-seed",
            "field": "status",
            "from_value": "not-purchased",
            "to_value": "purchased",
            "reason": "购入",
        }
    ]
    payload["events"][1]["missing_effects"]["state_transitions"] = [
        {
            "subject_id": "obj-seed",
            "field": "status",
            "from_value": "purchased",
            "to_value": "purchased-and-sealed",
            "reason": "封样",
        }
    ]

    parsed = _parse_audit(json.dumps(payload), canon, [chapter])
    filtered = filter_redundant_audit_effects(parsed, canon, [], [chapter])

    assert all(not item["missing_effects"]["state_transitions"] for item in filtered)
