import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_plan_normalizer import (
    normalize_plan_payload,
    normalize_redundant_location_state,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _hierarchical_canon():
    raw = _canon()
    raw["entities"].extend(
        [
            {
                "id": "loc-station",
                "kind": "location",
                "name": "白砾站",
                "aliases": [],
                "attributes": {"location_scope": "persistent"},
            },
            {
                "id": "loc-warehouse",
                "kind": "location",
                "name": "折射仓库",
                "aliases": [],
                "attributes": {
                    "location_scope": "scene",
                    "parent_location_id": "loc-station",
                },
            },
            {
                "id": "loc-sledge",
                "kind": "location",
                "name": "缆车",
                "aliases": [],
                "attributes": {"location_scope": "persistent"},
            },
        ]
    )
    raw["initial_state"]["char-a"]["location"] = "loc-station"
    return normalize_canon(raw)


def test_scene_location_requires_a_valid_acyclic_parent():
    raw = _canon()
    raw["entities"].append(
        {
            "id": "loc-room",
            "kind": "location",
            "name": "内室",
            "aliases": [],
            "attributes": {"location_scope": "scene"},
        }
    )

    with pytest.raises(ValueError, match="scene 地点缺少 parent_location_id"):
        normalize_canon(raw)


def test_scene_location_cannot_be_a_durable_initial_location():
    raw = _hierarchical_canon()
    raw.pop("canon_hash")
    raw["initial_state"]["char-a"]["location"] = "loc-warehouse"

    with pytest.raises(ValueError, match="初始持久地点不能引用 scene"):
        normalize_canon(raw)


def test_milestone_location_must_reference_a_registered_location():
    raw = _canon()
    raw["milestones"].append(
        {
            "id": "mile-archive",
            "label": "归档",
            "planned_position": 1,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "location",
                    "operator": "eq",
                    "value": "unregistered-locker",
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="里程碑引用未知地点"):
        normalize_canon(raw)


def test_internal_scene_visit_does_not_break_later_persistent_location_chain():
    canon = _hierarchical_canon()
    visit = _plan_row(1)
    visit["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "location",
            "operator": "eq",
            "value": "loc-station",
        }
    ]
    visit["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-station",
            "to_location_id": "loc-warehouse",
            "means": "进入站内仓库",
        }
    ]
    depart = _plan_row(2)
    depart["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "location",
            "operator": "eq",
            "value": "loc-station",
        }
    ]
    depart["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-station",
            "to_location_id": "loc-sledge",
            "means": "登上缆车",
        }
    ]

    normalized = normalize_redundant_location_state(canon, [visit, depart])

    assert normalized[0]["location_transitions"] == []
    assert normalized[1]["location_transitions"] == depart["location_transitions"]
    validate_generation_plan(canon, normalized)


def test_null_or_blank_movement_destination_is_removed_before_schema_validation():
    payload = normalize_plan_payload(
        {
            "chapters": [
                {
                    "location_transitions": [
                        {
                            "subject_id": "char-a",
                            "from_location_id": "loc-gate",
                            "to_location_id": None,
                            "means": "没有实际移动",
                        },
                        {
                            "subject_id": "char-a",
                            "from_location_id": "loc-gate",
                            "to_location_id": "loc-station",
                            "means": "步行",
                        },
                    ]
                }
            ]
        }
    )

    assert payload["chapters"][0]["location_transitions"] == [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-station",
            "means": "步行",
        }
    ]


def test_unique_expanded_provider_location_id_maps_to_canon_location():
    canon = _hierarchical_canon()
    canon["entities"].append(
        {
            "id": "loc-south-field",
            "kind": "location",
            "name": "南坡地",
            "aliases": [],
            "attributes": {},
        }
    )
    chapter = _plan_row(1)
    chapter["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-station",
            "to_location_id": "loc-south-slope-field",
            "means": "步行",
        }
    ]

    normalized = normalize_redundant_location_state(canon, [chapter])

    assert normalized[0]["location_transitions"][0]["to_location_id"] == (
        "loc-south-field"
    )


def test_ambiguous_expanded_provider_location_id_remains_fail_closed():
    canon = _hierarchical_canon()
    canon["entities"].extend(
        [
            {
                "id": "loc-south-field",
                "kind": "location",
                "name": "南坡地",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-slope-field",
                "kind": "location",
                "name": "坡地",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    chapter = _plan_row(1)
    chapter["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-station",
            "to_location_id": "loc-south-slope-field",
            "means": "步行",
        }
    ]

    normalized = normalize_redundant_location_state(canon, [chapter])

    assert normalized[0]["location_transitions"][0]["to_location_id"] == (
        "loc-south-slope-field"
    )
    with pytest.raises(ValueError, match="Canon locations"):
        validate_generation_plan(canon, normalized)
