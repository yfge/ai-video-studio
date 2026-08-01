import json

import pytest
from app.services.story.story_novel_chapter_contract_v4 import compile_intent_contract
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_state_validator import validate_state_delta
from app.services.story.story_novel_v4_prose_input import build_v4_prose_input
from tests.unit.test_story_novel_v4_snapshot import _response, _skeleton, _snapshot


def test_semantic_effects_compile_from_frozen_state_and_validate():
    snapshot, canon = _effect_snapshot()
    payload = json.loads(_response())
    payload["effect_intents"] = [
        _effect("FX01", "knowledge_gain", "C01", value="密道只在退潮时开启"),
        _effect(
            "FX02",
            "relationship_change",
            "C01",
            target_handle="C02",
            value="开始信任",
        ),
        _effect("FX03", "capability_add", "C01", value="辨潮"),
        _effect("FX04", "state_change", "C01", field="reputation", value=2),
        _effect(
            "FX05",
            "location_change",
            "C01",
            target_handle="S02",
            means="乘船",
        ),
        _effect("FX06", "ownership_change", "X01", target_handle="C02"),
    ]
    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
    contract, brief, delta = compile_intent_contract(
        _skeleton(), intent, snapshot, canon
    )
    state_before = snapshot["execution_context"]["state_before"]
    validation, state_after = validate_state_delta(canon, contract, state_before, delta)

    assert validation == {"status": "passed", "violations": []}
    assert any(
        item["field"] == "relationships.char-rival"
        and item["from_value"] is None
        and item["to_value"] == "开始信任"
        for item in contract["state_transitions"]
    )
    assert state_after["subjects"]["char-main"]["capabilities"] == ["辨潮"]
    assert state_after["subjects"]["char-main"]["reputation"] == 2
    assert state_after["subjects"]["char-main"]["location"] == "scope-far"
    assert state_after["subjects"]["object-key"]["owner_id"] == "char-rival"
    assert len(state_after["subjects"]["char-main"]["knowledge"]) == 1
    assert all(contract["effect_event_bindings"].values())
    assert "密道只在退潮时开启" in contract["effect_semantics"]["knowledge:1"]
    assert any(beat["effect_contract_ids"] for beat in brief["beats"])

    prose = build_v4_prose_input(snapshot, intent, contract, brief)
    encoded = json.dumps(prose, ensure_ascii=False)
    assert "effect_intents" in prose["chapter_intent"]
    assert "char-main" not in encoded
    assert "from_value" not in encoded


def test_canon_milestone_outcome_is_compiled_without_model_state_claim():
    snapshot = _snapshot()
    snapshot["model_input"]["visible_characters_and_world"][0]["current_state"] = {
        "status": "沉睡"
    }
    snapshot["execution_context"]["state_before"]["subjects"]["char-real-id"] = {
        "status": "沉睡"
    }
    _rehash(snapshot)
    skeleton = {**_skeleton(), "milestones_consumed": ["mile-awake"]}
    canon = {
        "entities": [
            {
                "id": "char-real-id",
                "kind": "character",
                "name": "苏砚",
                "aliases": [],
                "attributes": {},
            }
        ],
        "milestones": [
            {
                "id": "mile-awake",
                "label": "苏醒",
                "planned_position": 1,
                "repeatable": False,
                "outcomes": [
                    {
                        "subject_id": "char-real-id",
                        "field": "status",
                        "operator": "eq",
                        "value": "苏醒",
                    }
                ],
            }
        ],
    }
    intent = parse_chapter_intent(_response(), snapshot)
    contract, _brief, delta = compile_intent_contract(skeleton, intent, snapshot, canon)
    assert contract["state_transitions"][0]["from_value"] == "沉睡"
    assert contract["state_transitions"][0]["to_value"] == "苏醒"
    assert contract["effect_event_bindings"]["state:1"] == "event-1-1"
    validation, state_after = validate_state_delta(
        canon, contract, snapshot["execution_context"]["state_before"], delta
    )
    assert validation["status"] == "passed"
    assert state_after["subjects"]["char-real-id"]["status"] == "苏醒"


def test_intent_cannot_author_database_ids_or_from_to_values():
    snapshot = _snapshot()
    payload = json.loads(_response())
    payload["effect_intents"] = [
        {
            **_effect("FX01", "status_change", "C01", value="完成"),
            "from_value": "未完成",
        }
    ]
    with pytest.raises(ValueError, match="越界字段"):
        parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)


def test_intent_requires_one_final_effect_per_persistent_field():
    snapshot, _canon = _effect_snapshot()
    payload = json.loads(_response())
    payload["effect_intents"] = [
        _effect("FX01", "status_change", "X01", value="账册栏目已建立"),
        _effect("FX02", "status_change", "X01", value="账册开始记录失误"),
    ]

    with pytest.raises(ValueError, match="只能声明一次最终效果"):
        parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)


def test_optional_noop_effect_is_recorded_without_becoming_hard_state():
    snapshot, canon = _effect_snapshot()
    snapshot["model_input"]["visible_characters_and_world"][0]["current_state"][
        "resources"
    ] = ["已跟踪资源"]
    snapshot["execution_context"]["state_before"]["subjects"]["char-main"][
        "resources"
    ] = ["已跟踪资源"]
    _rehash(snapshot)
    payload = json.loads(_response())
    payload["effect_intents"] = [
        _effect("FX01", "resource_remove", "C01", value="未跟踪的剧情成本")
    ]
    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)

    contract, _brief, delta = compile_intent_contract(
        _skeleton(), intent, snapshot, canon
    )

    assert contract["state_transitions"] == []
    assert delta["state_transitions"] == []
    assert contract["ignored_effect_intents"] == [
        {
            "effect_handle": "FX01",
            "kind": "resource_remove",
            "reason": "no_persistent_state_change",
        }
    ]


def _effect(handle, kind, subject, **values):
    return {
        "effect_handle": handle,
        "kind": kind,
        "subject_handle": subject,
        "source_event_handle": "E01",
        "target_handle": values.get("target_handle"),
        "field": values.get("field"),
        "value": values.get("value"),
        "means": values.get("means"),
    }


def _effect_snapshot():
    snapshot = _snapshot()
    rows = [
        ("C01", "char-main", "character", "苏砚", {"reputation": 1, "location": "S01"}),
        ("C02", "char-rival", "character", "闻鹿", {"location": "S01"}),
        ("S01", "scope-home", "location", "旧港", {}),
        ("S02", "scope-far", "location", "远岛", {}),
        ("X01", "object-key", "object", "铜钥", {"owner_id": "C01", "location": "S01"}),
    ]
    snapshot["handle_bindings"]["entities"] = {
        handle: entity_id for handle, entity_id, *_ in rows
    }
    snapshot["model_input"]["allowed_entity_handles"] = [row[0] for row in rows]
    snapshot["model_input"]["visible_characters_and_world"] = [
        {
            "entity_handle": handle,
            "kind": kind,
            "name": name,
            "aliases": [],
            "attributes": {},
            "current_state": current,
        }
        for handle, _entity_id, kind, name, current in rows
    ]
    snapshot["execution_context"]["state_before"] = {
        "subjects": {
            "char-main": {"reputation": 1, "location": "scope-home"},
            "char-rival": {"location": "scope-home"},
            "scope-home": {},
            "scope-far": {},
            "object-key": {"owner_id": "char-main", "location": "scope-home"},
        }
    }
    _rehash(snapshot)
    canon = {
        "entities": [
            {
                "id": entity_id,
                "kind": kind,
                "name": name,
                "aliases": [],
                "attributes": {},
            }
            for _handle, entity_id, kind, name, _current in rows
        ],
        "milestones": [],
    }
    return snapshot, canon


def _rehash(snapshot):
    state = snapshot["execution_context"]["state_before"]
    snapshot["state_before_hash"] = value_hash(state)
    snapshot["execution_context"]["evidence"]["state_before_hash"] = value_hash(state)
    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash", None)
    snapshot["snapshot_hash"] = value_hash(snapshot)
