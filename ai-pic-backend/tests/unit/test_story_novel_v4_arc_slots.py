import json

import pytest
from app.services.story.story_novel_arc_slot_contract import parse_arc_package
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_planner_slot_visibility import (
    authorized_entity_slots,
)
from tests.unit.test_story_novel_v4_snapshot import _response, _snapshot
from tests.unit.test_story_novel_v4_world_roadmap import _chapters


def _target():
    return {
        "arc_id": "arc-1",
        "start_position": 1,
        "end_position": 2,
        "character_slots": [
            {
                "slot_id": "slot-rival",
                "narrative_function": "当前范围的持续竞争者",
                "relationship_target": "char-real-id",
                "mandatory": True,
            }
        ],
        "scope_slots": [],
    }


def _arc_payload():
    chapters = _chapters(2)
    return {
        "chapters": [
            {
                key: row[key]
                for key in (
                    "position",
                    "title",
                    "goal",
                    "key_events",
                    "character_focus",
                    "open_threads",
                    "end_state",
                )
            }
            for row in chapters
        ],
        "character_slots": [
            {
                "slot_id": "slot-rival",
                "first_appearance_position": 2,
                "name": "迟岚",
                "profile": "熟悉当前市场的年轻竞争者",
                "relationship": "公开竞争",
                "capabilities": ["议价"],
                "resources": ["本地渠道"],
                "knowledge_boundary": ["只了解当前市场"],
                "arc_direction": "竞争中形成相互认可",
            }
        ],
        "scope_slots": [],
    }


def test_arc_planner_instantiates_mandatory_slot_and_reveals_it_only_on_entry():
    package = parse_arc_package(
        json.dumps(_arc_payload(), ensure_ascii=False), _chapters(2), _target()
    )
    plan = {"current_arc_plan": {**_target(), **package}}
    assert authorized_entity_slots(plan, 1, {"char-real-id": "C01"}) == []
    visible = authorized_entity_slots(plan, 2, {"char-real-id": "C01"})
    assert visible[0]["name"] == "迟岚"
    assert visible[0]["mandatory"] is True
    assert visible[0]["relationship_target_handle"] == "C01"


def test_arc_planner_cannot_omit_mandatory_slot():
    payload = _arc_payload()
    payload["character_slots"] = []
    with pytest.raises(ValueError, match="mandatory"):
        parse_arc_package(
            json.dumps(payload, ensure_ascii=False), _chapters(2), _target()
        )


def test_chapter_intent_must_copy_frozen_arc_slot_without_rewriting_it():
    snapshot = _snapshot()
    slot = parse_arc_package(
        json.dumps(_arc_payload(), ensure_ascii=False), _chapters(2), _target()
    )["instantiated_character_slots"][0]
    snapshot["model_input"]["authorized_entity_slots"] = [
        {**slot, "relationship_target_handle": "C01"}
    ]
    from app.services.story.story_novel_context_utils import value_hash

    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash")
    snapshot["snapshot_hash"] = value_hash(snapshot)
    payload = json.loads(_response())
    payload["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "slot_id": "slot-rival",
            "kind": "character",
            "name": "迟岚",
            "aliases": [],
            "narrative_function": "当前范围的持续竞争者",
            "source_event_handle": "E01",
            "transient": False,
            "profile": "熟悉当前市场的年轻竞争者",
            "relationship_intents": [
                {"target_handle": "C01", "relationship": "公开竞争"}
            ],
            "capabilities": ["议价"],
            "resources": ["本地渠道"],
            "knowledge_boundary": ["只了解当前市场"],
            "arc_direction": "竞争中形成相互认可",
            "attributes": {},
        }
    ]
    assert (
        parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)[
            "entity_proposals"
        ][0]["slot_id"]
        == "slot-rival"
    )
    payload["entity_proposals"][0]["name"] = "改名"
    with pytest.raises(ValueError, match="Arc slot"):
        parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)


def test_scope_slot_freezes_custom_hierarchy_and_connection():
    target = {
        "arc_id": "arc-1",
        "start_position": 1,
        "end_position": 2,
        "character_slots": [],
        "scope_slots": [
            {
                "slot_id": "slot-new-range",
                "narrative_function": "扩大当前活动范围",
                "parent_scope_id": "scope-home",
                "scale_direction": "broader",
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
            "name": "远港",
            "scope_type": "贸易节点",
            "depth": 1,
            "connection_type": "航线",
        }
    ]
    package = parse_arc_package(
        json.dumps(payload, ensure_ascii=False),
        _chapters(2),
        target,
        {
            "scope_taxonomy": [
                {"type_id": "起点", "display_name": "起点"},
                {
                    "type_id": "贸易节点",
                    "display_name": "贸易节点",
                    "parent_type_id": "起点",
                },
            ],
            "scope_nodes": [
                {
                    "scope_id": "scope-home",
                    "scope_type": "起点",
                    "depth": 0,
                }
            ],
        },
    )
    plan = {
        "canon": {"entities": [{"id": "scope-home", "name": "故地"}]},
        "current_arc_plan": {**target, **package},
    }
    slot = authorized_entity_slots(plan, 2, {"scope-home": "S01"})[0]
    assert slot["parent_scope_handle"] == "S01"

    snapshot = _snapshot()
    snapshot["model_input"]["scope_taxonomy"] = [
        {"type_id": "起点", "display_name": "起点"},
        {"type_id": "贸易节点", "display_name": "贸易节点", "parent_type_id": "起点"},
    ]
    snapshot["model_input"]["visible_characters_and_world"].append(
        {
            "entity_handle": "S01",
            "kind": "location",
            "name": "故地",
            "aliases": [],
            "attributes": {"scope_type": "起点", "depth": 0},
            "current_state": {},
        }
    )
    snapshot["model_input"]["allowed_entity_handles"].append("S01")
    snapshot["model_input"]["authorized_entity_slots"] = [slot]
    from app.services.story.story_novel_context_utils import value_hash

    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash")
    snapshot["snapshot_hash"] = value_hash(snapshot)
    intent = json.loads(_response())
    intent["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "slot_id": "slot-new-range",
            "kind": "location",
            "name": "远港",
            "aliases": [],
            "narrative_function": "扩大当前活动范围",
            "source_event_handle": "E01",
            "transient": False,
            "attributes": {
                "scope_type": "贸易节点",
                "parent_scope_id": "S01",
                "depth": 1,
                "connections": [{"to_scope_id": "S01", "connection_type": "航线"}],
            },
        }
    ]
    parsed = parse_chapter_intent(json.dumps(intent, ensure_ascii=False), snapshot)
    assert parsed["entity_proposals"][0]["attributes"]["scope_type"] == "贸易节点"
    intent["entity_proposals"][0]["attributes"]["depth"] = 2
    with pytest.raises(ValueError, match="层级合同"):
        parse_chapter_intent(json.dumps(intent, ensure_ascii=False), snapshot)
