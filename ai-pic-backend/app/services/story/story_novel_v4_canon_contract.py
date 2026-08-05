"""Bind model-authored Canon entities to the frozen v4 StorySeed roadmap."""

from __future__ import annotations

import copy


def bind_seed_roadmap(payload: dict, planning_contract: dict) -> dict:
    outline = (planning_contract.get("story_seed") or {}).get(
        "structured_outline"
    ) or {}
    if int(outline.get("planning_structure_version") or 0) != 1:
        return payload
    result = copy.deepcopy(payload)
    entities = {
        str(item.get("id") or ""): item for item in result.get("entities") or []
    }
    initial = result.setdefault("initial_state", {})
    _bind_character_routes(
        entities, initial, outline.get("core_character_routes") or []
    )
    _bind_scope_nodes(entities, outline.get("initial_scope_nodes") or [])
    _bind_scope_edges(entities, outline.get("initial_scope_edges") or [])
    return result


def _bind_character_routes(entities, initial, routes):
    for route in routes:
        entity_id = str(route.get("character_ref") or "")
        entity = entities.get(entity_id)
        if not entity or entity.get("kind") != "character":
            raise ValueError(f"核心人物路线缺少 Canon character: {entity_id}")
        attributes = entity.setdefault("attributes", {})
        attributes.update(
            {
                key: copy.deepcopy(route.get(key))
                for key in (
                    "narrative_function",
                    "first_allowed_position",
                    "planned_arc_id",
                    "relationship_targets",
                    "start_direction",
                    "turning_directions",
                    "terminal_direction",
                )
            }
        )
        state = initial.setdefault(entity_id, {})
        for key, value in (route.get("hidden_state") or {}).items():
            if key in state and state[key] != value:
                raise ValueError(f"核心人物隐藏初态与 Canon 冲突: {entity_id}.{key}")
            state[key] = copy.deepcopy(value)


def _bind_scope_nodes(entities, nodes):
    for node in nodes:
        entity_id = str(node.get("scope_id") or "")
        entity = entities.get(entity_id)
        if not entity or entity.get("kind") != "location":
            raise ValueError(f"初始范围缺少 Canon location: {entity_id}")
        if str(entity.get("name") or "") != str(node.get("display_name") or ""):
            raise ValueError(f"初始范围名称与 Canon 冲突: {entity_id}")
        attributes = entity.setdefault("attributes", {})
        attributes.update(
            {
                "scope_type": node.get("scope_type"),
                "parent_scope_id": node.get("parent_scope_id"),
                "depth": int(node.get("depth") or 0),
                "first_allowed_position": int(node.get("first_allowed_position") or 1),
                "visibility": node.get("visibility") or "known",
                "governing_entities": copy.deepcopy(
                    node.get("governing_entities") or []
                ),
                "local_rules": copy.deepcopy(node.get("local_rules") or []),
            }
        )


def _bind_scope_edges(entities, edges):
    grouped: dict[str, list[dict]] = {}
    for edge in edges:
        grouped.setdefault(str(edge.get("from_scope_id") or ""), []).append(
            copy.deepcopy(edge)
        )
    for source_id, rows in grouped.items():
        entity = entities.get(source_id)
        if not entity or entity.get("kind") != "location":
            raise ValueError(f"范围连接起点缺少 Canon location: {source_id}")
        entity.setdefault("attributes", {})["connections"] = rows
