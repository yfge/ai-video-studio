from app.services.story.story_novel_plan_normalizer import (
    normalize_redundant_location_state,
)


def _canon():
    return {
        "entities": [
            {
                "id": "char-a",
                "kind": "character",
                "name": "甲",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-a",
                "kind": "location",
                "name": "甲地",
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
        ],
        "initial_state": {"char-a": {"location": "loc-a"}},
    }


def _chapter(transition, movements=None):
    return {
        "position": 1,
        "state_transitions": [transition],
        "location_transitions": movements or [],
    }


def test_removes_only_redundant_current_location_state():
    chapter = _chapter(
        {
            "subject_id": "char-a",
            "field": "location",
            "from_value": None,
            "to_value": "loc-a",
            "reason": "人物在当前地点首次出场",
        }
    )

    normalized = normalize_redundant_location_state(_canon(), [chapter])

    assert normalized[0]["state_transitions"] == []


def test_preserves_unrouted_real_location_change():
    transition = {
        "subject_id": "char-a",
        "field": "location",
        "from_value": "loc-a",
        "to_value": "loc-b",
        "reason": "真实移动却未使用 location_transitions",
    }

    normalized = normalize_redundant_location_state(_canon(), [_chapter(transition)])

    assert normalized[0]["state_transitions"] == [transition]


def test_removes_duplicate_when_explicit_movement_is_present():
    transition = {
        "subject_id": "char-a",
        "field": "location",
        "from_value": "loc-a",
        "to_value": "loc-b",
        "reason": "重复表达",
    }
    movement = {
        "subject_id": "char-a",
        "from_location_id": "loc-a",
        "to_location_id": "loc-b",
        "means": "步行",
    }

    normalized = normalize_redundant_location_state(
        _canon(), [_chapter(transition, [movement])]
    )

    assert normalized[0]["state_transitions"] == []
    assert normalized[0]["location_transitions"] == [movement]
