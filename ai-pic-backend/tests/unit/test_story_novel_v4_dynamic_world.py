import json

import pytest
from app.services.story.story_novel_chapter_contract_v4 import compile_intent_contract
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_scope_graph import initial_scope_graph
from app.services.story.story_novel_state_service import apply_state_delta
from app.services.story.story_novel_v4_prose_input import build_v4_prose_input
from tests.unit.test_story_novel_v4_snapshot import _response, _skeleton, _snapshot


def test_persistent_character_enters_revision_world_only_after_delta_application():
    snapshot = _snapshot()
    payload = json.loads(_response())
    payload["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "kind": "character",
            "name": "闻鹿",
            "aliases": [],
            "narrative_function": "后续持续合作的向导",
            "source_event_handle": "E01",
            "transient": False,
            "profile": "熟悉周边路线的年轻向导",
            "relationship_intents": [
                {"target_handle": "C01", "relationship": "谨慎合作"}
            ],
            "capabilities": ["辨路"],
            "resources": ["旧地图"],
            "knowledge_boundary": ["只了解当前区域"],
            "arc_direction": "由交易伙伴变成可靠同伴",
            "attributes": {"occupation": "向导"},
        }
    ]
    payload["beats"][1]["character_handles"].append("N01")
    payload["character_motivations"].append(
        {"character_handle": "N01", "motivation": "借引路证明自己的价值"}
    )
    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
    canon = {
        "entities": [
            {
                "id": "char-real-id",
                "kind": "character",
                "name": "苏砚",
                "aliases": [],
                "attributes": {},
            }
        ]
    }
    contract, brief, delta = compile_intent_contract(
        _skeleton(), intent, snapshot, canon
    )
    entity = contract["entity_introductions"][0]
    assert entity["id"] in contract["execution_contracts"][0]["actor_ids"]
    assert entity["id"] in brief["beats"][0]["allowed_entity_ids"]
    assert brief["character_motivations"][-1]["character_id"] == entity["id"]
    prose = build_v4_prose_input(snapshot, intent, contract, brief)
    assert prose["authorized_new_entities"][0]["motivation"] == "借引路证明自己的价值"
    state_before = snapshot["execution_context"]["state_before"]
    assert "revision_local_entities" not in state_before
    state_after = apply_state_delta(state_before, delta)
    assert state_after["revision_local_entities"][entity["id"]]["name"] == "闻鹿"
    assert state_after["subjects"][entity["id"]]["knowledge"] == []
    assert state_after["subjects"][entity["id"]]["relationships"] == {
        "char-real-id": "谨慎合作"
    }
    assert state_after["subjects"][entity["id"]]["capabilities"] == ["辨路"]


def test_transient_character_never_enters_expected_delta():
    snapshot = _snapshot()
    payload = json.loads(_response())
    payload["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "kind": "character",
            "name": "过路人",
            "aliases": [],
            "narrative_function": "只递交当前消息",
            "source_event_handle": "E01",
            "transient": True,
            "profile": "只在当前场景递话的路人",
            "attributes": {},
        }
    ]
    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
    contract, _brief, delta = compile_intent_contract(
        _skeleton(), intent, snapshot, {"entities": []}
    )
    assert contract["entity_introductions"] == []
    assert delta["entity_introductions"] == []


def test_scope_location_and_connection_extend_revision_scope_graph():
    snapshot = _snapshot()
    snapshot["model_input"]["scope_taxonomy"] = [
        {"type_id": "port", "display_name": "港口"},
        {"type_id": "market", "display_name": "市集", "parent_type_id": "port"},
    ]
    snapshot["model_input"]["visible_characters_and_world"].append(
        {
            "entity_handle": "S01",
            "kind": "location",
            "name": "旧港",
            "aliases": [],
            "attributes": {"scope_type": "port", "depth": 0},
            "current_state": {},
        }
    )
    snapshot["model_input"]["allowed_entity_handles"].append("S01")
    snapshot["handle_bindings"]["entities"]["S01"] = "scope-old"
    from app.services.story.story_novel_context_utils import value_hash

    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash")
    snapshot["snapshot_hash"] = value_hash(snapshot)
    payload = json.loads(_response())
    payload["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "kind": "location",
            "name": "远岛市集",
            "aliases": [],
            "narrative_function": "扩大当前交易范围",
            "source_event_handle": "E01",
            "transient": False,
            "attributes": {
                "scope_type": "market",
                "parent_scope_id": "S01",
                "depth": 1,
                "connections": [
                    {
                        "to_scope_id": "S01",
                        "connection_type": "定期航线",
                        "direction": "two_way",
                    }
                ],
            },
        }
    ]
    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
    canon = {
        "entities": [
            {
                "id": "scope-old",
                "kind": "location",
                "name": "旧港",
                "aliases": [],
                "attributes": {"scope_type": "port", "depth": 0},
            }
        ]
    }
    contract, _brief, delta = compile_intent_contract(
        _skeleton(), intent, snapshot, canon
    )
    state_before = {
        **snapshot["execution_context"]["state_before"],
        "scope_graph": initial_scope_graph(canon),
    }
    state_after = apply_state_delta(state_before, delta)
    entity_id = contract["entity_introductions"][0]["id"]
    assert (
        state_after["scope_graph"]["nodes"][entity_id]["parent_scope_id"] == "scope-old"
    )
    assert (
        next(iter(state_after["scope_graph"]["edges"].values()))["connection_type"]
        == "定期航线"
    )


def test_dynamic_location_must_use_frozen_genre_taxonomy():
    snapshot = _snapshot()
    snapshot["model_input"]["scope_taxonomy"] = [
        {"type_id": "station", "display_name": "空间站"}
    ]
    from app.services.story.story_novel_context_utils import value_hash

    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash")
    snapshot["snapshot_hash"] = value_hash(snapshot)
    payload = json.loads(_response())
    payload["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "kind": "location",
            "name": "越界地点",
            "narrative_function": "扩大活动范围",
            "source_event_handle": "E01",
            "transient": False,
            "attributes": {"scope_type": "固定县城模板", "depth": 0},
        }
    ]
    with pytest.raises(ValueError, match="未知 scope_type"):
        parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)


def test_persistent_characters_cannot_duplicate_the_same_relation_function():
    snapshot = _snapshot()
    payload = json.loads(_response())
    base = {
        "aliases": [],
        "narrative_function": "当前区域的持续向导",
        "source_event_handle": "E01",
        "transient": False,
        "profile": "熟悉本地路径",
        "relationship_intents": [{"target_handle": "C01", "relationship": "谨慎合作"}],
        "capabilities": ["辨路"],
        "resources": [],
        "knowledge_boundary": ["只了解当前区域"],
        "arc_direction": "逐步建立信任",
        "attributes": {},
    }
    payload["entity_proposals"] = [
        {**base, "proposal_handle": "N01", "kind": "character", "name": "闻鹿"},
        {**base, "proposal_handle": "N02", "kind": "character", "name": "迟岚"},
    ]
    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
    with pytest.raises(ValueError, match="叙事功能重复"):
        compile_intent_contract(
            _skeleton(),
            intent,
            snapshot,
            {
                "entities": [
                    {
                        "id": "char-real-id",
                        "kind": "character",
                        "name": "苏砚",
                        "aliases": [],
                        "attributes": {},
                    }
                ]
            },
        )
