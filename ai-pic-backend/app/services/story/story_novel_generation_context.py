"""Bounded, reproducible context packs for sequential novel chapters."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_domain import active_chapters
from .story_novel_memory_context import chapter_memory_context

CONTEXT_CHAR_BUDGET = 32_000


def _json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def _stable_canon(value: dict | None) -> dict:
    result = dict(value or {})
    snapshots = []
    for raw in result.get("character_snapshots") or []:
        item = dict(raw)
        item.pop("snapshot_business_id", None)
        snapshots.append(item)
    result["character_snapshots"] = snapshots
    return result


def _frozen_story_contract(snapshot: dict) -> dict:
    keys = (
        "business_id",
        "title",
        "genre",
        "theme",
        "target_audience",
        "main_characters",
        "character_relationships",
        "setting_time",
        "setting_location",
        "world_building",
        "story_seed",
        "story_seed_version",
        "memory_ledger_version",
        "memory_ledger_hash",
    )
    return {key: snapshot.get(key) for key in keys}


def _add_bounded(pack: dict, key: str, value: Any, truncations: list[dict]) -> None:
    candidate = {**pack, key: value}
    if len(_json(candidate)) <= CONTEXT_CHAR_BUDGET:
        pack[key] = value
        return
    source = _json(value)
    low, high, best = 0, len(source), ""
    while low <= high:
        middle = (low + high) // 2
        clipped = {"truncated": True, "content": source[:middle]}
        if len(_json({**pack, key: clipped})) <= CONTEXT_CHAR_BUDGET:
            best = source[:middle]
            low = middle + 1
        else:
            high = middle - 1
    clipped_value = {"truncated": True, "content": best}
    if len(_json({**pack, key: clipped_value})) <= CONTEXT_CHAR_BUDGET:
        pack[key] = clipped_value
    truncations.append(
        {"section": key, "original_chars": len(source), "kept_chars": len(best)}
    )


def revision_local_candidates(
    db, revision, position: int
) -> tuple[list[dict], list[dict]]:
    prior = {
        item.business_id: item
        for item in active_chapters(revision)
        if item.position < position
    }
    source_hashes = {
        business_id: novel_chapter_source_hash(chapter)
        for business_id, chapter in prior.items()
    }
    repo = NarrativeMemoryRepository(db)
    events = [
        {
            "business_id": item.business_id,
            "source_chapter_business_id": item.source_artifact_business_id,
            "source_hash": item.source_hash,
            "event_type": item.event_type,
            "summary": item.summary,
            "participant_character_ids": item.participant_character_ids or [],
            "presentation": item.presentation,
            "audience_disclosure": item.audience_disclosure,
        }
        for item in repo.list_events(revision.story_id)
        if item.status in {"candidate", "approved"}
        and source_hashes.get(item.source_artifact_business_id) == item.source_hash
    ]
    memories = [
        {
            "business_id": item.business_id,
            "source_chapter_business_id": item.source_artifact_business_id,
            "source_hash": item.source_hash,
            "character_business_id": item.character_business_id,
            "memory_type": item.memory_type,
            "content": item.content,
            "belief": item.belief,
            "effective_from_anchor_business_id": item.effective_from_anchor_business_id,
            "growth_delta": (item.candidate_evidence or {}).get("growth_delta"),
        }
        for item in repo.list_private_memories(revision.story_id)
        if item.status in {"candidate", "approved"}
        and source_hashes.get(item.source_artifact_business_id) == item.source_hash
    ]
    return events, memories


def _rolling_state(prior_ledger: dict) -> dict:
    events: list[dict] = []
    unresolved: list[str] = []
    characters: dict[str, Any] = {}
    for key in sorted(prior_ledger, key=int):
        delta = prior_ledger[key].get("plot_delta") or {}
        resolved = set(delta.get("resolved_threads") or [])
        unresolved = [item for item in unresolved if item not in resolved]
        for item in delta.get("unresolved_threads") or []:
            if item not in unresolved:
                unresolved.append(item)
        events.extend(
            {"chapter": int(key), "event": item}
            for item in delta.get("key_events") or []
        )
        characters.update(delta.get("character_states") or {})
    return {
        "key_events": events,
        "unresolved_threads": unresolved,
        "character_states": characters,
    }


def build_chapter_context(service, revision, position: int, chapter_plan: dict) -> dict:
    """Build a <=32K character context and auditable evidence manifest."""
    previous = [item for item in active_chapters(revision) if item.position < position]
    events, memories = revision_local_candidates(service.db, revision, position)
    ledger = dict(revision.continuity_ledger or {})
    prior_ledger = {
        key: value
        for key, value in (ledger.get("chapters") or {}).items()
        if int(key) < position and value.get("status") != "stale"
    }
    truncations: list[dict] = []
    pack: dict[str, Any] = {}
    sections = [
        (
            "story_contract",
            _frozen_story_contract(revision.story_snapshot or {}),
        ),
        ("chapter_plan", chapter_plan),
        (
            "approved_story_canon",
            _stable_canon(chapter_memory_context(service.db, revision, position) or {}),
        ),
        (
            "revision_local_canon",
            {"events": events, "character_memories": memories},
        ),
        (
            "rolling_plot_ledger",
            {
                "current_state": _rolling_state(prior_ledger),
                "prior_chapters": prior_ledger,
            },
        ),
        (
            "recent_chapters",
            [
                {
                    "business_id": item.business_id,
                    "position": item.position,
                    "title": item.title,
                    "summary": item.summary,
                    "cliffhanger": item.cliffhanger,
                    "content_hash": item.content_hash,
                }
                for item in previous[-6:]
            ],
        ),
        (
            "previous_chapter_tail",
            previous[-1].content_text[-2400:] if previous else "",
        ),
    ]
    for key, value in sections:
        _add_bounded(pack, key, value, truncations)
    context_hash = hashlib.sha256(_json(pack).encode()).hexdigest()
    return {
        "context": pack,
        "evidence": {
            "context_hash": context_hash,
            "context_chars": len(_json(pack)),
            "chapter_ids": [item.business_id for item in previous],
            "chapter_hashes": [item.content_hash for item in previous],
            "event_ids": [item["business_id"] for item in events],
            "event_hashes": [item["source_hash"] for item in events],
            "memory_ids": [item["business_id"] for item in memories],
            "memory_hashes": [item["source_hash"] for item in memories],
            "truncations": truncations,
        },
    }
