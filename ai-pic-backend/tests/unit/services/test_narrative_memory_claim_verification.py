import pytest
from app.core.exceptions import ServiceError
from app.services.narrative_memory.extraction_candidates import (
    build_candidate_payload,
    knowledge_character_bindings,
)
from tests.unit.services.narrative_memory_claim_fixtures import anchor as _anchor
from tests.unit.services.narrative_memory_claim_fixtures import (
    characters as _characters,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    event_evidence as _event_evidence,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    memory_bindings as _memory_bindings,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    normalized as _normalized,
)


def test_strict_candidates_replace_model_claims_with_source_quotes():
    anchor = _anchor()
    normalized = _normalized()

    payload = build_candidate_payload(
        normalized,
        [anchor],
        _characters(),
        strict=True,
        memory_character_bindings=_memory_bindings(),
        occurred_event_evidence=_event_evidence(),
    )

    event = payload.events[0]
    memory = payload.memories[0]
    assert event.summary == normalized["events"][0]["evidence"]
    assert "岑野" not in event.summary
    assert event.participant_character_ids == ["li-yan"]
    assert memory.content == normalized["memories"][0]["evidence"]
    assert memory.belief is None
    assert event.candidate_evidence["typed_event_ids"] == ["event-current"]
    assert event.candidate_evidence["claim_verified"] is True
    assert memory.candidate_evidence["typed_state_binding_verified"] is True
    assert memory.candidate_evidence["typed_character_id"] == "canon-li-yan"
    assert memory.candidate_evidence["typed_fact_id"] == "fact-key-received"
    assert memory.candidate_evidence["typed_source_event_id"] == "event-current"
    assert memory.candidate_evidence["claim_mode"] == "typed_state_bound"


def test_strict_candidates_reject_unknown_participant_and_anchor():
    normalized = _normalized()
    normalized["events"][0]["participant_character_ids"].append("future-ghost")
    with pytest.raises(ServiceError, match="未知角色"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence=_event_evidence(),
        )

    normalized = _normalized()
    normalized["events"][0]["occurred_at_anchor_business_id"] = "future-anchor"
    with pytest.raises(ServiceError, match="未知来源锚点"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence=_event_evidence(),
        )


def test_strict_memory_requires_exact_typed_grant_and_acquisition_clause():
    normalized = _normalized()
    normalized["memories"][0]["typed_fact_id"] = "future-fact"

    with pytest.raises(ServiceError, match="角色知识未绑定对应 typed grant"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence=_event_evidence(),
        )

    normalized = _normalized()
    normalized["memories"][0]["evidence"] = "黎雁站在门外……裴衡告诉褚蓝零号风钥已经移交"
    normalized["events"][0]["evidence"] = normalized["memories"][0]["evidence"]
    with pytest.raises(ServiceError, match="角色知识未绑定对应 typed grant"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence={
                "event-current": normalized["memories"][0]["evidence"]
            },
        )

    normalized = _normalized()
    unrelated = "黎雁确认大厅门已经锁好，裴衡随后告诉褚蓝密钥在甲库"
    normalized["events"][0]["evidence"] = unrelated
    normalized["memories"][0]["evidence"] = unrelated
    with pytest.raises(ServiceError, match="角色知识未绑定对应 typed grant"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence={"event-current": unrelated},
        )

    normalized = _normalized()
    wrong_recipient = "裴衡告诉褚蓝密钥在甲库，黎雁站在门外"
    normalized["events"][0]["evidence"] = wrong_recipient
    normalized["memories"][0]["evidence"] = wrong_recipient
    with pytest.raises(ServiceError, match="角色知识未绑定对应 typed grant"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence={"event-current": wrong_recipient},
        )

    normalized = _normalized()
    unrelated_suffix = "黎雁确认大厅门已经锁好，密钥其实藏在甲库"
    normalized["events"][0]["evidence"] = unrelated_suffix
    normalized["memories"][0]["evidence"] = unrelated_suffix
    with pytest.raises(ServiceError, match="角色知识未绑定对应 typed grant"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence={"event-current": unrelated_suffix},
        )

    normalized = _normalized()
    normalized["memories"] = []
    payload = build_candidate_payload(
        normalized,
        [_anchor()],
        _characters(),
        strict=True,
        memory_character_bindings={},
        occurred_event_evidence=_event_evidence(),
    )
    assert payload.memories == []


def test_knowledge_bindings_map_canon_ids_to_persisted_story_characters():
    bindings = knowledge_character_bindings(
        {
            "entities": [
                {"id": "li-yan", "kind": "character", "name": "黎雁"},
                {"id": "pei-heng", "kind": "character", "name": "裴衡"},
            ]
        },
        {
            "knowledge_grants": [
                {
                    "character_id": "li-yan",
                    "fact_id": "fact-key-received",
                    "source_event_id": "event-current",
                },
            ]
        },
        [
            {
                "character_business_id": "uuid-li-yan",
                "name": "黎雁-极昼邮路验收",
            }
        ],
    )

    assert bindings == {
        "uuid-li-yan": {
            "typed_character_id": "li-yan",
            "names": ["黎雁"],
            "grants": [
                {
                    "character_id": "li-yan",
                    "fact_id": "fact-key-received",
                    "source_event_id": "event-current",
                }
            ],
        }
    }
    normalized = _normalized()
    normalized["memories"][0].update(
        character_business_id="uuid-li-yan",
        virtual_ip_business_id="vip-li-yan",
        typed_character_id="li-yan",
    )
    normalized["events"][0]["participant_character_ids"] = []
    payload = build_candidate_payload(
        normalized,
        [_anchor()],
        [
            {
                "character_business_id": "uuid-li-yan",
                "virtual_ip_business_id": "vip-li-yan",
                "name": "黎雁-极昼邮路验收",
            }
        ],
        strict=True,
        memory_character_bindings=bindings,
        occurred_event_evidence=_event_evidence(),
    )
    assert payload.memories[0].candidate_evidence["typed_character_id"] == "li-yan"


def test_knowledge_bindings_fail_closed_when_story_character_is_missing():
    with pytest.raises(ServiceError, match="无法唯一映射 StoryCharacter"):
        knowledge_character_bindings(
            {
                "entities": [
                    {"id": "li-yan", "kind": "character", "name": "黎雁"},
                    {"id": "pei-heng", "kind": "character", "name": "裴衡"},
                ]
            },
            {
                "knowledge_grants": [
                    {
                        "character_id": "li-yan",
                        "fact_id": "fact-a",
                        "source_event_id": "event-a",
                    },
                    {
                        "character_id": "pei-heng",
                        "fact_id": "fact-b",
                        "source_event_id": "event-b",
                    },
                ]
            },
            [{"character_business_id": "uuid-li", "name": "黎雁"}],
        )
