import json

import pytest
from app.services.story.story_novel_plan_normalizer import normalize_plan_payload
from app.services.story.story_novel_plan_semantic_audit import (
    _apply_missing_effects,
    _parse_audit,
)
from app.services.story.story_novel_plan_semantic_effects import (
    filter_redundant_audit_effects,
    remove_unsupported_effects,
)
from app.services.story.story_novel_plan_validator import validate_generation_plan
from tests.unit.test_story_novel_plan_semantic_audit import _canon, _chapter


def _grant(character_id, fact_id, event_id):
    return {
        "character_id": character_id,
        "fact_id": fact_id,
        "source_event_id": event_id,
    }


def _empty_effects():
    return {
        "knowledge_grants": [],
        "state_transitions": [],
        "location_transitions": [],
        "milestones_consumed": [],
    }


def _execution(event_id, knowledge_fact_ids=None):
    return {
        "event_id": event_id,
        "action_phase": "instant",
        "time_scope": "instant",
        "actor_ids": ["char-wangming"],
        "effort": "none",
        "timeline_ids": [],
        "knowledge_fact_ids": list(knowledge_fact_ids or []),
    }


def _audit(grant, *, existing_fact_ids=None):
    existing_fact_ids = dict(existing_fact_ids or {})
    return [
        {
            "position": 1,
            "event_id": "evt-ch8-1",
            "event_order": 0,
            "execution_contract": _execution(
                "evt-ch8-1", existing_fact_ids.get("evt-ch8-1")
            ),
            "feasibility_issues": [],
            "missing_effects": {
                "knowledge_grants": [grant],
                "state_transitions": [],
                "location_transitions": [],
                "milestones_consumed": [],
            },
            "unsupported_effects": _empty_effects(),
        },
        {
            "position": 1,
            "event_id": "evt-ch8-2",
            "event_order": 1,
            "execution_contract": _execution(
                "evt-ch8-2", existing_fact_ids.get("evt-ch8-2")
            ),
            "feasibility_issues": [],
            "missing_effects": _empty_effects(),
            "unsupported_effects": _empty_effects(),
        },
    ]


def test_semantic_audit_moves_same_fact_to_earlier_source_event():
    chapter = _chapter()
    chapter["knowledge_grants"] = [_grant("char-wangming", "fact-canon", "evt-ch8-2")]
    audit = _audit(_grant("char-wangming", "fact-canon", "evt-ch8-1"))
    audit[0]["feasibility_issues"] = [
        {
            "code": "knowledge_effect_conflict",
            "severity": "blocking",
            "message": "同一事实应改绑较早事件",
        }
    ]

    result = filter_redundant_audit_effects(audit, _canon(), [], [chapter])
    patched, _ = _apply_missing_effects([chapter], result)
    patched, _ = remove_unsupported_effects(patched, result)

    assert result[0]["missing_effects"]["knowledge_grants"] == [
        _grant("char-wangming", "fact-canon", "evt-ch8-1")
    ]
    assert patched[0]["knowledge_grants"] == [
        _grant("char-wangming", "fact-canon", "evt-ch8-1")
    ]
    assert result[0]["feasibility_issues"] == [
        {
            "code": "knowledge_effect_conflict",
            "severity": "blocking",
            "message": "同一事实应改绑较早事件",
        }
    ]


def test_semantic_audit_keeps_same_fact_for_a_different_character():
    chapter = _chapter()
    chapter["knowledge_grants"] = [_grant("char-wangming", "fact-canon", "evt-ch8-2")]
    grant = _grant("char-laoguai", "fact-canon", "evt-ch8-1")

    result = filter_redundant_audit_effects(_audit(grant), _canon(), [], [chapter])

    assert result[0]["missing_effects"]["knowledge_grants"] == [grant]


def test_semantic_audit_accepts_existing_fact_id_for_same_source_event():
    chapter = _chapter()
    fact_id = "fact-dongqu-boundary-moved"
    chapter["knowledge_grants"] = [_grant("char-wangming", fact_id, "evt-ch8-1")]
    grant = _grant("char-laoguai", fact_id, "evt-ch8-1")

    parsed = _parse_audit(
        json.dumps(
            {"events": _audit(grant, existing_fact_ids={"evt-ch8-1": [fact_id]})}
        ),
        _canon(),
        [chapter],
    )

    assert parsed[0]["missing_effects"]["knowledge_grants"] == [grant]


def test_semantic_audit_assigns_stable_ids_for_new_model_fact_aliases():
    first = _grant("char-wangming", "fact-ev8-1-1", "evt-ch8-1")
    second = _grant("char-laoguai", "fact-ev8-1-1", "evt-ch8-1")
    payload = _audit(first)
    payload[0]["missing_effects"]["knowledge_grants"].append(second)

    parsed = _parse_audit(
        json.dumps({"events": payload}),
        _canon(),
        [_chapter()],
    )

    assert parsed[0]["missing_effects"]["knowledge_grants"] == [
        _grant("char-wangming", "fact-evt-ch8-1-1", "evt-ch8-1"),
        _grant("char-laoguai", "fact-evt-ch8-1-1", "evt-ch8-1"),
    ]


def test_semantic_audit_binds_omitted_source_to_containing_event():
    payload = _audit(_grant("char-wangming", "fact-ev8-1-1", "evt-ch8-1"))
    payload[0]["missing_effects"]["knowledge_grants"][0].pop("source_event_id")

    parsed = _parse_audit(json.dumps({"events": payload}), _canon(), [_chapter()])

    assert parsed[0]["missing_effects"]["knowledge_grants"] == [
        _grant("char-wangming", "fact-evt-ch8-1-1", "evt-ch8-1")
    ]


def test_semantic_audit_drops_organization_memory_suggestions():
    canon = _canon()
    canon["entities"].append(
        {"id": "org-villagers", "kind": "organization", "name": "村民组织"}
    )
    character_grant = _grant("char-wangming", "fact-evt-ch8-1-1", "evt-ch8-1")
    payload = _audit(character_grant)
    payload[0]["missing_effects"]["knowledge_grants"].append(
        _grant("org-villagers", "fact-evt-ch8-1-1", "evt-ch8-1")
    )

    parsed = _parse_audit(json.dumps({"events": payload}), canon, [_chapter()])

    assert parsed[0]["missing_effects"]["knowledge_grants"] == [character_grant]


def test_plan_normalizer_drops_known_organization_memory_only():
    canon = _canon()
    canon["entities"].append(
        {"id": "org-villagers", "kind": "organization", "name": "村民组织"}
    )
    chapter = _chapter()
    chapter["knowledge_grants"] = [
        _grant("org-villagers", "fact-evt-ch8-1-1", "evt-ch8-1")
    ]

    with pytest.raises(ValueError, match="知识只能授予角色"):
        validate_generation_plan(canon, [chapter])

    normalized = normalize_plan_payload({"chapters": [chapter]}, canon, None)

    assert normalized["chapters"][0]["knowledge_grants"] == []
