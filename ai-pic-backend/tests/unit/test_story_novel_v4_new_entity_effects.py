import json

from app.services.story.story_novel_chapter_contract_v4 import compile_intent_contract
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_state_validator import validate_state_delta
from tests.unit.test_story_novel_v4_snapshot import _response, _skeleton, _snapshot


def test_new_character_can_gain_knowledge_in_its_introduction_chapter():
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
            "attributes": {},
        }
    ]
    payload["beats"][1]["character_handles"].append("N01")
    payload["character_motivations"].append(
        {"character_handle": "N01", "motivation": "证明自己的判断"}
    )
    payload["effect_intents"] = [
        {
            "effect_handle": "FX01",
            "kind": "knowledge_gain",
            "subject_handle": "N01",
            "source_event_handle": "E01",
            "target_handle": None,
            "field": None,
            "value": "旧约的真实含义",
            "means": None,
        },
        {
            "effect_handle": "FX02",
            "kind": "relationship_change",
            "subject_handle": "N01",
            "source_event_handle": "E01",
            "target_handle": "C01",
            "field": None,
            "value": "决定合作",
            "means": None,
        },
    ]
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
    contract, _brief, delta = compile_intent_contract(
        _skeleton(), intent, snapshot, canon
    )
    entity_id = contract["entity_introductions"][0]["id"]

    assert contract["knowledge_grants"][0]["character_id"] == entity_id
    assert any(
        item["subject_id"] == entity_id
        and item["field"] == "relationships.char-real-id"
        and item["to_value"] == "决定合作"
        for item in contract["state_transitions"]
    )
    validation, state_after = validate_state_delta(
        canon,
        contract,
        snapshot["execution_context"]["state_before"],
        delta,
    )
    assert validation == {"status": "passed", "violations": []}
    assert len(state_after["subjects"][entity_id]["knowledge"]) == 1
    assert state_after["subjects"][entity_id]["relationships"]["char-real-id"] == (
        "决定合作"
    )


def test_transient_character_cannot_author_typed_effects():
    snapshot = _snapshot()
    payload = json.loads(_response())
    payload["entity_proposals"] = [
        {
            "proposal_handle": "N01",
            "kind": "character",
            "name": "路人",
            "narrative_function": "传递一次消息",
            "source_event_handle": "E01",
            "transient": True,
            "profile": "只在当前场景出现",
        }
    ]
    payload["effect_intents"] = [
        {
            "effect_handle": "FX01",
            "kind": "knowledge_gain",
            "subject_handle": "N01",
            "source_event_handle": "E01",
            "value": "秘密",
        }
    ]
    import pytest

    with pytest.raises(ValueError, match="subject/source event"):
        parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
