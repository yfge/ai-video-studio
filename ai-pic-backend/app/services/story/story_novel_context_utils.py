"""Pure helpers for bounded long-form chapter context packs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

CONTEXT_CHAR_BUDGET = 32_000
CHAPTER_RUNTIME_FIELDS = {
    "actual_chars",
    "generation_status",
    "context_hash",
    "body_hash",
    "source_hash",
    "extraction_status",
    "event_ids",
    "fact_ids",
    "memory_ids",
}


def json_text(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def value_hash(value: Any) -> str:
    return hashlib.sha256(json_text(value).encode()).hexdigest()


def stable_canon(value: dict | None) -> dict:
    result = dict(value or {})
    snapshots = []
    for raw in result.get("character_snapshots") or []:
        item = dict(raw)
        item.pop("snapshot_business_id", None)
        snapshots.append(item)
    result["character_snapshots"] = snapshots
    return result


def prompt_chapter_contract(value: dict) -> dict:
    return {
        key: item for key, item in value.items() if key not in CHAPTER_RUNTIME_FIELDS
    }


def frozen_story_contract(snapshot: dict) -> dict:
    keys = (
        "business_id",
        "title",
        "genre",
        "target_audience",
        "story_seed_version",
        "memory_ledger_version",
        "memory_ledger_hash",
    )
    seed = snapshot.get("story_seed") or {}
    seed_keys = (
        "schema",
        "title",
        "target_audience",
    )
    return {
        **{key: snapshot.get(key) for key in keys},
        "story_seed_invariants": {
            key: seed.get(key) for key in seed_keys if seed.get(key) is not None
        },
        "outline_scope": "current_chapter_contract_only",
    }


def add_bounded(pack: dict, key: str, value: Any, truncations: list[dict]) -> None:
    if len(json_text({**pack, key: value})) <= CONTEXT_CHAR_BUDGET:
        pack[key] = value
        return
    source = json_text(value)
    low, high, best = 0, len(source), ""
    while low <= high:
        middle = (low + high) // 2
        clipped = {"truncated": True, "content": source[:middle]}
        if len(json_text({**pack, key: clipped})) <= CONTEXT_CHAR_BUDGET:
            best = source[:middle]
            low = middle + 1
        else:
            high = middle - 1
    clipped_value = {"truncated": True, "content": best}
    if len(json_text({**pack, key: clipped_value})) <= CONTEXT_CHAR_BUDGET:
        pack[key] = clipped_value
    truncations.append(
        {"section": key, "original_chars": len(source), "kept_chars": len(best)}
    )


def rolling_state(prior_ledger: dict) -> dict:
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


def prompt_safe_prior_ledger(prior_ledger: dict) -> dict:
    """Expose prior deltas and hashes without replaying full Canon state snapshots."""
    allowed = {
        "status",
        "chapter_business_id",
        "body_hash",
        "source_hash",
        "char_count",
        "canon_hash",
        "context_hash",
        "state_before_hash",
        "state_after_hash",
        "state_delta",
        "state_validation",
        "plot_delta",
        "plot_delta_source",
        "plot_delta_version",
        "body_repair_count",
        "state_extraction_repair_count",
        "extraction_status",
        "event_ids",
        "memory_ids",
    }
    return {
        key: {name: value for name, value in entry.items() if name in allowed}
        for key, entry in prior_ledger.items()
    }


def recent_chapter_rows(previous: list) -> list[dict]:
    return [
        {
            "business_id": item.business_id,
            "position": item.position,
            "title": item.title,
            "content_hash": item.content_hash,
        }
        for item in previous[-6:]
    ]
