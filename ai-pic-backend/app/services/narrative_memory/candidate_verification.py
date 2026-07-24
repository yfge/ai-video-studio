"""Revalidate extractive novel candidates at prompt and approval boundaries."""

from __future__ import annotations

import re

from app.services.narrative_memory.extraction_candidates import (
    CLAIM_VERIFICATION_VERSION,
)
from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key
from app.services.narrative_memory.source_evidence import source_contains_evidence
from app.services.narrative_memory.source_hash import novel_chapter_source_hash


def verified_novel_candidate(
    entity,
    chapter,
    entry: dict,
    *,
    require_ledger_membership: bool,
) -> bool:
    evidence = dict(entity.candidate_evidence or {})
    quote = evidence.get("source_quote")
    is_event = hasattr(entity, "summary")
    claim_mode = "extractive" if is_event else "typed_state_bound"
    ledger_key = "event_ids" if is_event else "memory_ids"
    if (
        entity.source_artifact_business_id != chapter.business_id
        or entity.source_hash != novel_chapter_source_hash(chapter)
        or evidence.get("source_quote_verified") is not True
        or evidence.get("claim_verified") is not True
        or evidence.get("claim_mode") != claim_mode
        or int(evidence.get("verification_version") or 0) < CLAIM_VERIFICATION_VERSION
        or not isinstance(quote, str)
        or len(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", quote)) < 3
        or not source_contains_evidence(
            f"{chapter.title}\n{chapter.content_text}", quote
        )
        or (
            require_ledger_membership
            and entity.business_id not in entry.get(ledger_key, [])
        )
    ):
        return False
    delta = entry.get("state_delta") or {}
    if is_event:
        typed_event_ids = list(evidence.get("typed_event_ids") or [])
        event_id = typed_event_ids[0] if len(typed_event_ids) == 1 else None
        return bool(
            entity.summary == quote
            and evidence.get("participant_binding_verified") is True
            and event_id in (delta.get("occurred_event_ids") or [])
            and _semantic(quote)
            == _semantic((delta.get("evidence") or {}).get(event_id) or "")
        )
    grant_key = (
        evidence.get("typed_character_id"),
        evidence.get("typed_fact_id"),
        evidence.get("typed_source_event_id"),
    )
    allowed_grants = {_grant_key(item) for item in delta.get("knowledge_grants") or []}
    grant_quote = (delta.get("knowledge_evidence") or {}).get(
        knowledge_evidence_key(
            {
                "character_id": grant_key[0],
                "fact_id": grant_key[1],
                "source_event_id": grant_key[2],
            }
        )
    )
    return bool(
        entity.content == quote
        and evidence.get("typed_state_binding_verified") is True
        and grant_key in allowed_grants
        and grant_key[2] in (delta.get("occurred_event_ids") or [])
        and _semantic(quote) == _semantic(grant_quote or "")
    )


def complete_novel_candidate_set(entry: dict, events: list, memories: list) -> bool:
    delta = entry.get("state_delta") or {}
    expected_events = set(delta.get("occurred_event_ids") or [])
    covered_events = {
        event_id
        for item in events
        for event_id in (item.candidate_evidence or {}).get("typed_event_ids") or []
    }
    expected_grants = (
        {tuple(item) for item in entry.get("memory_grant_keys") or []}
        if "memory_grant_keys" in entry
        else {_grant_key(item) for item in delta.get("knowledge_grants") or []}
    )
    covered_grants = {
        (
            evidence.get("typed_character_id"),
            evidence.get("typed_fact_id"),
            evidence.get("typed_source_event_id"),
        )
        for item in memories
        for evidence in [item.candidate_evidence or {}]
    }
    return expected_events == covered_events and expected_grants == covered_grants


def _grant_key(item: dict) -> tuple[str | None, str | None, str | None]:
    return (
        item.get("character_id"),
        item.get("fact_id"),
        item.get("source_event_id"),
    )


def _semantic(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
