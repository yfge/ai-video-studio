from types import SimpleNamespace

from app.services.narrative_memory.candidate_verification import (
    verified_novel_candidate,
)
from app.services.story.story_novel_sentence_spans import resolve_sentence_refs


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
            "verification_version": 4,
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
            "verification_version": 4,
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
            "knowledge_evidence": {
                "canon-li-yan|fact-key-received|event-current": quote
            },
        },
    }

    assert verified_novel_candidate(
        memory, chapter, entry, require_ledger_membership=True
    )
    memory.candidate_evidence["typed_fact_id"] = "future-fact"
    assert not verified_novel_candidate(
        memory, chapter, entry, require_ledger_membership=True
    )


def test_v3_sentence_spans_revalidate_exact_short_fragments_without_legacy_rewrite():
    body = "“我签。”沈禾按下手印。里正收起契纸。"
    proof = resolve_sentence_refs(body, ["S0001", "S0002"])
    chapter = SimpleNamespace(
        business_id="chapter-v3",
        position=1,
        title="第一章",
        content_text=body,
        content_hash="body-hash",
    )
    event = SimpleNamespace(
        business_id="candidate-v3",
        summary=proof["quote"],
        source_artifact_business_id=chapter.business_id,
        source_hash=None,
        candidate_evidence={
            "source_quote": proof["quote"],
            "source_quote_verified": True,
            "claim_verified": True,
            "claim_mode": "extractive",
            "verification_version": 4,
            "participant_binding_verified": True,
            "typed_event_ids": ["event-current"],
            "sentence_ids": proof["sentence_ids"],
            "spans": proof["spans"],
            "sentence_index_hash": proof["sentence_index_hash"],
        },
    )
    from app.services.narrative_memory.source_hash import novel_chapter_source_hash

    event.source_hash = novel_chapter_source_hash(chapter)
    entry = {
        "event_ids": [event.business_id],
        "state_delta": {
            "occurred_event_ids": ["event-current"],
            "evidence": {"event-current": proof["quote"]},
        },
    }

    assert verified_novel_candidate(
        event, chapter, entry, require_ledger_membership=True
    )
    event.candidate_evidence["spans"][0]["start"] += 1
    assert not verified_novel_candidate(
        event, chapter, entry, require_ledger_membership=True
    )
