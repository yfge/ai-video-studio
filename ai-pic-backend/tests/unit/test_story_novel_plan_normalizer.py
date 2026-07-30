from app.services.story.story_novel_plan_normalizer import (
    normalize_plan_payload,
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


def _chapter(transition=None, movements=None):
    return {
        "position": 1,
        "state_transitions": [transition] if transition else [],
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


def test_preserves_ordered_round_trip_to_initial_location():
    outbound = {
        "subject_id": "char-a",
        "from_location_id": "loc-a",
        "to_location_id": "loc-b",
        "means": "步行外出",
    }
    inbound = {
        "subject_id": "char-a",
        "from_location_id": "loc-b",
        "to_location_id": "loc-a",
        "means": "步行返回",
    }

    normalized = normalize_redundant_location_state(
        _canon(), [_chapter(movements=[outbound, inbound])]
    )

    assert normalized[0]["location_transitions"] == [outbound, inbound]


def test_normalizes_location_reason_alias_without_fabricating_means():
    normalized = normalize_plan_payload(
        {
            "chapters": [
                {
                    "location_transitions": [
                        {"subject_id": "char-a", "reason": "步行"},
                        {"subject_id": "char-a"},
                    ]
                }
            ]
        }
    )

    movements = normalized["chapters"][0]["location_transitions"]
    assert movements[0]["means"] == "步行"
    assert "means" not in movements[1]


def test_drops_misrouted_unknown_character_arrival_but_keeps_explicit_move():
    canon = _canon()
    canon["entities"].append(
        {"id": "char-b", "kind": "character", "name": "乙", "attributes": {}}
    )
    alias = {
        "subject_id": "char-b",
        "field": "location",
        "from_value": None,
        "to_value": "loc-a",
        "reason": "首次在场",
    }
    explicit = {
        "subject_id": "char-b",
        "from_location_id": None,
        "to_location_id": "loc-a",
        "means": "从未知地点来到甲地",
    }

    normalized = normalize_plan_payload(
        {"chapters": [_chapter(alias, [explicit])]}, canon
    )["chapters"][0]

    assert normalized["state_transitions"] == []
    assert normalized["location_transitions"] == [explicit]


def _owned_object_canon():
    canon = _canon()
    canon["entities"].append(
        {
            "id": "obj-a",
            "kind": "object",
            "name": "物件",
            "aliases": [],
            "attributes": {},
        }
    )
    canon["entities"].append(
        {
            "id": "loc-c",
            "kind": "location",
            "name": "丙地",
            "aliases": [],
            "attributes": {},
        }
    )
    canon["initial_state"]["char-a"]["possessions"] = ["obj-a"]
    canon["initial_state"]["obj-a"] = {
        "owner_id": "char-a",
        "location": "loc-a",
    }
    return canon


def _movement(subject_id, target="loc-b"):
    return {
        "subject_id": subject_id,
        "from_location_id": "loc-a",
        "to_location_id": target,
        "means": "同行",
    }


def test_drops_owned_object_movement_already_applied_by_owner_movement():
    owner_movement = _movement("char-a")
    object_movement = _movement("obj-a")
    chapter = _chapter(movements=[owner_movement, object_movement])

    normalized = normalize_redundant_location_state(_owned_object_canon(), [chapter])

    assert normalized[0]["location_transitions"] == [owner_movement]


def test_preserves_object_movement_when_owner_target_does_not_match():
    owner_movement = _movement("char-a")
    object_movement = _movement("obj-a", "loc-c")
    chapter = _chapter(movements=[owner_movement, object_movement])

    normalized = normalize_redundant_location_state(_owned_object_canon(), [chapter])

    assert normalized[0]["location_transitions"] == [
        owner_movement,
        object_movement,
    ]
