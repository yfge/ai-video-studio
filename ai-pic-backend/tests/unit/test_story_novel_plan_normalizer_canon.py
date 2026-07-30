import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_plan_normalizer import (
    normalize_plan_payload,
    normalize_redundant_location_state,
)
from tests.unit.test_story_novel_longform import _canon as _longform_canon
from tests.unit.test_story_novel_longform import _plan_row


def _object_plan_canon():
    raw = _longform_canon()
    raw["entities"].append(
        {
            "id": "obj-evidence",
            "kind": "object",
            "name": "物证",
            "aliases": [],
            "attributes": {},
        }
    )
    raw["initial_state"]["char-a"]["possessions"] = []
    raw["initial_state"]["obj-evidence"] = {
        "status": "未发现",
        "location": None,
        "owner_id": None,
    }
    return normalize_canon(raw)


def test_normalizes_only_unambiguous_predicate_operator_aliases():
    row = _plan_row(1)
    row["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "location",
            "operator": "equals",
            "value": "loc-gate",
        },
        {
            "subject_id": "char-a",
            "field": "rank",
            "operator": "greater_than",
            "value": 1,
        },
        {
            "subject_id": "char-a",
            "field": "new_trial_status",
            "operator": "not_exists",
            "value": None,
        },
        {
            "subject_id": "char-a",
            "field": "rank",
            "operator": "not_exists",
            "value": 1,
        },
    ]

    normalized = normalize_plan_payload({"chapters": [row]})

    assert normalized["chapters"][0]["preconditions"][0]["operator"] == "eq"
    assert normalized["chapters"][0]["preconditions"][1]["operator"] == "greater_than"
    assert normalized["chapters"][0]["preconditions"][2]["operator"] == "eq"
    assert normalized["chapters"][0]["preconditions"][3]["operator"] == "not_exists"


def _owner_transition():
    return {
        "subject_id": "obj-evidence",
        "field": "owner_id",
        "from_value": None,
        "to_value": "char-a",
        "reason": "物证由甲保管",
    }


def _object_movement(target="loc-gate"):
    return {
        "subject_id": "obj-evidence",
        "from_location_id": None,
        "to_location_id": target,
        "means": "取得物证",
    }


def test_drops_null_movement_when_owner_transition_places_existing_object():
    canon = _object_plan_canon()
    row = _plan_row(1)
    row["state_transitions"] = [_owner_transition()]
    row["location_transitions"] = [_object_movement()]

    normalized = normalize_redundant_location_state(canon, [row])

    assert normalized[0]["location_transitions"] == []
    validate_generation_plan(canon, normalized)


def test_keeps_unsupported_null_movement_fail_closed():
    canon = _object_plan_canon()
    row = _plan_row(1)
    row["location_transitions"] = [_object_movement()]

    normalized = normalize_redundant_location_state(canon, [row])

    assert normalized[0]["location_transitions"] == [_object_movement()]
    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, normalized)


def test_owner_movement_carries_newly_owned_object_without_null_placement():
    raw = _longform_canon()
    raw["entities"].extend(
        [
            {
                "id": "obj-evidence",
                "kind": "object",
                "name": "物证",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-b",
                "kind": "location",
                "name": "乙地",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    raw["initial_state"]["char-a"]["possessions"] = []
    raw["initial_state"]["obj-evidence"] = {
        "status": "未发现",
        "location": None,
        "owner_id": None,
    }
    canon = normalize_canon(raw)
    row = _plan_row(1)
    row["state_transitions"] = [_owner_transition()]
    row["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-b",
            "means": "步行",
        },
        _object_movement("loc-b"),
    ]

    normalized = normalize_redundant_location_state(canon, [row])

    assert normalized[0]["location_transitions"] == [row["location_transitions"][0]]
    validate_generation_plan(canon, normalized)


def _identity_canon():
    raw = _longform_canon()
    raw["initial_state"]["char-a"].update({"identity": None, "occupation": "民间向导"})
    raw["milestones"] = [
        {
            "id": "mile-identity",
            "label": "身份公开",
            "planned_position": 1,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "identity",
                    "operator": "eq",
                    "value": "监察官继承人",
                }
            ],
        }
    ]
    return normalize_canon(raw)


def _misrouted_identity_reveal():
    row = _plan_row(1)
    row["milestones_consumed"] = ["mile-identity"]
    row["canon_refs"].append("mile-identity")
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "occupation",
            "from_value": "民间向导",
            "to_value": "监察官继承人",
            "reason": "身份公开",
        }
    ]
    return row


def test_does_not_guess_milestone_field_from_matching_value():
    canon = _identity_canon()
    source = _misrouted_identity_reveal()

    normalized = normalize_redundant_location_state(canon, [source])

    assert normalized[0]["state_transitions"] == source["state_transitions"]
    with pytest.raises(ValueError, match="里程碑结果未落地"):
        validate_generation_plan(canon, normalized)


def test_does_not_guess_precondition_field_from_matching_milestone_value():
    canon = _identity_canon()
    reveal = _plan_row(1)
    reveal["milestones_consumed"] = ["mile-identity"]
    reveal["canon_refs"].append("mile-identity")
    reveal["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "identity",
            "from_value": None,
            "to_value": "监察官继承人",
            "reason": "身份公开",
        }
    ]
    later = _plan_row(2)
    later["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "occupation",
            "operator": "eq",
            "value": "监察官继承人",
        }
    ]

    normalized = normalize_redundant_location_state(canon, [reveal, later])

    assert normalized[1]["preconditions"] == [
        {
            "subject_id": "char-a",
            "field": "occupation",
            "operator": "eq",
            "value": "监察官继承人",
        }
    ]
    with pytest.raises(ValueError, match="前置状态不连续"):
        validate_generation_plan(canon, normalized)
