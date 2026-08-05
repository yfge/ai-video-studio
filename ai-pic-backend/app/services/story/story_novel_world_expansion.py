"""Revision-local world expansion proposed by one chapter package."""

from __future__ import annotations

import copy

from .story_novel_initial_state import apply_subject_transition
from .story_novel_scope_graph import (
    apply_scope_introduction,
    validate_scope_introduction,
)
from .story_novel_world_order import stable_entity_id, validate_world_expansion_order

ENTITY_KINDS = {"character", "location", "object", "organization", "concept"}
_RAW_KEYS = {
    "ref",
    "kind",
    "name",
    "aliases",
    "attributes",
    "initial_state",
    "source_event_id",
    "persistence",
    "reason",
}


def normalize_package_expansion(
    contract: dict,
    brief: dict,
    canon: dict,
    state_before: dict,
) -> tuple[dict, dict]:
    """Assign stable IDs and replace response-local refs before Pydantic parsing."""
    result, model_brief = copy.deepcopy(contract), copy.deepcopy(brief)
    position = int(result["position"])
    raw_rows = list(result.get("entity_introductions") or [])
    known = world_entities(canon, state_before)
    known_names = _entity_names(known.values())
    known_functions = {_function_key(item) for item in known.values()} - {None}
    scope_state = copy.deepcopy(state_before)
    refs: dict[str, str] = {}
    rows = []
    for index, raw in enumerate(raw_rows, start=1):
        if not isinstance(raw, dict) or set(raw).difference(_RAW_KEYS):
            raise ValueError("entity_introductions 包含越界字段")
        kind = str(raw.get("kind") or "")
        name = str(raw.get("name") or "").strip()
        local_ref = str(raw.get("ref") or f"new-{index}").strip()
        source_event_id = str(raw.get("source_event_id") or "").strip()
        reason = str(raw.get("reason") or "").strip()
        if kind not in ENTITY_KINDS or not name or not local_ref or not reason:
            raise ValueError("持久世界实体必须包含 kind/name/ref/reason")
        if source_event_id not in set(result.get("required_event_ids") or []):
            raise ValueError(f"世界实体 {name} 未绑定当前章节事件")
        aliases = _strings(raw.get("aliases") or [], f"{name}.aliases")
        if {name, *aliases}.intersection(known_names):
            raise ValueError(f"世界实体已存在，必须复用现有 ID: {name}")
        if local_ref in refs:
            raise ValueError(f"世界实体临时 ref 重复: {local_ref}")
        function_key = _function_key(raw)
        if function_key in known_functions:
            raise ValueError(f"世界实体叙事功能重复，必须复用现有实体: {name}")
        entity_id = stable_entity_id(kind, position, name, source_event_id)
        refs[local_ref] = entity_id
        rows.append(
            {
                "id": entity_id,
                "kind": kind,
                "name": name,
                "aliases": aliases,
                "attributes": _mapping(raw.get("attributes"), f"{name}.attributes"),
                "source_event_id": source_event_id,
                "first_appearance_position": position,
                "persistence": "revision",
                "reason": reason,
                "initial_state": _mapping(
                    raw.get("initial_state"), f"{name}.initial_state"
                ),
            }
        )
        known_names.update({name, *aliases})
        known_functions.add(function_key)
    result["entity_introductions"] = _replace_refs(rows, refs)
    return _replace_refs(result, refs), _replace_refs(model_brief, refs)


def canon_with_plan_expansion(canon: dict, chapters=(), state: dict | None = None):
    """Return a validation/prompt view; the immutable Canon hash is unchanged."""
    validate_world_expansion_order(chapters)
    result = copy.deepcopy(canon)
    entities = {
        item["id"]: copy.deepcopy(item) for item in result.get("entities") or []
    }
    initial = copy.deepcopy(result.get("initial_state") or {})
    local = (state or {}).get("revision_local_entities") or {}
    for item in [*local.values(), *_plan_introductions(chapters)]:
        entity_id = item["id"]
        entity = _canon_entity(item)
        existing = entities.get(entity_id)
        if existing is not None and existing != entity:
            raise ValueError(f"修订版世界实体 ID 冲突: {entity_id}")
        entities[entity_id] = entity
        initial.setdefault(entity_id, copy.deepcopy(item.get("initial_state") or {}))
    result["entities"] = list(entities.values())
    result["initial_state"] = initial
    return result


def state_with_pending_expansion(state_before: dict, introductions=()) -> dict:
    state = copy.deepcopy(state_before)
    for item in introductions or []:
        _apply_introduction(state, item)
    return state


def apply_entity_introductions(state: dict, introductions=()) -> None:
    for item in introductions or []:
        _apply_introduction(state, item)


def validate_entity_introductions(
    canon: dict, chapter_plan: dict, state_before: dict, delta: dict
) -> list[str]:
    planned = list(chapter_plan.get("entity_introductions") or [])
    actual = list(delta.get("entity_introductions") or [])
    if actual != planned:
        return ["正文状态增量的世界实体引入与章节合同不一致"]
    known = world_entities(canon, state_before)
    known_names = _entity_names(known.values())
    scope_state = copy.deepcopy(state_before)
    errors = []
    for item in planned:
        entity_id = item.get("id")
        names = {item.get("name"), *(item.get("aliases") or [])} - {None, ""}
        if entity_id in known or names.intersection(known_names):
            errors.append(f"世界实体重复引入: {entity_id}")
        if item.get("source_event_id") not in set(
            chapter_plan.get("required_event_ids") or []
        ):
            errors.append(f"世界实体未绑定当前事件: {entity_id}")
        if int(item.get("first_appearance_position") or 0) != int(
            chapter_plan["position"]
        ):
            errors.append(f"世界实体首次出现章不匹配: {entity_id}")
        errors.extend(validate_scope_introduction(scope_state, item))
        known[entity_id] = item
        known_names.update(names)
        _apply_introduction(scope_state, item)
    return errors


def world_entities(canon: dict, state: dict | None = None) -> dict[str, dict]:
    result = {
        str(item["id"]): copy.deepcopy(item)
        for item in canon.get("entities") or []
        if item.get("id")
    }
    result.update(copy.deepcopy((state or {}).get("revision_local_entities") or {}))
    return result


def _apply_introduction(state: dict, item: dict) -> None:
    entity_id = item["id"]
    local = state.setdefault("revision_local_entities", {})
    local.setdefault(entity_id, copy.deepcopy(item))
    subjects = state.setdefault("subjects", {})
    if entity_id in subjects:
        return
    initial = copy.deepcopy(item.get("initial_state") or {})
    owner_id = initial.pop("owner_id", None)
    if item.get("kind") == "character":
        initial.setdefault("knowledge", [])
        initial.setdefault("possessions", [])
    subjects[entity_id] = initial
    if owner_id is not None:
        apply_subject_transition(subjects, entity_id, "owner_id", owner_id)
    apply_scope_introduction(state, item)


def _plan_introductions(chapters) -> list[dict]:
    result, seen_names = [], set()
    for chapter in sorted(chapters or [], key=lambda item: int(item["position"])):
        for item in chapter.get("entity_introductions") or []:
            names = {item.get("name"), *(item.get("aliases") or [])} - {None, ""}
            if names.intersection(seen_names):
                raise ValueError(f"世界实体名称重复引入: {sorted(names)}")
            seen_names.update(names)
            result.append(item)
    return result


def _canon_entity(item: dict) -> dict:
    return {
        key: copy.deepcopy(item.get(key))
        for key in ("id", "kind", "name", "aliases", "attributes")
    }


def _replace_refs(value, refs: dict[str, str]):
    if isinstance(value, str):
        return refs.get(value, value)
    if isinstance(value, list):
        return [_replace_refs(item, refs) for item in value]
    if isinstance(value, dict):
        return {
            refs.get(str(key), key): _replace_refs(item, refs)
            for key, item in value.items()
        }
    return value


def _mapping(value, label: str) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} 必须是对象")
    return copy.deepcopy(value)


def _strings(values, label: str) -> list[str]:
    result = [str(value).strip() for value in values]
    if any(not value for value in result) or len(result) != len(set(result)):
        raise ValueError(f"{label} 必须是非空且不重复的字符串数组")
    return result


def _entity_names(values) -> set[str]:
    return {
        str(name).strip()
        for item in values
        for name in [item.get("name"), *(item.get("aliases") or [])]
        if str(name or "").strip()
    }


def _function_key(item: dict):
    function = str((item.get("attributes") or {}).get("narrative_function") or "")
    return (item.get("kind"), function) if function else None
