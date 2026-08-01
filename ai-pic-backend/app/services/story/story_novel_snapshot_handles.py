"""Replace revision entity IDs with call-local snapshot handles."""

from __future__ import annotations

import copy


def localize_ids(value, reverse_entities):
    if isinstance(value, str):
        return reverse_entities.get(value, value)
    if isinstance(value, list):
        return [localize_ids(item, reverse_entities) for item in value]
    if isinstance(value, dict):
        return {
            key: localize_ids(item, reverse_entities) for key, item in value.items()
        }
    return copy.deepcopy(value)


def visible_snapshot_entities(context: dict, hard: dict) -> list[dict]:
    rows = list((hard.get("compiled_canon") or {}).get("entities") or [])
    known = {item["id"] for item in rows}
    local = (context.get("state_before") or {}).get("revision_local_entities") or {}
    rows.extend(
        copy.deepcopy(local[entity_id])
        for entity_id in sorted(local)
        if entity_id not in known
    )
    return rows
