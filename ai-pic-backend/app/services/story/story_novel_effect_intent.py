"""Validate topic-neutral chapter effects expressed with snapshot-local handles."""

from __future__ import annotations

import re

KINDS = {
    "knowledge_gain",
    "relationship_change",
    "capability_add",
    "capability_remove",
    "resource_add",
    "resource_remove",
    "permission_add",
    "permission_remove",
    "status_change",
    "state_change",
    "location_change",
    "ownership_change",
}
_LIST_KINDS = {
    "capability_add",
    "capability_remove",
    "resource_add",
    "resource_remove",
    "permission_add",
    "permission_remove",
}
_TARGET_KINDS = {"relationship_change", "location_change", "ownership_change"}
_ALLOWED_KEYS = {
    "effect_handle",
    "kind",
    "subject_handle",
    "source_event_handle",
    "target_handle",
    "field",
    "value",
    "means",
}
_FIELD = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_RESERVED_FIELDS = {"knowledge", "location", "possessions", "owner_id", "relationships"}


def parse_effect_intents(value, model_input: dict, proposals=()) -> list[dict]:
    rows = list(value or [])
    if any(not isinstance(item, dict) for item in rows):
        raise ValueError("effect_intents 必须是对象数组")
    entities = {
        item["entity_handle"]: item
        for item in model_input.get("visible_characters_and_world") or []
    }
    entities.update(
        {
            item["proposal_handle"]: _proposal_entity(item)
            for item in proposals or []
            if not item.get("transient")
        }
    )
    events = {item["event_handle"] for item in model_input["current_chapter"]["events"]}
    result = [
        _effect(item, index, entities, events) for index, item in enumerate(rows, 1)
    ]
    keys = [
        (
            item["subject_handle"],
            item["kind"],
            item.get("field"),
            item.get("target_handle"),
            repr(item.get("value")),
        )
        for item in result
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("effect_intents 不得重复")
    targets = [key for item in result if (key := _persistent_target(item))]
    if len(targets) != len(set(targets)):
        raise ValueError("effect_intents 同一持久状态字段只能声明一次最终效果")
    return result


def _persistent_target(item: dict) -> tuple[str, str] | None:
    kind = item["kind"]
    if kind == "knowledge_gain":
        return None
    if kind == "relationship_change":
        field = f"relationships.{item['target_handle']}"
    elif kind in {"capability_add", "capability_remove"}:
        field = "capabilities"
    elif kind in {"resource_add", "resource_remove"}:
        field = "resources"
    elif kind in {"permission_add", "permission_remove"}:
        field = "permissions"
    elif kind == "status_change":
        field = "status"
    elif kind == "state_change":
        field = item["field"]
    elif kind == "location_change":
        field = "location"
    else:
        field = "owner_id"
    return item["subject_handle"], field


def _proposal_entity(item: dict) -> dict:
    state = {}
    if item.get("kind") == "character":
        state = {
            "knowledge": [],
            "possessions": list(item.get("resources") or []),
            "capabilities": list(item.get("capabilities") or []),
            "relationships": {
                row["target_handle"]: row["relationship"]
                for row in item.get("relationship_intents") or []
            },
        }
    return {
        "entity_handle": item["proposal_handle"],
        "kind": item["kind"],
        "name": item["name"],
        "current_state": state,
    }


def _effect(item, index, entities, events) -> dict:
    if set(item).difference(_ALLOWED_KEYS):
        raise ValueError("effect_intent 包含越界字段")
    expected = f"FX{index:02d}"
    if item.get("effect_handle") != expected:
        raise ValueError("effect_handle 必须从 FX01 连续编号")
    kind = _text(item, "kind")
    subject = _text(item, "subject_handle")
    event = _text(item, "source_event_handle")
    if kind not in KINDS or subject not in entities or event not in events:
        raise ValueError("effect_intent kind/subject/source event 无效")
    target = str(item.get("target_handle") or "").strip() or None
    field = str(item.get("field") or "").strip() or None
    means = str(item.get("means") or "").strip() or None
    raw_value = item.get("value")
    if kind in _TARGET_KINDS:
        if target not in entities:
            raise ValueError("effect_intent target_handle 必须来自当前快照")
    elif target is not None:
        raise ValueError("当前 effect kind 不接受 target_handle")
    if kind == "state_change":
        if not field or not _FIELD.fullmatch(field) or field in _RESERVED_FIELDS:
            raise ValueError("state_change field 无效或属于保留字段")
        if field not in (entities[subject].get("current_state") or {}):
            raise ValueError("state_change 只能修改当前快照已有状态字段")
    elif field is not None:
        raise ValueError("只有 state_change 可以提供 field")
    if kind == "location_change":
        if entities[target].get("kind") != "location" or not means:
            raise ValueError("location_change 必须提供地点 target 与 means")
    elif means is not None:
        raise ValueError("只有 location_change 可以提供 means")
    _validate_kinds(
        kind, entities[subject].get("kind"), entities.get(target, {}).get("kind")
    )
    if kind in _LIST_KINDS | {"knowledge_gain", "relationship_change", "status_change"}:
        raw_value = str(raw_value or "").strip()
        if not raw_value:
            raise ValueError(f"{kind} 必须提供非空 value")
    elif kind in {"location_change", "ownership_change"}:
        if raw_value not in (None, ""):
            raise ValueError(f"{kind} 不接受 value")
        raw_value = None
    elif raw_value is None:
        raise ValueError("state_change value 不能为空")
    return {
        "effect_handle": expected,
        "kind": kind,
        "subject_handle": subject,
        "source_event_handle": event,
        "target_handle": target,
        "field": field,
        "value": raw_value,
        "means": means,
    }


def _validate_kinds(kind: str, subject_kind: str, target_kind: str | None) -> None:
    if (
        kind in {"knowledge_gain", "relationship_change"}
        and subject_kind != "character"
    ):
        raise ValueError(f"{kind} 的 subject 必须是人物")
    if kind == "relationship_change" and target_kind != "character":
        raise ValueError("relationship_change 的 target 必须是人物")
    if kind == "ownership_change" and (
        subject_kind != "object" or target_kind not in {"character", "organization"}
    ):
        raise ValueError("ownership_change 必须把物件交给人物或组织")


def _text(value: dict, key: str) -> str:
    result = str(value.get(key) or "").strip()
    if not result:
        raise ValueError(f"{key} 不能为空")
    return result
