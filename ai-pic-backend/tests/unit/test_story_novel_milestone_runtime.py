from copy import deepcopy

import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_milestone_effect_compiler import (
    compile_milestone_effects,
)
from app.services.story.story_novel_milestone_state import (
    validate_consumed_milestone_outcomes,
    validate_future_milestone_outcomes,
)
from pydantic import ValidationError
from tests.unit.test_story_novel_milestone_outcomes import _canon


def test_legacy_canon_remains_normalizable_but_cannot_claim_gate_v1():
    legacy = _canon()
    legacy.pop("gate_version")
    for milestone in legacy["milestones"]:
        milestone.pop("outcomes")

    normalized = normalize_canon(legacy)
    assert normalized["gate_version"] == 0
    with pytest.raises(ValueError, match="gate_version"):
        normalize_canon(legacy, required_gate_version=CANON_GATE_VERSION)


def test_gate_v1_requires_outcomes_and_known_subjects():
    missing = _canon()
    missing["milestones"][0]["outcomes"] = []
    with pytest.raises(ValueError, match="缺少 outcomes"):
        normalize_canon(missing, required_gate_version=CANON_GATE_VERSION)

    unknown = _canon()
    unknown["milestones"][0]["outcomes"][0]["subject_id"] = "obj-unknown"
    with pytest.raises(ValueError, match="未知实体"):
        normalize_canon(unknown, required_gate_version=CANON_GATE_VERSION)


def test_gate_v1_rejects_unknown_owner_outcome_target():
    invalid = _canon()
    invalid["milestones"][0]["outcomes"][0]["value"] = "char-not-exist"

    with pytest.raises(ValueError, match="owner_id 指向非法所有者"):
        normalize_canon(invalid, required_gate_version=CANON_GATE_VERSION)


def test_milestone_outcome_operator_is_limited_to_eq_and_contains():
    invalid = _canon()
    invalid["milestones"][0]["outcomes"][0]["operator"] = "ne"

    with pytest.raises(ValidationError):
        normalize_canon(invalid)


@pytest.mark.parametrize("encoded_value", ["null", " NULL ", "[]", " {} "])
def test_gate_v1_rejects_json_containers_encoded_as_strings(encoded_value: str):
    invalid = _canon()
    invalid["milestones"][0]["outcomes"][0]["value"] = encoded_value

    with pytest.raises(ValueError, match="真实 JSON"):
        normalize_canon(invalid, required_gate_version=CANON_GATE_VERSION)


def test_future_and_consumed_helpers_share_the_same_outcome_contract():
    canon = normalize_canon(_canon(), required_gate_version=CANON_GATE_VERSION)
    subjects = deepcopy(canon["initial_state"])
    subjects["obj-zero-wind-key"]["owner_id"] = "char-li-yan"

    validate_consumed_milestone_outcomes(
        canon,
        subjects,
        ["mile-key-transfer"],
        current_position=1,
    )
    with pytest.raises(ValueError, match="mile-ticket-obtained"):
        early = deepcopy(subjects)
        early["obj-ticket-18h"]["owner_id"] = "char-li-yan"
        validate_future_milestone_outcomes(
            canon,
            early,
            current_position=1,
        )

    with pytest.raises(ValueError, match="结果未落地"):
        validate_consumed_milestone_outcomes(
            canon,
            canon["initial_state"],
            ["mile-key-transfer"],
            current_position=1,
        )


def test_relationship_contains_outcome_compiles_and_validates_as_mapping():
    canon = {
        "entities": [
            {"id": "char-a", "kind": "character", "name": "甲"},
            {"id": "char-b", "kind": "character", "name": "乙"},
        ],
        "milestones": [
            {
                "id": "mile-partners",
                "planned_position": 2,
                "repeatable": False,
                "outcomes": [
                    {
                        "subject_id": "char-a",
                        "field": "relationships",
                        "operator": "contains",
                        "value": "business-partner:char-b",
                    }
                ],
            }
        ],
    }
    subjects = {
        "char-a": {"relationships": {"char-c": "trusted:char-c"}},
        "char-b": {"relationships": {}},
    }
    chapter = {
        "position": 2,
        "required_event_ids": ["event-2-1"],
        "milestones_consumed": ["mile-partners"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
    }

    compiled = compile_milestone_effects(canon, chapter, subjects)

    assert compiled["state_transitions"] == [
        {
            "subject_id": "char-a",
            "field": "relationships",
            "from_value": {"char-c": "trusted:char-c"},
            "to_value": {
                "char-c": "trusted:char-c",
                "char-b": "business-partner:char-b",
            },
            "reason": "Canon milestone mile-partners",
        }
    ]
    after = deepcopy(subjects)
    after["char-a"]["relationships"] = compiled["state_transitions"][0]["to_value"]
    validate_consumed_milestone_outcomes(
        canon, after, ["mile-partners"], current_position=2
    )


def test_non_relationship_mapping_contains_outcome_stays_invalid():
    canon = {
        "milestones": [
            {
                "id": "mile-invalid",
                "outcomes": [
                    {
                        "subject_id": "concept-a",
                        "field": "status",
                        "operator": "contains",
                        "value": "active",
                    }
                ],
            }
        ]
    }
    chapter = {
        "milestones_consumed": ["mile-invalid"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
    }

    with pytest.raises(ValueError, match="目标不是数组"):
        compile_milestone_effects(
            canon, chapter, {"concept-a": {"status": {"phase": "old"}}}
        )
