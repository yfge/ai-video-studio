"""Ordering rules for revision-local world expansion."""

from __future__ import annotations

import json

from .story_novel_context_utils import value_hash

_PREFIXES = {
    "character": "char",
    "location": "loc",
    "object": "obj",
    "organization": "org",
    "concept": "concept",
}
_TEXT_FIELDS = (
    "title",
    "goal",
    "key_events",
    "character_focus",
    "open_threads",
    "end_state",
)


def stable_entity_id(kind: str, position: int, name: str, source_event_id: str) -> str:
    fingerprint = value_hash(
        {"kind": kind, "position": position, "name": name, "event": source_event_id}
    )[:12]
    return f"{_PREFIXES[kind]}-local-{position}-{fingerprint}"


def validate_world_expansion_order(chapters) -> None:
    """Reject references or prose-authoritative names before first appearance."""
    rows = sorted(chapters or [], key=lambda item: int(item["position"]))
    introductions = _introductions(rows)
    for chapter in rows:
        position = int(chapter["position"])
        future_ids = {
            entity_id
            for entity_id, item in introductions.items()
            if int(item["first_appearance_position"]) > position
        }
        leaked_ids = _chapter_refs(chapter).intersection(future_ids)
        if leaked_ids:
            raise ValueError(
                f"第 {position} 章提前引用尚未登场的修订版实体: "
                f"{sorted(leaked_ids)}"
            )
        surface = json.dumps(
            {key: chapter.get(key) for key in _TEXT_FIELDS},
            ensure_ascii=False,
            default=str,
        )
        leaked_names = sorted(
            name
            for entity_id in future_ids
            for name in _names(introductions[entity_id])
            if name in surface
        )
        if leaked_names:
            raise ValueError(
                f"第 {position} 章提前写出尚未登场的修订版实体名称: " f"{leaked_names}"
            )


def _introductions(chapters) -> dict[str, dict]:
    result: dict[str, dict] = {}
    names: set[str] = set()
    for chapter in chapters:
        position = int(chapter["position"])
        required = set(chapter.get("required_event_ids") or [])
        for item in chapter.get("entity_introductions") or []:
            entity_id = str(item.get("id") or "")
            source_event_id = str(item.get("source_event_id") or "")
            kind = str(item.get("kind") or "")
            name = str(item.get("name") or "").strip()
            if (
                not entity_id
                or kind not in _PREFIXES
                or not name
                or source_event_id not in required
                or int(item.get("first_appearance_position") or 0) != position
                or item.get("persistence") != "revision"
            ):
                raise ValueError(f"第 {position} 章修订版实体引入合同无效")
            expected = stable_entity_id(kind, position, name, source_event_id)
            if entity_id != expected:
                raise ValueError(
                    f"第 {position} 章修订版实体稳定 ID 不匹配: {entity_id}"
                )
            aliases = _names(item)
            if entity_id in result or names.intersection(aliases):
                raise ValueError(f"第 {position} 章修订版实体重复引入: {entity_id}")
            result[entity_id] = item
            names.update(aliases)
    return result


def _chapter_refs(chapter: dict) -> set[str]:
    refs = set(chapter.get("canon_refs") or [])
    for key in ("preconditions", "state_transitions", "location_transitions"):
        for item in chapter.get(key) or []:
            refs.add(item.get("subject_id"))
            refs.add(item.get("from_location_id"))
            refs.add(item.get("to_location_id"))
    refs.update(
        item.get("character_id") for item in chapter.get("knowledge_grants") or []
    )
    refs.update(
        actor_id
        for item in chapter.get("execution_contracts") or []
        for actor_id in item.get("actor_ids") or []
    )
    return {str(value) for value in refs if value}


def _names(item: dict) -> set[str]:
    return {
        str(value).strip()
        for value in [item.get("name"), *(item.get("aliases") or [])]
        if str(value or "").strip()
    }
