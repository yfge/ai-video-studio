"""Freeze scope graph evidence and call-local handles for Arc planning."""

from __future__ import annotations

import copy


def scope_world_context(plan: dict, snapshot: dict) -> dict:
    if snapshot.get("scope_context"):
        return copy.deepcopy(snapshot["scope_context"])
    nodes = list((plan.get("scope_graph") or {}).get("nodes") or [])
    state = (snapshot.get("execution_context") or {}).get("state_before") or {}
    for entity in (state.get("revision_local_entities") or {}).values():
        attributes = entity.get("attributes") or {}
        slot_id = attributes.get("slot_id")
        if entity.get("kind") != "location" or not slot_id:
            continue
        nodes.append(
            {
                "scope_id": slot_id,
                "scope_type": attributes.get("scope_type"),
                "depth": attributes.get("depth"),
            }
        )
    return {
        "scope_taxonomy": (plan.get("scope_graph") or {}).get("taxonomy") or [],
        "scope_nodes": nodes,
        "scope_handles": _scope_handles(snapshot, nodes),
    }


def _scope_handles(snapshot: dict, nodes: list[dict]) -> dict:
    bindings = (snapshot.get("handle_bindings") or {}).get("entities") or {}
    result = {
        handle: entity_id
        for handle, entity_id in bindings.items()
        if str(handle).startswith("S")
    }
    for visible in (snapshot.get("model_input") or {}).get(
        "visible_characters_and_world"
    ) or []:
        handle = visible.get("entity_handle")
        if not str(handle).startswith("S") or handle in result:
            continue
        scope_type = (visible.get("attributes") or {}).get("scope_type")
        candidates = [
            item["scope_id"]
            for item in nodes
            if item.get("display_name") == visible.get("name")
            and item.get("scope_type") == scope_type
        ]
        if len(candidates) == 1:
            result[handle] = candidates[0]
    return result
