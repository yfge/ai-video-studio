"""Human-readable effect meanings for prose and proof audit prompts."""

from __future__ import annotations


def intent_effect_meaning(effect: dict, model_input: dict) -> str:
    names = {
        item["entity_handle"]: item.get("name") or item["entity_handle"]
        for item in model_input.get("visible_characters_and_world") or []
    }
    subject = names.get(effect["subject_handle"], effect["subject_handle"])
    target = names.get(effect.get("target_handle"), effect.get("target_handle"))
    kind = effect["kind"]
    value = effect.get("value")
    if kind == "knowledge_gain":
        return f"{subject}在当前事件中获知：{value}"
    if kind == "relationship_change":
        return f"{subject}与{target}的关系变为：{value}"
    if kind == "location_change":
        return f"{subject}通过{effect.get('means')}到达{target}"
    if kind == "ownership_change":
        return f"{subject}的所有权转移给{target}"
    if kind == "status_change":
        return f"{subject}的状态变为：{value}"
    if kind == "state_change":
        return f"{subject}的{effect.get('field')}变为：{value}"
    action = "获得" if kind.endswith("_add") else "失去"
    label = {
        "capability": "能力",
        "resource": "资源",
        "permission": "权限",
    }[kind.rsplit("_", 1)[0]]
    return f"{subject}{action}{label}：{value}"


def default_effect_meanings(row: dict, snapshot: dict) -> dict[str, str]:
    names = _persistent_names(snapshot)
    result = {}
    for index, item in enumerate(row.get("state_transitions") or [], 1):
        name = names.get(item.get("subject_id"), item.get("subject_id"))
        result[f"state:{index}"] = (
            f"{name}的{item.get('field')}变为：{item.get('to_value')}"
        )
    for index, item in enumerate(row.get("location_transitions") or [], 1):
        subject = names.get(item.get("subject_id"), item.get("subject_id"))
        target = names.get(item.get("to_location_id"), item.get("to_location_id"))
        result[f"location:{index}"] = f"{subject}到达{target}"
    for index, item in enumerate(row.get("knowledge_grants") or [], 1):
        name = names.get(item.get("character_id"), item.get("character_id"))
        result[f"knowledge:{index}"] = f"{name}获知事实：{item.get('fact_id')}"
    return result


def _persistent_names(snapshot: dict) -> dict[str, str]:
    bindings = snapshot["handle_bindings"]["entities"]
    local_names = {
        item["entity_handle"]: item.get("name") or item["entity_handle"]
        for item in snapshot["model_input"].get("visible_characters_and_world") or []
    }
    return {
        persistent_id: local_names.get(handle, handle)
        for handle, persistent_id in bindings.items()
    }
