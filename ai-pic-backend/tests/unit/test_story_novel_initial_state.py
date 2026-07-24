import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_initial_state import canonical_initial_subjects
from app.services.story.story_novel_state_service import initial_story_state
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_entity_attributes_fill_missing_initial_fields():
    value = _canon()
    value["entities"][0]["attributes"] = {
        "status": "已死亡",
        "profile": {"origin": "旱海", "rank": "旧值"},
    }
    value["initial_state"]["char-a"].pop("status")
    value["initial_state"]["char-a"]["profile"] = {"rank": "显式值"}
    canon = normalize_canon(value)

    subjects = canonical_initial_subjects(canon)
    assert subjects["char-a"]["status"] == "已死亡"
    assert subjects["char-a"]["profile"] == {
        "origin": "旱海",
        "rank": "显式值",
    }
    assert initial_story_state(canon)["subjects"] == subjects


def test_plan_precondition_reads_static_entity_attribute():
    value = _canon()
    value["entities"][0]["attributes"] = {"status": "已死亡"}
    value["initial_state"]["char-a"].pop("status")
    canon = normalize_canon(value)
    row = _plan_row()
    row["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "已死亡",
        }
    ]

    validate_generation_plan(canon, [row])


def test_future_milestone_outcome_cannot_hide_in_entity_attributes():
    value = _canon()
    value["gate_version"] = CANON_GATE_VERSION
    value["entities"][0]["attributes"] = {"status": "已公开"}
    value["initial_state"]["char-a"].pop("status")
    value["milestones"] = [
        {
            "id": "mile-reveal",
            "label": "身份公开",
            "planned_position": 2,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "status",
                    "operator": "eq",
                    "value": "已公开",
                }
            ],
        }
    ]

    with pytest.raises(ValueError, match="状态提前包含未来里程碑结果"):
        normalize_canon(value, required_gate_version=CANON_GATE_VERSION)


def test_explicit_initial_state_overrides_static_attribute():
    value = _canon()
    value["gate_version"] = CANON_GATE_VERSION
    value["entities"][0]["attributes"] = {"status": "已公开"}
    value["initial_state"]["char-a"]["status"] = "未公开"
    value["milestones"] = [
        {
            "id": "mile-reveal",
            "label": "身份公开",
            "planned_position": 2,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "status",
                    "operator": "eq",
                    "value": "已公开",
                }
            ],
        }
    ]

    canon = normalize_canon(value, required_gate_version=CANON_GATE_VERSION)
    assert canonical_initial_subjects(canon)["char-a"]["status"] == "未公开"
