import pytest
from app.services.story.story_novel_chapter_package_contract import (
    _finalize_contract,
    _normalize_missing_contract_fields,
    _strip_thread_state_transitions,
    parse_chapter_package,
)
from app.services.story.story_novel_plan_execution_contract import (
    execution_contracts_valid,
)


def test_package_shape_rejects_legacy_effect_coverage():
    with pytest.raises(ValueError, match="只含 chapter_contract/chapter_brief"):
        parse_chapter_package(
            '{"chapter_contract":{},"chapter_brief":{},"effect_coverage":[]}',
            None,
            None,
            1,
        )


def test_package_deduplicates_shared_fact_execution_refs():
    skeleton = {
        "position": 5,
        "title": "共同获知",
        "goal": "两人共同确认同一事实",
        "key_events": ["沈禾与顾砚共同完成测量"],
        "character_focus": ["沈禾", "顾砚"],
        "open_threads": [],
        "end_state": "两人掌握同一测量结论",
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
        "length_source": "profile_default",
        "required_event_ids": ["event-5-1"],
        "timeline_event_bindings": {"time-5": "event-5-1"},
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-shen", "char-gu"],
        "future_guard_entity_ids": ["char-shen", "char-gu"],
    }
    contract = {
        **skeleton,
        "preconditions": [],
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [
            {
                "character_id": character_id,
                "fact_id": "fact-shared-measurement",
                "source_event_id": "event-5-1",
            }
            for character_id in ("char-shen", "char-gu")
        ],
        "execution_contracts": [
            {
                "event_id": "event-5-1",
                "action_phase": "complete",
                "time_scope": "same_day",
                "actor_ids": ["char-shen", "char-gu"],
                "effort": "moderate",
                "timeline_ids": [],
                "knowledge_fact_ids": [],
            }
        ],
    }
    canon = {
        "entities": [
            {"id": character_id, "kind": "character", "name": character_id}
            for character_id in ("char-shen", "char-gu")
        ]
    }

    result = _finalize_contract(contract, skeleton, canon)

    assert result["execution_contracts"][0]["knowledge_fact_ids"] == [
        "fact-shared-measurement"
    ]
    assert execution_contracts_valid(result)


def test_validator_accepts_only_redundant_fact_refs_from_legacy_packages():
    chapter = {
        "required_event_ids": ["event-5-1"],
        "timeline_event_bindings": {},
        "knowledge_grants": [
            {
                "character_id": character_id,
                "fact_id": "fact-shared-measurement",
                "source_event_id": "event-5-1",
            }
            for character_id in ("char-shen", "char-gu")
        ],
        "execution_contracts": [
            {
                "event_id": "event-5-1",
                "action_phase": "complete",
                "time_scope": "same_day",
                "actor_ids": ["char-shen", "char-gu"],
                "effort": "moderate",
                "timeline_ids": [],
                "knowledge_fact_ids": [
                    "fact-shared-measurement",
                    "fact-shared-measurement",
                ],
            }
        ],
    }

    assert execution_contracts_valid(chapter)
    chapter["execution_contracts"][0]["knowledge_fact_ids"].append("fact-extra")
    assert not execution_contracts_valid(chapter)


def test_package_keeps_thread_closure_out_of_entity_state_transitions():
    contract = {
        "open_threads": [],
        "payoffs_due": ["堆肥能否安全腐熟"],
        "preconditions": [
            {"predicate": "木料已经备齐"},
            {
                "subject_id": "obj-tool",
                "field": "status",
                "operator": "eq",
                "value": "ready",
            },
        ],
        "state_transitions": [
            {
                "subject_id": "堆肥能否安全腐熟",
                "field": "status",
                "from_value": "open",
                "to_value": "closed",
            },
            {
                "subject_id": "unknown-object",
                "field": "status",
                "from_value": "旧",
                "to_value": "新",
            },
            {
                "subject_id": "obj-ordinary-tool",
                "field": "location",
                "to_value": "loc-house",
            },
        ],
    }

    normalized = _strip_thread_state_transitions(contract)

    assert normalized["state_transitions"] == [contract["state_transitions"][1]]
    assert normalized["preconditions"] == [contract["preconditions"][1]]


def test_package_keeps_missing_character_and_movement_means_invalid():
    contract = {
        "knowledge_grants": [
            {"fact_id": "fact-seed", "source_event_id": "event-11-1"},
            {
                "subject_id": "char-he",
                "fact_id": "fact-risk",
                "source_event_id": "event-11-2",
            },
        ],
        "location_transitions": [
            {
                "subject_id": "char-he",
                "from_location_id": "loc-field",
                "to_location_id": "loc-market",
            }
        ],
        "execution_contracts": [
            {
                "event_id": "event-11-1",
                "actor_ids": ["char-he"],
                "knowledge_fact_ids": ["fact-seed"],
            },
            {
                "event_id": "event-11-2",
                "actor_ids": ["char-he", "char-yan"],
                "knowledge_fact_ids": ["fact-risk"],
            },
        ],
    }
    canon = {
        "entities": [
            {"id": "char-he", "kind": "character"},
            {"id": "char-yan", "kind": "character"},
        ]
    }

    normalized = _normalize_missing_contract_fields(contract, canon)

    assert "character_id" not in normalized["knowledge_grants"][0]
    assert normalized["knowledge_grants"][1]["character_id"] == "char-he"
    assert "subject_id" not in normalized["knowledge_grants"][1]
    assert "means" not in normalized["location_transitions"][0]
