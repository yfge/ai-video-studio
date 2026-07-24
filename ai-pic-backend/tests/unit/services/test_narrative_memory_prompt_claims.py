from types import SimpleNamespace

from app.services.narrative_memory.candidate_verification import (
    verified_novel_candidate,
)


def test_prompt_boundary_revalidates_claim_quote_and_ledger_id():
    chapter = SimpleNamespace(
        business_id="chapter-a",
        position=1,
        title="第一章",
        content_text="黎雁接过零号风钥。黎雁确认移交完成。",
        content_hash="body-hash",
    )
    event = SimpleNamespace(
        business_id="candidate-a",
        summary="黎雁接过零号风钥",
        source_artifact_business_id="chapter-a",
        source_hash=None,
        candidate_evidence={
            "source_quote": "黎雁接过零号风钥",
            "source_quote_verified": True,
            "claim_verified": True,
            "claim_mode": "extractive",
            "verification_version": 3,
            "participant_binding_verified": True,
            "typed_event_ids": ["event-current"],
        },
    )
    from app.services.narrative_memory.source_hash import novel_chapter_source_hash

    event.source_hash = novel_chapter_source_hash(chapter)
    entry = {
        "event_ids": ["candidate-a"],
        "state_delta": {
            "occurred_event_ids": ["event-current"],
            "evidence": {"event-current": "黎雁接过零号风钥"},
        },
    }

    assert verified_novel_candidate(
        event, chapter, entry, require_ledger_membership=True
    )
    event.summary = "岑野第48章死亡"
    assert not verified_novel_candidate(
        event, chapter, entry, require_ledger_membership=True
    )
    event.summary = "黎雁接过零号风钥"
    entry["event_ids"] = []
    assert not verified_novel_candidate(
        event, chapter, entry, require_ledger_membership=True
    )


def test_prompt_boundary_revalidates_typed_memory_grant():
    quote = "黎雁确认零号风钥移交完成"
    chapter = SimpleNamespace(
        business_id="chapter-a",
        position=1,
        title="第一章",
        content_text=quote,
        content_hash="body-hash",
    )
    memory = SimpleNamespace(
        business_id="memory-a",
        content=quote,
        source_artifact_business_id="chapter-a",
        source_hash=None,
        candidate_evidence={
            "source_quote": quote,
            "source_quote_verified": True,
            "claim_verified": True,
            "claim_mode": "typed_state_bound",
            "verification_version": 3,
            "typed_state_binding_verified": True,
            "typed_character_id": "canon-li-yan",
            "typed_fact_id": "fact-key-received",
            "typed_source_event_id": "event-current",
        },
    )
    from app.services.narrative_memory.source_hash import novel_chapter_source_hash

    memory.source_hash = novel_chapter_source_hash(chapter)
    entry = {
        "memory_ids": ["memory-a"],
        "state_delta": {
            "occurred_event_ids": ["event-current"],
            "knowledge_grants": [
                {
                    "character_id": "canon-li-yan",
                    "fact_id": "fact-key-received",
                    "source_event_id": "event-current",
                }
            ],
            "evidence": {"event-current": quote},
        },
    }

    assert verified_novel_candidate(
        memory, chapter, entry, require_ledger_membership=True
    )
    memory.candidate_evidence["typed_fact_id"] = "future-fact"
    assert not verified_novel_candidate(
        memory, chapter, entry, require_ledger_membership=True
    )
