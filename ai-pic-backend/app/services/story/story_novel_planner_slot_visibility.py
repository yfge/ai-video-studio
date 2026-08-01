"""Expose only current-position arc commitments and instantiated slots."""

from __future__ import annotations

import copy

from .story_novel_v4_plan import arc_for_position


def visible_arc_context(plan: dict, position: int, reverse_entities: dict) -> dict:
    arc = arc_for_position(plan, position)
    return {
        key: copy.deepcopy(arc.get(key))
        for key in (
            "arc_id",
            "title",
            "start_position",
            "end_position",
            "narrative_goal",
            "growth",
        )
    }


def authorized_entity_slots(
    plan: dict, position: int, reverse_entities: dict, entity_rows=()
) -> list[dict]:
    arc = arc_for_position(plan, position)
    rows = [
        *list(arc.get("instantiated_character_slots") or []),
        *list(arc.get("instantiated_scope_slots") or []),
    ]
    character_handles = sorted(
        reverse_entities[item.get("id")]
        for item in entity_rows
        if item.get("kind") == "character" and item.get("id") in reverse_entities
    )
    result = []
    for item in rows:
        if int(item.get("first_appearance_position") or 0) != position:
            continue
        row = copy.deepcopy(item)
        target = row.pop("relationship_target", None)
        row["relationship_target_handle"] = _target_handle(
            target, reverse_entities, entity_rows
        )
        if row.get("kind") == "character":
            row["allowed_relationship_target_handles"] = character_handles
        if row.get("kind") == "location":
            parent_id = row.pop("parent_scope_id", None)
            row["parent_scope_handle"] = _target_handle(
                parent_id, reverse_entities, entity_rows
            )
        result.append(row)
    return result


def _target_handle(target, reverse_entities, entity_rows):
    if not target:
        return None
    if target in reverse_entities:
        return reverse_entities[target]
    entity_id = next(
        (
            item.get("id")
            for item in entity_rows
            if (item.get("attributes") or {}).get("slot_id") == target
        ),
        None,
    )
    return reverse_entities.get(entity_id)
