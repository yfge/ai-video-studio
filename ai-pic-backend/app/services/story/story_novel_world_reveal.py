"""Deterministic first-appearance index for preplanned world entities."""

from __future__ import annotations

from .story_novel_context_utils import value_hash

SCHEMA = "story_novel_world_reveal_index.v1"


def compile_world_reveal_index(canon: dict, chapters: list[dict]) -> dict:
    positions = {}
    local_entities = {}
    for chapter in sorted(chapters, key=lambda item: int(item["position"])):
        position = int(chapter["position"])
        for entity_id in chapter.get("future_guard_entity_ids") or []:
            positions.setdefault(str(entity_id), position)
        for item in chapter.get("entity_introductions") or []:
            entity_id = str(item["id"])
            positions[entity_id] = position
            local_entities[entity_id] = item
    entities = [
        *list(canon.get("entities") or []),
        *list(local_entities.values()),
    ]
    entries = [
        {
            "entity_id": str(item["id"]),
            "kind": item.get("kind"),
            "first_appearance_position": positions.get(str(item["id"])),
        }
        for item in entities
        if item.get("id")
    ]
    result = {"schema": SCHEMA, "entities": entries}
    result["index_hash"] = value_hash(result)
    return result


def world_reveal_index_matches(stored: dict, expected: dict) -> bool:
    return stored == expected and stored.get("index_hash") == value_hash(
        {key: value for key, value in stored.items() if key != "index_hash"}
    )
