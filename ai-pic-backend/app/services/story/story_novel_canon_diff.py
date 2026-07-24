"""Canon diff helpers used by human repair invalidation."""

from __future__ import annotations

from .story_novel_canon_service import CANON_SECTIONS


def changed_canon_refs(before: dict, after: dict) -> set[str]:
    changed: set[str] = set()
    for section in CANON_SECTIONS:
        key = "character_id" if section == "character_arcs" else "id"
        old = {item[key]: item for item in before.get(section) or []}
        new = {item[key]: item for item in after.get(section) or []}
        changed.update(
            item_id
            for item_id in old.keys() | new.keys()
            if old.get(item_id) != new.get(item_id)
        )
    states = set((before.get("initial_state") or {})) | set(
        after.get("initial_state") or {}
    )
    changed.update(
        item_id
        for item_id in states
        if (before.get("initial_state") or {}).get(item_id)
        != (after.get("initial_state") or {}).get(item_id)
    )
    return changed


def earliest_affected_position(chapters: list[dict], changed: set[str]) -> int:
    for chapter in chapters:
        refs = set(chapter.get("canon_refs") or [])
        refs.update(
            item.get("subject_id") for item in chapter.get("preconditions") or []
        )
        refs.update(
            item.get("subject_id") for item in chapter.get("state_transitions") or []
        )
        refs.update(
            item.get("subject_id") for item in chapter.get("location_transitions") or []
        )
        refs.update(
            item.get("character_id") for item in chapter.get("knowledge_grants") or []
        )
        refs.update(chapter.get("milestones_consumed") or [])
        if changed.intersection(refs):
            return int(chapter["position"])
    return 1
