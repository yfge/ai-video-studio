import pytest
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_state_validator import validate_state_delta
from app.services.story.story_novel_world_expansion import (
    canon_with_plan_expansion,
    normalize_package_expansion,
)
from app.services.story.story_novel_world_order import stable_entity_id


def test_package_assigns_stable_ids_and_rewrites_current_refs():
    contract = _chapter()
    contract["entity_introductions"] = [
        {
            "ref": "new-guide",
            "kind": "character",
            "name": "引路人",
            "aliases": [],
            "attributes": {"occupation": "向导"},
            "initial_state": {"location": "loc-home", "knowledge": []},
            "source_event_id": "event-3-1",
            "persistence": "revision",
            "reason": "后续继续带领主角认识更大区域",
        }
    ]
    contract["execution_contracts"][0]["actor_ids"] = ["char-main", "new-guide"]
    brief = {
        "character_motivations": [
            {"character_id": "new-guide", "motivation": "完成引路职责"}
        ]
    }

    normalized, normalized_brief = normalize_package_expansion(
        contract, brief, _canon(), _state()
    )
    entity = normalized["entity_introductions"][0]

    assert entity["id"].startswith("char-local-3-")
    assert entity["name"] == "引路人"
    assert entity["reason"] == "后续继续带领主角认识更大区域"
    assert normalized["execution_contracts"][0]["actor_ids"] == [
        "char-main",
        entity["id"],
    ]
    assert normalized_brief["character_motivations"][0]["character_id"] == entity["id"]
    repeated, _ = normalize_package_expansion(contract, brief, _canon(), _state())
    assert repeated["entity_introductions"][0]["id"] == entity["id"]
    expanded = canon_with_plan_expansion(_canon(), [normalized], _state())
    assert entity["id"] in {item["id"] for item in expanded["entities"]}


def test_verified_introduction_enters_revision_world_and_next_state():
    contract = _chapter()
    entity_id = stable_entity_id("character", 3, "引路人", "event-3-1")
    entity = {
        "id": entity_id,
        "kind": "character",
        "name": "引路人",
        "aliases": [],
        "attributes": {"occupation": "向导"},
        "source_event_id": "event-3-1",
        "first_appearance_position": 3,
        "persistence": "revision",
        "reason": "后续继续承担向导职责",
        "initial_state": {"location": "loc-home", "knowledge": []},
    }
    contract["entity_introductions"] = [entity]
    delta = compile_expected_delta(contract, _state())

    report, state_after = validate_state_delta(_canon(), contract, _state(), delta)

    assert report == {"status": "passed", "violations": []}
    assert state_after["revision_local_entities"][entity["id"]] == entity
    assert state_after["subjects"][entity["id"]]["location"] == "loc-home"
    expanded = canon_with_plan_expansion(_canon(), state=state_after)
    assert entity["id"] in {item["id"] for item in expanded["entities"]}


def test_existing_world_name_cannot_be_reintroduced():
    contract = _chapter()
    contract["entity_introductions"] = [
        {
            "ref": "duplicate",
            "kind": "character",
            "name": "主角",
            "source_event_id": "event-3-1",
            "reason": "错误重复",
        }
    ]

    with pytest.raises(ValueError, match="必须复用现有 ID"):
        normalize_package_expansion(contract, {}, _canon(), _state())


def _canon():
    return {
        "entities": [
            {"id": "char-main", "kind": "character", "name": "主角"},
            {"id": "loc-home", "kind": "location", "name": "起点"},
        ],
        "timeline": [],
        "world_rules": [],
        "milestones": [],
        "character_arcs": [],
        "initial_state": {"char-main": {"location": "loc-home", "knowledge": []}},
        "canon_hash": "canon-hash",
    }


def _state():
    return {
        "subjects": {
            "char-main": {
                "location": "loc-home",
                "knowledge": [],
                "possessions": [],
            }
        },
        "occurred_event_ids": [],
        "completed_milestone_ids": [],
        "threads": {},
    }


def _chapter(position=3):
    return {
        "position": position,
        "title": "看见更大的世界",
        "goal": "推进当前选择",
        "key_events": ["主角在引导下认识新的活动范围"],
        "character_focus": ["主角"],
        "open_threads": [],
        "end_state": "主角拥有新的选择",
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
        "length_source": "profile_default",
        "preconditions": [],
        "required_event_ids": [f"event-{position}-1"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-main", "loc-home"],
        "timeline_event_bindings": {},
        "execution_contracts": [
            {
                "event_id": f"event-{position}-1",
                "action_phase": "instant",
                "time_scope": "same_day",
                "actor_ids": ["char-main"],
                "effort": "light",
                "timeline_ids": [],
                "knowledge_fact_ids": [],
            }
        ],
        "entity_introductions": [],
    }
