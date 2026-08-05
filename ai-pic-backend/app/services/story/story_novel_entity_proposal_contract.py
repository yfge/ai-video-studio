"""Parse revision-local entity proposals against one planner snapshot."""

from __future__ import annotations

import copy

ENTITY_KINDS = {"character", "location", "organization", "object", "concept"}


def parse_entity_proposals(value, model_input: dict) -> list[dict]:
    rows = list(value or [])
    if any(not isinstance(item, dict) for item in rows):
        raise ValueError("entity proposal 必须是对象")
    event_handles = {
        item["event_handle"] for item in model_input["current_chapter"]["events"]
    }
    handles = [_required_text(item, "proposal_handle") for item in rows]
    if len(handles) != len(set(handles)):
        raise ValueError("entity proposal handle 必须非空且不重复")
    available = set(model_input.get("allowed_entity_handles") or []) | set(handles)
    slots = {
        item["slot_id"]: item
        for item in model_input.get("authorized_entity_slots") or []
        if item.get("slot_id")
    }
    visible = {
        item["entity_handle"]: item
        for item in model_input.get("visible_characters_and_world") or []
        if item.get("entity_handle")
    }
    character_handles = {
        handle for handle, item in visible.items() if item.get("kind") == "character"
    }
    taxonomy = {
        item["type_id"]: item
        for item in model_input.get("scope_taxonomy") or []
        if item.get("type_id")
    }
    result = [
        _proposal(
            item,
            handle,
            available,
            event_handles,
            slots,
            visible,
            character_handles,
        )
        for item, handle in zip(rows, handles, strict=True)
    ]
    _require_mandatory_slots(result, slots)
    _validate_dynamic_scope_hierarchy(result, visible, taxonomy)
    return result


def _proposal(
    item, handle, available, event_handles, slots, visible, character_handles
):
    kind = _required_text(item, "kind")
    name = _required_text(item, "name")
    source = _required_text(item, "source_event_handle")
    function = _required_text(item, "narrative_function")
    transient = bool(item.get("transient", False))
    if kind not in ENTITY_KINDS or source not in event_handles:
        raise ValueError("entity proposal kind/source 无效")
    profile = str(item.get("profile") or "").strip()
    arc_direction = str(item.get("arc_direction") or "").strip()
    if kind == "character" and not transient and (not profile or not arc_direction):
        raise ValueError("持久人物 proposal 必须包含 profile 和 arc_direction")
    relationships = _relationships(
        item.get("relationship_intents"), character_handles, handle
    )
    result = {
        "proposal_handle": handle,
        "slot_id": str(item.get("slot_id") or "").strip() or None,
        "kind": kind,
        "name": name,
        "aliases": _strings(item.get("aliases")),
        "narrative_function": function,
        "source_event_handle": source,
        "transient": transient,
        "profile": profile,
        "relationship_intents": relationships,
        "capabilities": _strings(item.get("capabilities")),
        "resources": _strings(item.get("resources")),
        "knowledge_boundary": _strings(item.get("knowledge_boundary")),
        "arc_direction": arc_direction,
        "attributes": _attributes(item.get("attributes"), kind, available),
    }
    _validate_slot_match(result, slots, visible)
    return result


def _validate_slot_match(result, slots, visible):
    # A proposal without a slot remains a genuinely dynamic current-chapter proposal.
    if not result["slot_id"]:
        return
    slot = slots.get(result["slot_id"])
    if slot is None:
        raise ValueError("entity proposal 引用了未授权 slot_id")
    if result["transient"]:
        raise ValueError("Arc slot 实体不得标记为 transient")
    for key in ("kind", "name", "profile", "narrative_function", "arc_direction"):
        if str(result.get(key) or "") != str(slot.get(key) or ""):
            raise ValueError(f"entity proposal 与 Arc slot 的 {key} 不匹配")
    for key in ("capabilities", "resources", "knowledge_boundary"):
        if result[key] != list(slot.get(key) or []):
            raise ValueError(f"entity proposal 与 Arc slot 的 {key} 不匹配")
    target = slot.get("relationship_target_handle")
    if target:
        expected = [{"target_handle": target, "relationship": slot["relationship"]}]
        if result["relationship_intents"] != expected:
            raise ValueError("entity proposal 与 Arc slot 的关系合同不匹配")
    else:
        allowed = set(
            slot.get("allowed_relationship_target_handles")
            or [
                handle
                for handle, item in visible.items()
                if item.get("kind") == "character"
            ]
        )
        actual = {item["target_handle"] for item in result["relationship_intents"]}
        if not actual.issubset(allowed):
            raise ValueError("entity proposal 与 Arc slot 的关系合同不匹配")
    if result["kind"] == "location":
        _validate_scope_slot(result, slot)


def _validate_scope_slot(result, slot):
    attributes = result["attributes"]
    if (
        attributes.get("scope_type") != slot.get("scope_type")
        or int(attributes.get("depth", -1)) != int(slot.get("depth", -2))
        or attributes.get("parent_scope_id") != slot.get("parent_scope_handle")
    ):
        raise ValueError("范围 proposal 与 Arc slot 的层级合同不匹配")
    expected_type = str(slot.get("connection_type") or "")
    connections = list(attributes.get("connections") or [])
    actual_types = [str(item.get("connection_type") or "") for item in connections]
    if expected_type and actual_types != [expected_type]:
        raise ValueError("范围 proposal 与 Arc slot 的连接合同不匹配")
    parent = slot.get("parent_scope_handle")
    if expected_type and parent and connections[0].get("to_scope_id") != parent:
        raise ValueError("范围 proposal 的连接终点必须是 Arc slot 父范围")
    if not expected_type and connections:
        raise ValueError("Arc slot 未授权新范围连接")


def _require_mandatory_slots(rows, slots):
    required = {key for key, item in slots.items() if item.get("mandatory")}
    actual = {item.get("slot_id") for item in rows if item.get("slot_id")}
    if not required.issubset(actual):
        raise ValueError("当前章遗漏 mandatory Arc slot 实体提案")


def _validate_dynamic_scope_hierarchy(rows, visible, taxonomy):
    proposals = {item["proposal_handle"]: item for item in rows}
    for item in rows:
        attributes = item.get("attributes") or {}
        if item.get("kind") != "location" or not attributes.get("scope_type"):
            continue
        scope_type = attributes["scope_type"]
        if taxonomy and scope_type not in taxonomy:
            raise ValueError(f"新范围使用未知 scope_type: {scope_type}")
        parent_id = attributes.get("parent_scope_id")
        parent = visible.get(parent_id) or proposals.get(parent_id)
        parent_attributes = (parent or {}).get("attributes") or {}
        parent_depth = parent_attributes.get("depth")
        expected_depth = int(parent_depth) + 1 if parent is not None else 0
        if int(attributes.get("depth", -1)) != expected_depth:
            raise ValueError("新范围 depth 与父范围不连续")
        parent_type = parent_attributes.get("scope_type")
        required = (taxonomy.get(scope_type) or {}).get("parent_type_id")
        if required and parent_type != required:
            raise ValueError("新范围 scope_type 与父范围类型不匹配")


def _relationships(value, available, own_handle):
    rows = list(value or [])
    result = []
    for item in rows:
        keys = set(item) if isinstance(item, dict) else set()
        if keys == {"target_handle", "intent"}:
            item = {
                "target_handle": item["target_handle"],
                "relationship": item["intent"],
            }
        elif keys != {"target_handle", "relationship"}:
            raise ValueError(
                "relationship_intents 必须是数组，且每项只能包含 "
                "target_handle 与 relationship（兼容 intent）；不得使用对象映射"
            )
        target = _required_text(item, "target_handle")
        relationship = _required_text(item, "relationship")
        if target not in available or target == own_handle:
            raise ValueError("relationship target 必须是其他已授权 handle")
        result.append({"target_handle": target, "relationship": relationship})
    targets = [item["target_handle"] for item in result]
    if len(targets) != len(set(targets)):
        raise ValueError("同一人物关系目标不得重复")
    return result


def _attributes(value, kind: str, available: set[str]) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("entity proposal attributes 必须是对象")
    result = copy.deepcopy(value)
    if kind != "location" or not result.get("scope_type"):
        return result
    parent = result.get("parent_scope_id")
    depth = result.get("depth", 0)
    if parent is not None and parent not in available:
        raise ValueError("新范围 parent_scope_id 必须使用当前快照 handle")
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0:
        raise ValueError("新范围 depth 必须是非负整数")
    for connection in result.get("connections") or []:
        if not isinstance(connection, dict):
            raise ValueError("新范围 connection 必须是对象")
        target = connection.get("to_scope_id") or connection.get("to_scope_handle")
        if (
            target not in available
            or not str(connection.get("connection_type") or "").strip()
        ):
            raise ValueError("新范围 connection 必须绑定已授权 handle 和类型")
    return result


def _strings(value) -> list[str]:
    rows = [str(item).strip() for item in value or []]
    if any(not item for item in rows) or len(rows) != len(set(rows)):
        raise ValueError("字符串数组必须非空且不重复")
    return rows


def _required_text(value: dict, key: str) -> str:
    result = str(value.get(key) or "").strip()
    if not result:
        raise ValueError(f"{key} 不能为空")
    return result
