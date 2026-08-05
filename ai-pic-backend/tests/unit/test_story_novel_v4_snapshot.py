import copy
import json

import pytest
from app.services.story.story_novel_chapter_contract_v4 import compile_intent_contract
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_planner_snapshot import valid_planner_snapshot
from app.services.story.story_novel_snapshot_handles import (
    localize_ids,
    visible_snapshot_entities,
)
from app.services.story.story_novel_v4_prose_input import build_v4_prose_input


def _snapshot():
    value = {
        "schema": "story_novel_planner_snapshot.v1",
        "position": 1,
        "canon_hash": "canon-hash",
        "chapter_contract_hash": "contract-hash",
        "state_before_hash": value_hash({"subjects": {"char-real-id": {}}}),
        "source_manifest": {
            "chapter_ids": [],
            "chapter_hashes": [],
            "event_ids": ["database-event-id"],
            "event_hashes": ["source-hash"],
            "memory_ids": ["database-memory-id"],
            "memory_hashes": ["memory-hash"],
        },
        "handle_bindings": {
            "events": {"E01": "event-1-1"},
            "entities": {"C01": "char-real-id"},
            "world_events": {"WE01": "database-event-id"},
            "memories": {"M01": "database-memory-id"},
        },
        "model_input": {
            "schema": "story_novel_chapter_planner_input.v1",
            "position": 1,
            "current_chapter": {
                "position": 1,
                "title": "开局",
                "goal": "作出选择",
                "character_focus": ["苏砚"],
                "open_threads": [],
                "end_state": "选择已作出",
                "min_chars": 1800,
                "target_chars": 2000,
                "max_chars": 3000,
                "events": [{"event_handle": "E01", "description": "苏砚接受挑战"}],
            },
            "current_arc": {},
            "story_invariants": {"genre": "成长冒险"},
            "visible_characters_and_world": [
                {
                    "entity_handle": "C01",
                    "kind": "character",
                    "name": "苏砚",
                    "aliases": [],
                    "attributes": {},
                    "current_state": {},
                }
            ],
            "planning_evidence": [
                {"evidence_handle": "M01", "content": "苏砚记得旧约"}
            ],
            "recent_chapters": [],
            "previous_chapter_tail": "",
            "allowed_entity_handles": ["C01"],
            "expected_beat_count": 2,
        },
        "execution_context": {
            "brief_input": {"planning_evidence": {}},
            "state_before": {"subjects": {"char-real-id": {}}},
            "hard_constraints": {},
            "evidence": {
                "state_before_hash": value_hash({"subjects": {"char-real-id": {}}})
            },
        },
        "audit_context": {"canon": {}, "future_guard_index": {}},
        "truncations": [],
    }
    value["model_input_hash"] = value_hash(value["model_input"])
    value["snapshot_hash"] = value_hash(value)
    return value


def _response():
    return json.dumps(
        {
            "beats": [
                {
                    "beat_id": "B01",
                    "purpose": "压力出现",
                    "target_chars": 900,
                    "event_handles": [],
                    "character_handles": ["C01"],
                },
                {
                    "beat_id": "B02",
                    "purpose": "作出选择",
                    "target_chars": 1100,
                    "event_handles": ["E01"],
                    "character_handles": ["C01"],
                },
            ],
            "character_motivations": [
                {"character_handle": "C01", "motivation": "保护眼前所得"}
            ],
            "emotional_continuity": "犹疑转为坚定",
            "causal_bridge": "旧约促使他接受挑战",
            "summary": "苏砚接受挑战",
            "cliffhanger": "挑战的代价随即出现",
            "entity_proposals": [],
        },
        ensure_ascii=False,
    )


def _skeleton():
    return {
        "position": 1,
        "title": "开局",
        "goal": "作出选择",
        "key_events": ["苏砚接受挑战"],
        "character_focus": ["苏砚"],
        "open_threads": [],
        "end_state": "选择已作出",
        "min_chars": 1800,
        "target_chars": 2000,
        "max_chars": 3000,
        "length_source": "profile_default",
        "required_event_ids": ["event-1-1"],
        "timeline_event_bindings": {},
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-real-id"],
        "future_guard_entity_ids": ["char-real-id"],
    }


def test_intent_parser_is_deterministic_for_same_frozen_snapshot():
    snapshot = _snapshot()
    assert valid_planner_snapshot(snapshot)
    first = parse_chapter_intent(_response(), snapshot)
    second = parse_chapter_intent(_response(), copy.deepcopy(snapshot))
    assert first == second
    assert first["snapshot_hash"] == snapshot["snapshot_hash"]


def test_intent_parser_rejects_mutated_snapshot():
    snapshot = _snapshot()
    snapshot["model_input"]["previous_chapter_tail"] = "changed"
    with pytest.raises(ValueError, match="snapshot"):
        parse_chapter_intent(_response(), snapshot)


def test_prose_packet_contains_no_raw_memory_event_or_database_ids():
    snapshot = _snapshot()
    intent = parse_chapter_intent(_response(), snapshot)
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
    contract, brief, _delta = compile_intent_contract(
        _skeleton(), intent, snapshot, canon
    )
    prose = build_v4_prose_input(snapshot, intent, contract, brief)
    encoded = json.dumps(prose, ensure_ascii=False)
    assert prose["prompt_evidence"]["raw_world_event_count"] == 0
    assert prose["prompt_evidence"]["raw_character_memory_count"] == 0
    assert "database-event-id" not in encoded
    assert "database-memory-id" not in encoded
    assert "char-real-id" not in encoded


def test_visible_state_references_are_replaced_by_snapshot_handles():
    localized = localize_ids(
        {
            "owner_id": "char-real-id",
            "connections": [{"to_scope_id": "scope-real-id"}],
        },
        {"char-real-id": "C01", "scope-real-id": "S01"},
    )
    encoded = json.dumps(localized, ensure_ascii=False)
    assert "char-real-id" not in encoded
    assert "scope-real-id" not in encoded
    assert '"owner_id": "C01"' in encoded
    assert '"to_scope_id": "S01"' in encoded


def test_revision_local_entities_remain_available_to_later_planners():
    rows = visible_snapshot_entities(
        {
            "state_before": {
                "revision_local_entities": {
                    "char-new": {
                        "id": "char-new",
                        "kind": "character",
                        "name": "迟岚",
                        "aliases": [],
                        "attributes": {"narrative_function": "本卷竞争者"},
                    }
                }
            }
        },
        {"compiled_canon": {"entities": []}},
    )
    assert [(item["id"], item["name"]) for item in rows] == [("char-new", "迟岚")]
