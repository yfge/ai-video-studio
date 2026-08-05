from types import SimpleNamespace

from app.services.story.story_novel_v3_candidate_evidence import (
    memory_evidence,
    participant_ids,
)
from app.services.story.story_novel_v3_candidates import _payload_memory_grant_keys


def test_event_participants_require_typed_event_binding_and_source_name():
    entry = {
        "state_delta": {
            "knowledge_grants": [
                {
                    "character_id": "char-a",
                    "fact_id": "fact-event-1-1",
                    "source_event_id": "event-1",
                },
                {
                    "character_id": "char-b",
                    "fact_id": "fact-event-2-1",
                    "source_event_id": "event-2",
                },
            ]
        }
    }
    characters = [
        {
            "character_business_id": "business-a",
            "canon_character_id": "char-a",
            "name": "沈禾",
        },
        {
            "character_business_id": "business-b",
            "canon_character_id": "char-b",
            "name": "顾砚",
        },
        {
            "character_business_id": "business-unbound",
            "canon_character_id": None,
            "name": "里正",
        },
    ]

    assert participant_ids(
        "event-1", "沈禾向顾砚和里正说明了发现。", entry, characters
    ) == ["business-a"]
    assert participant_ids("event-1", "她向众人说明了发现。", entry, characters) == []


def test_memory_evidence_matches_typed_grant_when_binding_adds_evidence():
    raw_grant = {
        "character_id": "char-a",
        "fact_id": "fact-event-1-1",
        "source_event_id": "event-1",
    }
    bound_grant = {**raw_grant, "evidence": "沈禾看过田契。"}
    entry = {
        "state_delta": {"knowledge_grants": [raw_grant]},
        "proof_spans": [
            {
                "contract_id": "knowledge:1",
                "sentence_ids": ["S0001"],
                "spans": [{"start": 0, "end": 8}],
            }
        ],
        "sentence_index_hash": "sentences",
        "chapter_brief": {"character_motivations": []},
    }
    revision = SimpleNamespace(generation_plan={"canon": {"character_arcs": []}})

    result = memory_evidence(
        revision,
        SimpleNamespace(position=1),
        bound_grant,
        "沈禾看过田契。",
        entry,
    )

    assert result["typed_character_id"] == "char-a"
    assert result["sentence_ids"] == ["S0001"]


def test_candidate_completeness_freezes_only_persistable_memory_grants():
    payload = SimpleNamespace(
        memories=[
            SimpleNamespace(
                candidate_evidence={
                    "typed_character_id": "char-a",
                    "typed_fact_id": "fact-a",
                    "typed_source_event_id": "event-a",
                }
            )
        ]
    )

    assert _payload_memory_grant_keys(payload) == {("char-a", "fact-a", "event-a")}
