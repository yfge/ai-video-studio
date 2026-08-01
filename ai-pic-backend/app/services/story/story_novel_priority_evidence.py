"""Keep planner-referenced evidence ahead of optional rolling context."""

from fastapi import HTTPException

from .story_novel_context_utils import CONTEXT_CHAR_BUDGET, json_text


def add_priority_evidence(pack, events, memories, priority_ids, truncations) -> None:
    available = {
        item.get("business_id")
        for item in [*events, *memories]
        if item.get("business_id") in priority_ids
    }
    _add_rows(
        pack,
        "world_events",
        [item for item in events if item.get("business_id") in priority_ids],
        truncations,
    )
    _add_rows(
        pack,
        "character_memories",
        [item for item in memories if item.get("business_id") in priority_ids],
        truncations,
    )
    kept = {
        item.get("business_id")
        for key in ("world_events", "character_memories")
        for item in pack.get(key) or []
    }
    if missing := available.difference(kept):
        raise HTTPException(
            status_code=500,
            detail=f"continuity watchpoint evidence 超过上下文预算: {sorted(missing)}",
        )


def append_unpinned_evidence(pack, key, rows, priority_ids, truncations) -> None:
    source = [item for item in rows if item.get("business_id") not in priority_ids]
    kept = list(pack.get(key) or [])
    original_items = len(kept) + len(source)
    for item in source:
        if len(json_text({**pack, key: [*kept, item]})) > CONTEXT_CHAR_BUDGET:
            break
        kept.append(item)
    pack[key] = kept
    if len(kept) != original_items:
        truncations.append(
            {"section": key, "original_items": original_items, "kept_items": len(kept)}
        )


def _add_rows(pack, key, rows, truncations) -> None:
    source, kept = list(rows or []), []
    for item in source:
        if len(json_text({**pack, key: [*kept, item]})) > CONTEXT_CHAR_BUDGET:
            break
        kept.append(item)
    pack[key] = kept
    if len(kept) != len(source):
        truncations.append(
            {"section": key, "original_items": len(source), "kept_items": len(kept)}
        )
