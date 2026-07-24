from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_plan_normalizer import (
    normalize_redundant_location_state,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _owned_object_canon():
    raw = _canon()
    raw["entities"].extend(
        [
            {
                "id": "char-source",
                "kind": "character",
                "name": "交付人",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-b",
                "kind": "location",
                "name": "船舱",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "obj-key",
                "kind": "object",
                "name": "钥匙",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    raw["initial_state"]["char-a"]["possessions"] = []
    raw["initial_state"]["char-source"] = {
        "location": "loc-gate",
        "knowledge": [],
        "possessions": ["obj-key"],
    }
    raw["initial_state"]["obj-key"] = {
        "location": "loc-gate",
        "owner_id": "char-source",
        "status": "sealed",
    }
    return normalize_canon(raw)


def test_new_owner_movement_drops_redundant_object_movement():
    canon = _owned_object_canon()
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "obj-key",
            "field": "owner_id",
            "from_value": "char-source",
            "to_value": "char-a",
            "reason": "公开交接",
        }
    ]
    row["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-b",
            "means": "登船",
        },
        {
            "subject_id": "obj-key",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-b",
            "means": "由新持有人携带",
        },
    ]

    normalized = normalize_redundant_location_state(canon, [row])

    assert normalized[0]["location_transitions"] == [row["location_transitions"][0]]
    validate_generation_plan(canon, normalized)


def test_same_location_object_movement_is_dropped():
    canon = _owned_object_canon()
    row = _plan_row(1)
    row["location_transitions"] = [
        {
            "subject_id": "obj-key",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-gate",
            "means": "原地归档",
        }
    ]

    normalized = normalize_redundant_location_state(canon, [row])

    assert normalized[0]["location_transitions"] == []
    validate_generation_plan(canon, normalized)
