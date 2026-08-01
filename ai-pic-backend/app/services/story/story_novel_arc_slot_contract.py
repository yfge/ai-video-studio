"""Validate current-arc chapter refinements and slot instantiations."""

from __future__ import annotations

from app.schemas.story_seed import StorySeedStructuredChapter
from app.utils.json_utils import extract_json_block


def parse_arc_package(
    text: str, source_rows: list[dict], target: dict, world_context: dict | None = None
) -> dict:
    payload = extract_json_block(text) or {}
    if set(payload) != {"chapters", "character_slots", "scope_slots"}:
        raise ValueError("Arc Plan 只能包含 chapters/character_slots/scope_slots")
    chapters = [
        StorySeedStructuredChapter.model_validate(item).model_dump()
        for item in payload["chapters"]
    ]
    _validate_chapters(chapters, source_rows)
    characters = _character_slots(payload["character_slots"], target)
    scopes = _scope_slots(payload["scope_slots"], target, world_context or {})
    names = [item["name"] for item in [*characters, *scopes]]
    if len(names) != len(set(names)):
        raise ValueError("Arc Plan 实例化实体名称不得重复")
    return {
        "chapters": chapters,
        "instantiated_character_slots": characters,
        "instantiated_scope_slots": scopes,
    }


def _validate_chapters(chapters, source_rows):
    if [item["position"] for item in chapters] != [
        int(item["position"]) for item in source_rows
    ]:
        raise ValueError("Arc Plan 章节位置不连续")
    frozen_keys = (
        "title",
        "goal",
        "key_events",
        "character_focus",
        "open_threads",
        "end_state",
    )
    for result, source in zip(chapters, source_rows, strict=True):
        if any(result[key] != source.get(key) for key in frozen_keys):
            raise ValueError("Arc Plan 不得改写冻结章节骨架或借此引入实体")


def _character_slots(value, target):
    allowed = {item["slot_id"]: item for item in target.get("character_slots") or []}
    rows = list(value or [])
    _validate_slot_ids(rows, allowed, "人物")
    result = []
    for item in rows:
        slot_id = item["slot_id"]
        position = _slot_position(item, target, "人物")
        capabilities = _strings(item.get("capabilities"))
        if not set(allowed[slot_id].get("required_capabilities") or []).issubset(
            capabilities
        ):
            raise ValueError("人物槽缺少预定能力")
        result.append(
            {
                "slot_id": slot_id,
                "mandatory": bool(allowed[slot_id].get("mandatory")),
                "kind": "character",
                "first_appearance_position": position,
                "name": _text(item, "name"),
                "profile": _text(item, "profile"),
                "narrative_function": allowed[slot_id]["narrative_function"],
                "relationship_target": allowed[slot_id].get("relationship_target"),
                "relationship": _text(item, "relationship"),
                "capabilities": capabilities,
                "resources": _strings(item.get("resources")),
                "knowledge_boundary": _strings(item.get("knowledge_boundary")),
                "arc_direction": _text(item, "arc_direction"),
            }
        )
    return result


def _scope_slots(value, target, world_context):
    allowed = {item["slot_id"]: item for item in target.get("scope_slots") or []}
    rows = list(value or [])
    _validate_slot_ids(rows, allowed, "范围")
    result = []
    for item in rows:
        frozen = allowed[item["slot_id"]]
        frozen_parent = frozen.get("parent_scope_id")
        proposed_parent = str(item.get("parent_scope_id") or "").strip() or None
        proposed_parent = (world_context.get("scope_handles") or {}).get(
            proposed_parent, proposed_parent
        )
        if frozen_parent and proposed_parent and proposed_parent != frozen_parent:
            raise ValueError("范围槽不得改写 Roadmap 冻结父范围")
        result.append(
            {
                "slot_id": item["slot_id"],
                "mandatory": bool(frozen.get("mandatory")),
                "kind": "location",
                "first_appearance_position": _slot_position(item, target, "范围"),
                "name": _text(item, "name"),
                "narrative_function": frozen["narrative_function"],
                "scope_type": _text(item, "scope_type"),
                "parent_scope_id": frozen_parent or proposed_parent,
                "connection_type": str(item.get("connection_type") or "").strip(),
            }
        )
    _validate_scope_hierarchy(result, world_context)
    return result


def _validate_scope_hierarchy(rows, context):
    taxonomy = {item["type_id"]: item for item in context.get("scope_taxonomy") or []}
    nodes = {item["scope_id"]: item for item in context.get("scope_nodes") or []}
    slots = {item["slot_id"]: item for item in rows}
    for item in rows:
        scope_type = item["scope_type"]
        if taxonomy and scope_type not in taxonomy:
            raise ValueError(f"范围槽使用未知 scope_type: {scope_type}")
        item["parent_scope_id"] = _resolve_parent(item, taxonomy, nodes, slots)
    for item in rows:
        parent_id = item.get("parent_scope_id")
        parent = nodes.get(parent_id) or slots.get(parent_id)
        if parent_id and parent is None:
            raise ValueError(f"范围槽父范围不存在: {parent_id}")
        parent_type = (parent or {}).get("scope_type")
        required_parent_type = (taxonomy.get(item["scope_type"]) or {}).get(
            "parent_type_id"
        )
        if required_parent_type and parent_type != required_parent_type:
            raise ValueError(f"范围槽 scope_type 与父范围类型不匹配: {item['slot_id']}")
    for item in rows:
        item["depth"] = _derived_depth(item, nodes, slots, set())


def _resolve_parent(item, taxonomy, nodes, slots):
    parent_id = item.get("parent_scope_id")
    if parent_id:
        return parent_id
    required = (taxonomy.get(item["scope_type"]) or {}).get("parent_type_id")
    if not required:
        return None
    candidates = [
        key
        for key, parent in {**nodes, **slots}.items()
        if key != item["slot_id"] and parent.get("scope_type") == required
    ]
    if len(candidates) != 1:
        raise ValueError(f"范围槽父范围不明确: {item['slot_id']}")
    return candidates[0]


def _derived_depth(item, nodes, slots, visiting):
    item_id = item["slot_id"]
    if item_id in visiting:
        raise ValueError(f"范围槽层级存在循环: {item_id}")
    parent_id = item.get("parent_scope_id")
    if not parent_id:
        return 0
    parent = nodes.get(parent_id) or slots.get(parent_id)
    if parent is None:
        raise ValueError(f"范围槽父范围不存在: {parent_id}")
    if parent_id in nodes:
        return int(parent.get("depth") or 0) + 1
    return _derived_depth(parent, nodes, slots, {*visiting, item_id}) + 1


def _validate_slot_ids(rows, allowed, label):
    if any(not isinstance(item, dict) for item in rows):
        raise ValueError(f"{label}槽实例必须是对象")
    ids = [str(item.get("slot_id") or "") for item in rows]
    required = {key for key, item in allowed.items() if item.get("mandatory")}
    if (
        len(ids) != len(set(ids))
        or not set(ids).issubset(allowed)
        or not required.issubset(ids)
    ):
        raise ValueError(f"{label}槽 ID 重复、未知或遗漏 mandatory 槽")


def _slot_position(item, target, label):
    position = _nonnegative_int(item, "first_appearance_position")
    if not int(target["start_position"]) <= position <= int(target["end_position"]):
        raise ValueError(f"{label}槽登场章超出当前卷")
    return position


def _nonnegative_int(item, key):
    value = item.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} 必须是非负整数")
    return value


def _strings(value):
    result = [str(item).strip() for item in value or []]
    if any(not item for item in result) or len(result) != len(set(result)):
        raise ValueError("槽实例数组必须非空且不重复")
    return result


def _text(item, key):
    result = str(item.get(key) or "").strip()
    if not result:
        raise ValueError(f"{key} 不能为空")
    return result
