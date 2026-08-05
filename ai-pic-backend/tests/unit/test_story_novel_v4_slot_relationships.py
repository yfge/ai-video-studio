import pytest
from app.services.story.story_novel_entity_proposal_contract import (
    parse_entity_proposals,
)
from app.services.story.story_novel_planner_slot_visibility import (
    authorized_entity_slots,
)


def test_slot_without_single_target_accepts_visible_character_subset():
    model_input = _model_input()
    rows = parse_entity_proposals([_proposal()], model_input)

    assert rows[0]["relationship_intents"] == [
        {"target_handle": "C02", "relationship": "谨慎合作"},
        {"target_handle": "C01", "relationship": "经验校正"},
    ]


def test_slot_without_single_target_allows_no_initial_relation():
    model_input = _model_input()
    proposal = _proposal()
    proposal["relationship_intents"] = []

    assert (
        parse_entity_proposals([proposal], model_input)[0]["relationship_intents"] == []
    )


def test_transient_character_does_not_require_long_term_profile_or_arc():
    proposal = {
        "proposal_handle": "T01",
        "kind": "character",
        "name": "养畜人",
        "narrative_function": "完成一次当前章交换",
        "source_event_handle": "E01",
        "transient": True,
    }

    result = parse_entity_proposals([proposal], _model_input())[0]

    assert result["profile"] == ""
    assert result["arc_direction"] == ""


def test_persistent_character_still_requires_profile_and_arc():
    proposal = _proposal()
    proposal["profile"] = ""

    with pytest.raises(ValueError, match="持久人物 proposal"):
        parse_entity_proposals([proposal], _model_input())


def test_relationship_intent_alias_is_normalized_to_canonical_shape():
    model_input, proposal = _model_input(), _proposal()
    proposal["relationship_intents"] = [{"target_handle": "C01", "intent": "有限合作"}]

    parsed = parse_entity_proposals([proposal], model_input)

    assert parsed[0]["relationship_intents"] == [
        {"target_handle": "C01", "relationship": "有限合作"}
    ]


@pytest.mark.parametrize(
    "malformed",
    [
        {"C01": "合作"},
        [{"target_handle": "C01", "intent": "合作", "relationship": "合作"}],
    ],
)
def test_relationship_intents_error_explains_the_exact_json_shape(malformed):
    model_input, proposal = _model_input(), _proposal()
    proposal["relationship_intents"] = malformed

    with pytest.raises(ValueError, match="不得使用对象映射"):
        parse_entity_proposals([proposal], model_input)


@pytest.mark.parametrize("target", ["S01", "P02"])
def test_slot_cannot_target_location_or_same_chapter_proposal(target):
    model_input = _model_input()
    proposal = _proposal()
    second = _proposal() | {"proposal_handle": "P02", "slot_id": None, "name": "新客"}
    proposal["relationship_intents"] = [
        {"target_handle": target, "relationship": "临时结盟"}
    ]

    with pytest.raises(ValueError, match="relationship target"):
        parse_entity_proposals([proposal, second], model_input)


def test_slot_with_explicit_target_keeps_exact_singleton_contract():
    model_input = _model_input()
    slot = model_input["authorized_entity_slots"][0]
    slot["relationship_target_handle"] = "C01"
    proposal = _proposal()
    proposal["relationship_intents"] = [
        {"target_handle": "C01", "relationship": slot["relationship"]}
    ]
    assert parse_entity_proposals([proposal], model_input)

    proposal["relationship_intents"][0]["relationship"] = "改写关系"
    with pytest.raises(ValueError, match="关系合同不匹配"):
        parse_entity_proposals([proposal], model_input)


def test_slot_visibility_freezes_only_current_visible_character_handles():
    slot = _model_input()["authorized_entity_slots"][0]
    plan = {
        "current_arc_plan": {
            "start_position": 1,
            "end_position": 8,
            "instantiated_character_slots": [{**slot, "first_appearance_position": 5}],
            "instantiated_scope_slots": [],
        }
    }
    rows = [
        {"id": "char-main", "kind": "character"},
        {"id": "scope-home", "kind": "location"},
    ]
    visible = authorized_entity_slots(
        plan,
        5,
        {"char-main": "C01", "scope-home": "S01", "hidden": "C99"},
        rows,
    )
    assert visible[0]["allowed_relationship_target_handles"] == ["C01"]


def _model_input():
    slot = {
        "slot_id": "slot-local-grower",
        "mandatory": False,
        "kind": "character",
        "name": "林茂",
        "profile": "长期在本地耕作的老农",
        "narrative_function": "用本地经验校正试作判断",
        "relationship_target_handle": None,
        "relationship": "与顾砚、沈禾尚无依附关系，以经验参与有限合作。",
        "capabilities": ["辨识苗情"],
        "resources": ["邻田"],
        "knowledge_boundary": ["不知道沈禾的真实来历"],
        "arc_direction": "由质疑到有限合作",
    }
    return {
        "current_chapter": {"events": [{"event_handle": "E01"}]},
        "allowed_entity_handles": ["C01", "C02", "S01"],
        "visible_characters_and_world": [
            _character("C01", "顾砚"),
            _character("C02", "沈禾"),
            {"entity_handle": "S01", "kind": "location", "name": "薄田"},
        ],
        "authorized_entity_slots": [
            {**slot, "allowed_relationship_target_handles": ["C01", "C02"]}
        ],
    }


def _character(handle, name):
    return {"entity_handle": handle, "kind": "character", "name": name, "aliases": []}


def _proposal():
    return {
        "proposal_handle": "P01",
        "slot_id": "slot-local-grower",
        "kind": "character",
        "name": "林茂",
        "narrative_function": "用本地经验校正试作判断",
        "source_event_handle": "E01",
        "transient": False,
        "profile": "长期在本地耕作的老农",
        "relationship_intents": [
            {"target_handle": "C02", "relationship": "谨慎合作"},
            {"target_handle": "C01", "relationship": "经验校正"},
        ],
        "capabilities": ["辨识苗情"],
        "resources": ["邻田"],
        "knowledge_boundary": ["不知道沈禾的真实来历"],
        "arc_direction": "由质疑到有限合作",
    }
