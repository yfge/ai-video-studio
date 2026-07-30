"""Source-bound evidence and character-arc intent for deterministic candidates."""

import re

from app.core.exceptions import ServiceError
from app.services.narrative_memory.extraction_candidates import (
    CLAIM_VERIFICATION_VERSION,
)
from app.services.narrative_memory.knowledge_evidence import knowledge_grant_key


def event_evidence(event_id, quote, entry):
    proof = _proof(entry, f"event:{event_id}")
    return {
        "source_quote": quote,
        "source_quote_verified": True,
        "claim_verified": True,
        "claim_mode": "extractive",
        "verification_version": CLAIM_VERIFICATION_VERSION,
        "participant_binding_verified": True,
        "typed_event_ids": [event_id],
        "sentence_ids": proof["sentence_ids"],
        "spans": proof["spans"],
        "sentence_index_hash": entry["sentence_index_hash"],
    }


def memory_evidence(revision, chapter, grant, quote, entry):
    grant_key = knowledge_grant_key(grant)
    index = next(
        (
            index
            for index, item in enumerate(
                entry["state_delta"]["knowledge_grants"], start=1
            )
            if knowledge_grant_key(item) == grant_key
        ),
        None,
    )
    if index is None:
        raise ServiceError("v3 memory grant 不属于 expected delta")
    proof = _proof(entry, f"knowledge:{index}")
    intent = _memory_intent(revision, chapter.position, grant, entry)
    return {
        "source_quote": quote,
        "source_quote_verified": True,
        "claim_verified": True,
        "claim_mode": "typed_state_bound",
        "verification_version": CLAIM_VERIFICATION_VERSION,
        "typed_state_binding_verified": True,
        "typed_character_id": grant["character_id"],
        "typed_fact_id": grant["fact_id"],
        "typed_source_event_id": grant["source_event_id"],
        "sentence_ids": proof["sentence_ids"],
        "spans": proof["spans"],
        "sentence_index_hash": entry["sentence_index_hash"],
        "memory_intent": intent,
        "growth_delta": (
            {"arc_state": intent["arc_state"]} if intent.get("arc_state") else None
        ),
    }


def participant_ids(
    event_id: str, quote: str, entry: dict, characters: list[dict]
) -> list[str]:
    compact = re.sub(r"\s+", "", quote)
    bound = {
        item.get("character_id")
        for item in (entry.get("state_delta") or {}).get("knowledge_grants") or []
        if item.get("source_event_id") == event_id
    }
    return [
        item["character_business_id"]
        for item in characters
        if item.get("canon_character_id") in bound
        and re.sub(r"\s+", "", item["name"]) in compact
    ]


def _memory_intent(revision, position: int, grant: dict, entry: dict) -> dict:
    character_id = grant["character_id"]
    motivations = (entry.get("chapter_brief") or {}).get("character_motivations") or []
    motivation = next(
        (
            item.get("motivation")
            for item in motivations
            if item.get("character_id") == character_id
        ),
        None,
    )
    arcs = ((revision.generation_plan or {}).get("canon") or {}).get(
        "character_arcs"
    ) or []
    arc = next((item for item in arcs if item.get("character_id") == character_id), {})
    arc_state = next(
        (
            item.get("state")
            for item in arc.get("checkpoints") or []
            if int(item.get("position") or 0) == position
        ),
        None,
    )
    return {
        "motivation": motivation,
        "emotional_continuity": (entry.get("chapter_brief") or {}).get(
            "emotional_continuity"
        ),
        "arc_state": arc_state,
    }


def _proof(entry, contract_id):
    proof = next(
        (
            item
            for item in entry.get("proof_spans") or []
            if item["contract_id"] == contract_id
        ),
        None,
    )
    if proof is None:
        raise ServiceError(f"v3 proof 缺失: {contract_id}")
    return proof
