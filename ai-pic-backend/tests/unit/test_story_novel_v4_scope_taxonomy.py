import json

import pytest
from app.services.story.story_novel_arc_slot_contract import parse_arc_package
from app.services.story.story_novel_v4_scope_context import scope_world_context
from tests.unit.test_story_novel_v4_arc_slots import _arc_payload
from tests.unit.test_story_novel_v4_world_roadmap import _chapters


def test_arc_scope_slot_rejects_type_outside_story_taxonomy():
    target = {
        "start_position": 1,
        "end_position": 2,
        "character_slots": [],
        "scope_slots": [
            {
                "slot_id": "slot-new-range",
                "narrative_function": "扩大范围",
                "parent_scope_id": "scope-home",
                "mandatory": True,
            }
        ],
    }
    payload = _arc_payload()
    payload["character_slots"] = []
    payload["scope_slots"] = [
        {
            "slot_id": "slot-new-range",
            "first_appearance_position": 2,
            "name": "错误范围",
            "scope_type": "未授权类型",
            "depth": 1,
            "connection_type": "航线",
        }
    ]
    with pytest.raises(ValueError, match="未知 scope_type"):
        parse_arc_package(
            json.dumps(payload, ensure_ascii=False),
            _chapters(2),
            target,
            {
                "scope_taxonomy": [{"type_id": "起点"}],
                "scope_nodes": [
                    {"scope_id": "scope-home", "scope_type": "起点", "depth": 0}
                ],
            },
        )


def test_later_arc_exposes_prior_scope_slot_as_parent():
    context = scope_world_context(
        {"scope_graph": {"taxonomy": [{"type_id": "market"}], "nodes": []}},
        {
            "execution_context": {
                "state_before": {
                    "revision_local_entities": {
                        "scope-stable": {
                            "kind": "location",
                            "attributes": {
                                "slot_id": "slot-prior-market",
                                "scope_type": "market",
                                "depth": 0,
                            },
                        }
                    }
                }
            }
        },
    )
    assert context["scope_nodes"] == [
        {"scope_id": "slot-prior-market", "scope_type": "market", "depth": 0}
    ]
    target = {
        "start_position": 1,
        "end_position": 2,
        "character_slots": [],
        "scope_slots": [
            {
                "slot_id": "slot-next-market",
                "narrative_function": "扩大范围",
                "parent_scope_id": "slot-prior-market",
                "mandatory": True,
            }
        ],
    }
    payload = _arc_payload()
    payload["character_slots"] = []
    payload["scope_slots"] = [
        {
            "slot_id": "slot-next-market",
            "first_appearance_position": 2,
            "name": "新市场",
            "scope_type": "market",
            "depth": 1,
            "connection_type": "商路",
        }
    ]
    package = parse_arc_package(
        json.dumps(payload, ensure_ascii=False), _chapters(2), target, context
    )
    assert package["instantiated_scope_slots"][0]["parent_scope_id"] == (
        "slot-prior-market"
    )


def test_arc_scope_depth_is_server_derived_from_unique_taxonomy_parent():
    target = {
        "start_position": 1,
        "end_position": 2,
        "character_slots": [],
        "scope_slots": [
            {
                "slot_id": "slot-new-market",
                "narrative_function": "扩大范围",
                "parent_scope_id": None,
                "mandatory": True,
            }
        ],
    }
    payload = _arc_payload()
    payload["character_slots"] = []
    payload["scope_slots"] = [
        {
            "slot_id": "slot-new-market",
            "first_appearance_position": 2,
            "name": "新市场",
            "scope_type": "market",
            "depth": 99,
            "connection_type": "商路",
        }
    ]
    package = parse_arc_package(
        json.dumps(payload, ensure_ascii=False),
        _chapters(2),
        target,
        {
            "scope_taxonomy": [
                {"type_id": "home"},
                {"type_id": "market", "parent_type_id": "home"},
            ],
            "scope_nodes": [
                {"scope_id": "scope-home", "scope_type": "home", "depth": 0}
            ],
        },
    )
    slot = package["instantiated_scope_slots"][0]
    assert slot["parent_scope_id"] == "scope-home"
    assert slot["depth"] == 1


def test_arc_scope_parent_handle_is_restored_to_stable_scope_id():
    target = {
        "start_position": 1,
        "end_position": 2,
        "character_slots": [],
        "scope_slots": [
            {
                "slot_id": "slot-new-market",
                "narrative_function": "扩大范围",
                "mandatory": True,
            }
        ],
    }
    payload = _arc_payload()
    payload["character_slots"] = []
    payload["scope_slots"] = [
        {
            "slot_id": "slot-new-market",
            "first_appearance_position": 2,
            "name": "新市场",
            "scope_type": "market",
            "parent_scope_id": "S01",
            "connection_type": "商路",
        }
    ]
    package = parse_arc_package(
        json.dumps(payload, ensure_ascii=False),
        _chapters(2),
        target,
        {
            "scope_taxonomy": [
                {"type_id": "home"},
                {"type_id": "market", "parent_type_id": "home"},
            ],
            "scope_nodes": [
                {"scope_id": "scope-home", "scope_type": "home", "depth": 0}
            ],
            "scope_handles": {"S01": "scope-home"},
        },
    )
    assert package["instantiated_scope_slots"][0]["parent_scope_id"] == "scope-home"
