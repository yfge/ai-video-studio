import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_state_validator import validate_state_delta
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_canon_reports_location_and_future_state_errors_together():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "loc-bridge",
            "kind": "location",
            "name": "断桥",
            "aliases": [],
            "attributes": {"status": "已毁"},
        }
    )
    canon_raw["initial_state"]["char-a"]["location"] = "loc-unknown"
    canon_raw["milestones"] = [
        {
            "id": "mile-bridge-destroyed",
            "label": "桥梁永久断裂",
            "planned_position": 3,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "loc-bridge",
                    "field": "status",
                    "operator": "eq",
                    "value": "已毁",
                }
            ],
        }
    ]

    with pytest.raises(ValueError) as exc_info:
        normalize_canon(canon_raw, required_gate_version=1)

    error = str(exc_info.value)
    assert "初始状态引用未知地点: ['loc-unknown']" in error
    assert "mile-bridge-destroyed loc-bridge.status" in error


def test_plan_requires_consumed_milestone_outcomes_to_land():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "obj-key",
            "kind": "object",
            "name": "唯一钥匙",
            "aliases": [],
            "attributes": {},
        }
    )
    canon_raw["initial_state"]["obj-key"] = {"owner_id": None}
    canon_raw["milestones"] = [
        {
            "id": "mile-key-transfer",
            "label": "钥匙移交",
            "planned_position": 1,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "obj-key",
                    "field": "owner_id",
                    "operator": "eq",
                    "value": "char-a",
                }
            ],
        }
    ]
    canon = normalize_canon(canon_raw)
    row = _plan_row(1)
    row["milestones_consumed"] = ["mile-key-transfer"]

    with pytest.raises(ValueError, match="eq 'char-a'"):
        validate_generation_plan(canon, [row])


def test_plan_and_body_gate_reject_future_outcome_before_its_chapter():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "obj-ticket",
            "kind": "object",
            "name": "车票",
            "aliases": [],
            "attributes": {},
        }
    )
    canon_raw["initial_state"]["obj-ticket"] = {"owner_id": None}
    canon_raw["milestones"] = [
        {
            "id": "mile-ticket-obtained",
            "label": "取得车票",
            "planned_position": 2,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "obj-ticket",
                    "field": "owner_id",
                    "operator": "eq",
                    "value": "char-a",
                }
            ],
        }
    ]
    canon = normalize_canon(canon_raw)
    row = _plan_row(1)
    early_transition = {
        "subject_id": "obj-ticket",
        "field": "owner_id",
        "from_value": None,
        "to_value": "char-a",
        "reason": "提前取得",
    }
    row["state_transitions"] = [early_transition]

    with pytest.raises(ValueError, match="提前包含未来里程碑结果"):
        validate_generation_plan(canon, [row])

    delta = {
        "occurred_event_ids": ["event-1"],
        "state_transitions": [early_transition],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
    }
    report, _state_after = validate_state_delta(
        canon, row, initial_story_state(canon), delta
    )
    assert any(
        "提前包含未来里程碑结果" in item["message"] for item in report["violations"]
    )


def test_plan_rejects_string_encoded_json_state_values():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "missing",
            "operator": "eq",
            "value": "null",
        }
    ]

    with pytest.raises(ValueError, match="真实 JSON 类型"):
        validate_generation_plan(canon, [row])


def test_plan_rejects_knowledge_inside_state_transitions():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "from_value": [],
            "to_value": ["fact-1"],
            "reason": "错误地重复授予知识",
        }
    ]

    with pytest.raises(ValueError, match="不能写入 state_transitions"):
        validate_generation_plan(canon, [row])


def test_plan_rejects_location_inside_state_transitions():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "location",
            "from_value": "loc-gate",
            "to_value": "loc-gate",
            "reason": "错误地重复地点变化",
        }
    ]

    with pytest.raises(ValueError, match="不能写入 state_transitions"):
        validate_generation_plan(canon, [row])


def test_state_validator_catches_reversion_and_illegal_knowledge():
    canon = normalize_canon(_canon())
    row = _plan_row()
    delta = {
        "occurred_event_ids": ["event-1"],
        "state_transitions": [
            {
                "subject_id": "char-a",
                "field": "status",
                "from_value": "已离开",
                "to_value": "返回",
            }
        ],
        "knowledge_grants": [
            {
                "character_id": "char-a",
                "fact_id": "future-fact",
                "source_event_id": "future-event",
            }
        ],
        "location_transitions": [],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
    }

    report, _state_after = validate_state_delta(
        canon, row, initial_story_state(canon), delta
    )
    assert {item["code"] for item in report["violations"]} == {
        "canon_violation",
        "state_reversion",
        "illegal_knowledge",
    }


def test_state_validator_rejects_unplanned_knowledge_from_current_event():
    canon = normalize_canon(_canon())
    row = _plan_row()
    delta = {
        "occurred_event_ids": ["event-1"],
        "knowledge_grants": [
            {
                "character_id": "char-a",
                "fact_id": "fact-current",
                "source_event_id": "event-1",
            }
        ],
    }

    report, _state_after = validate_state_delta(
        canon, row, initial_story_state(canon), delta
    )
    assert report["status"] == "failed"
    assert report["violations"] == [
        {
            "code": "illegal_knowledge",
            "message": (
                "正文出现未规划知识授予: ('char-a', 'fact-current', 'event-1')"
            ),
        }
    ]
