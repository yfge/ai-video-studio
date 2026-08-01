"""Genre-defined revision-local scope graph derived from location entities."""

from __future__ import annotations

import copy

from .story_novel_context_utils import value_hash


def initial_scope_graph(canon: dict) -> dict | None:
    nodes = {}
    for item in canon.get("entities") or []:
        attributes = item.get("attributes") or {}
        if item.get("kind") != "location" or not attributes.get("scope_type"):
            continue
        nodes[item["id"]] = _node(item)
    if not nodes:
        return None
    graph = {"nodes": nodes, "edges": {}}
    for item in canon.get("entities") or []:
        if item.get("id") not in nodes:
            continue
        for connection in (item.get("attributes") or {}).get("connections") or []:
            target = connection.get("to_scope_id")
            if target not in nodes:
                continue
            payload = {
                "from_scope_id": item["id"],
                "to_scope_id": target,
                "connection_type": connection.get("connection_type"),
                "direction": connection.get("direction") or "two_way",
                "cost": copy.deepcopy(connection.get("cost") or {}),
                "duration": copy.deepcopy(connection.get("duration") or {}),
                "available_from_position": int(
                    connection.get("available_from_position") or 1
                ),
            }
            edge_id = str(
                connection.get("edge_id") or f"edge-{value_hash(payload)[:16]}"
            )
            graph["edges"].setdefault(edge_id, {"edge_id": edge_id, **payload})
    return graph


def validate_scope_introduction(state: dict, item: dict) -> list[str]:
    attributes = item.get("attributes") or {}
    if item.get("kind") != "location" or not attributes.get("scope_type"):
        return []
    graph = state.get("scope_graph") or {"nodes": {}, "edges": {}}
    parent = attributes.get("parent_scope_id")
    if parent and parent not in graph.get("nodes", {}):
        return [f"新范围父节点不存在: {parent}"]
    expected_depth = (
        int((graph["nodes"].get(parent) or {}).get("depth") or 0) + 1 if parent else 0
    )
    if int(attributes.get("depth") or 0) != expected_depth:
        return [f"新范围 depth 与父节点不连续: {item.get('id')}"]
    errors = []
    known = {*graph.get("nodes", {}), item.get("id")}
    for connection in attributes.get("connections") or []:
        if not isinstance(connection, dict):
            errors.append("范围 connection 必须是对象")
            continue
        target = connection.get("to_scope_id") or connection.get("to_scope_handle")
        if target not in known or not str(connection.get("connection_type") or ""):
            errors.append(f"范围 connection 终点或类型无效: {target}")
    return errors


def apply_scope_introduction(state: dict, item: dict) -> None:
    attributes = item.get("attributes") or {}
    if item.get("kind") != "location" or not attributes.get("scope_type"):
        return
    graph = state.setdefault("scope_graph", {"nodes": {}, "edges": {}})
    graph.setdefault("nodes", {}).setdefault(item["id"], _node(item))
    edges = graph.setdefault("edges", {})
    for connection in attributes.get("connections") or []:
        target = connection.get("to_scope_id") or connection.get("to_scope_handle")
        payload = {
            "from_scope_id": item["id"],
            "to_scope_id": target,
            "connection_type": connection["connection_type"],
            "direction": connection.get("direction") or "two_way",
            "cost": copy.deepcopy(connection.get("cost") or {}),
            "duration": copy.deepcopy(connection.get("duration") or {}),
            "available_from_position": int(item["first_appearance_position"]),
        }
        edge_id = str(connection.get("edge_id") or f"edge-{value_hash(payload)[:16]}")
        edges.setdefault(edge_id, {"edge_id": edge_id, **payload})


def _node(item: dict) -> dict:
    attributes = item.get("attributes") or {}
    return {
        "scope_id": item["id"],
        "scope_type": attributes["scope_type"],
        "display_name": item.get("name"),
        "parent_scope_id": attributes.get("parent_scope_id"),
        "depth": int(attributes.get("depth") or 0),
        "first_allowed_position": int(item.get("first_appearance_position") or 1),
        "visibility": "visited",
        "governing_entities": copy.deepcopy(attributes.get("governing_entities") or []),
        "local_rules": copy.deepcopy(attributes.get("local_rules") or []),
        "state": {},
    }
