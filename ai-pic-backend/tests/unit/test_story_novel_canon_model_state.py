import json

import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    parse_model_canon,
)
from tests.unit.test_story_novel_longform import _canon


def _contract():
    return {
        "story_seed": {
            "structured_outline": {
                "chapters": [
                    {
                        "position": 1,
                        "key_events": ["第一日，发现线索"],
                    },
                    {
                        "position": 43,
                        "title": "木牌进公柜",
                        "goal": "公开存放水契木牌",
                        "key_events": ["沈禾将水契木牌交入合作社双锁公柜"],
                        "end_state": "木牌由公柜保管",
                    },
                ]
            },
            "world_constraints": [],
        }
    }


def _model_canon():
    raw = _canon()
    raw["entities"].extend(
        [
            {
                "id": "loc-village",
                "kind": "location",
                "name": "柳溪村",
                "aliases": [],
                "attributes": {"location_scope": "persistent"},
            },
            {
                "id": "loc-house",
                "kind": "location",
                "name": "沈禾旧屋",
                "aliases": [],
                "attributes": {
                    "location_scope": "scene",
                    "parent_location_id": "loc-village",
                },
            },
            {
                "id": "obj-water-deed",
                "kind": "object",
                "name": "水契木牌",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "obj-locker",
                "kind": "object",
                "name": "合作社双锁公柜",
                "aliases": ["公柜"],
                "attributes": {},
            },
        ]
    )
    raw["initial_state"]["char-a"]["location"] = "loc-house"
    raw["initial_state"]["char-a"]["possessions"] = ["obj-water-deed"]
    raw["initial_state"]["obj-water-deed"] = {
        "location": "char-a",
        "owner_id": "char-a",
        "status": "held",
    }
    raw["initial_state"]["obj-locker"] = {
        "location": "loc-house",
        "owner_id": None,
        "status": "not-built",
    }
    raw["milestones"] = [
        {
            "id": "mile-locker",
            "label": "水契木牌归入公柜",
            "planned_position": 43,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "obj-water-deed",
                    "field": "location",
                    "operator": "eq",
                    "value": "obj-locker",
                },
                {
                    "subject_id": "obj-water-deed",
                    "field": "owner_id",
                    "operator": "eq",
                    "value": None,
                },
            ],
        }
    ]
    return raw


def test_model_parser_compiles_owner_scene_absence_and_container_state():
    raw = _model_canon()

    canon, error, diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False), _contract()
    )

    assert error is None
    assert canon["initial_state"]["char-a"]["location"] == "loc-village"
    assert canon["initial_state"]["obj-water-deed"]["location"] is None
    assert canon["initial_state"]["obj-locker"] == {
        "location": None,
        "owner_id": None,
        "status": "absent",
    }
    assert canon["milestones"][0]["outcomes"] == [
        {
            "subject_id": "obj-water-deed",
            "field": "status",
            "operator": "eq",
            "value": "stored_in:obj-locker",
        },
        {
            "subject_id": "obj-water-deed",
            "field": "owner_id",
            "operator": "eq",
            "value": None,
        },
    ]
    assert {item["reason"] for item in diagnostics} >= {
        "container_location_compiled_to_status",
        "scene_location_mapped_to_persistent_parent",
        "owner_reference_removed_from_location",
        "absent_object_state_normalized",
    }
    with pytest.raises(ValueError):
        normalize_canon(raw)


def test_model_parser_does_not_hide_unregistered_location():
    raw = _model_canon()
    raw["initial_state"]["char-a"]["location"] = "loc-missing"

    canon, error, _diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False), _contract()
    )

    assert canon is None
    assert "初始状态引用未知地点" in error


def test_model_parser_promotes_only_an_orphan_scene_location():
    raw = _canon()
    raw["entities"].append(
        {
            "id": "loc-oxcart",
            "kind": "location",
            "name": "赶路牛车",
            "aliases": [],
            "attributes": {"location_scope": "scene"},
        }
    )

    canon, error, diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False), _contract()
    )

    assert error is None
    entity = next(item for item in canon["entities"] if item["id"] == "loc-oxcart")
    assert entity["attributes"] == {}
    assert {
        "id": "loc-oxcart",
        "section": "entities",
        "reason": "orphan_scene_promoted_to_persistent",
    } in diagnostics
    with pytest.raises(ValueError, match="scene 地点缺少 parent_location_id"):
        normalize_canon(raw)
