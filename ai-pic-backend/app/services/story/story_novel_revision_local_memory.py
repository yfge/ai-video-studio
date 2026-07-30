"""Ledger-backed memories for characters introduced inside one novel revision."""

from __future__ import annotations

from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_context_utils import value_hash


def local_memory_rows(chapter, entry: dict) -> list[dict]:
    local_ids = set(
        ((entry.get("state_after") or {}).get("revision_local_entities") or {})
    )
    delta = entry.get("state_delta") or {}
    source_hash = novel_chapter_source_hash(chapter)
    rows = []
    for grant in delta.get("knowledge_grants") or []:
        if grant.get("character_id") not in local_ids:
            continue
        quote = str(
            (delta.get("knowledge_evidence") or {}).get(knowledge_evidence_key(grant))
            or ""
        ).strip()
        if not quote:
            continue
        identity = {
            "chapter": chapter.business_id,
            "character_id": grant["character_id"],
            "fact_id": grant["fact_id"],
            "source_event_id": grant["source_event_id"],
            "source_hash": source_hash,
        }
        rows.append(
            {
                "business_id": f"revision-memory-{value_hash(identity)[:24]}",
                "source_chapter_business_id": chapter.business_id,
                "source_hash": source_hash,
                "character_business_id": grant["character_id"],
                "memory_type": "witnessed",
                "content": quote,
                "belief": None,
                "effective_from_anchor_business_id": None,
                "growth_delta": None,
                "source_quote": quote,
                "revision_local": True,
                "typed_fact_id": grant["fact_id"],
                "typed_source_event_id": grant["source_event_id"],
            }
        )
    return rows


def prior_local_memories(revision, prior_chapters) -> list[dict]:
    ledger = (revision.continuity_ledger or {}).get("chapters") or {}
    by_position = {int(item.position): item for item in prior_chapters or []}
    result = []
    for position, chapter in sorted(by_position.items()):
        entry = ledger.get(str(position)) or {}
        source_hash = novel_chapter_source_hash(chapter)
        if entry.get("status") != "ready" or entry.get("source_hash") != source_hash:
            continue
        result.extend(
            item
            for item in entry.get("revision_local_memories") or []
            if item.get("source_chapter_business_id") == chapter.business_id
            and item.get("source_hash") == source_hash
        )
    return result
