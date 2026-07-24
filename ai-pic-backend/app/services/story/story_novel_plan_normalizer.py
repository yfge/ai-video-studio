"""Compile deterministic Canon effects before strict plan validation."""

from __future__ import annotations

from .story_novel_initial_state import (
    apply_subject_movement,
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_location_rules import entity_kinds


def normalize_redundant_location_state(canon: dict, chapters: list[dict]) -> list[dict]:
    """Drop location state entries that cannot represent a real move."""
    subjects = canonical_initial_subjects(canon)
    kinds = entity_kinds(canon)
    normalized = []
    for chapter in chapters:
        row = dict(chapter)
        transitions = [dict(item) for item in row.get("state_transitions") or []]
        movements = [dict(item) for item in row.get("location_transitions") or []]
        movement_targets = {
            (item["subject_id"], item["to_location_id"]) for item in movements
        }
        row["state_transitions"] = [
            item
            for item in transitions
            if not (
                item.get("field") == "location"
                and (
                    item.get("to_value")
                    == (subjects.get(item.get("subject_id")) or {}).get("location")
                    or (item.get("subject_id"), item.get("to_value"))
                    in movement_targets
                )
            )
        ]
        row["location_transitions"] = _drop_owner_placement_movements(
            movements, row["state_transitions"], subjects, kinds
        )
        _replay_row(row, subjects)
        normalized.append(row)
    return normalized


def _drop_owner_placement_movements(movements, transitions, subjects, kinds):
    owners = {
        item["subject_id"]: item.get("to_value")
        for item in transitions
        if item.get("field") == "owner_id"
        and item.get("to_value")
        and item.get("from_value") != item.get("to_value")
    }
    owner_targets = {
        item["subject_id"]: item.get("to_location_id") for item in movements
    }
    kept = []
    for movement in movements:
        subject_id = movement["subject_id"]
        if movement.get("from_location_id") is not None:
            kept.append(movement)
            continue
        current = subjects.get(subject_id) or {}
        target = movement.get("to_location_id")
        if current.get("location") == target:
            continue
        owner_id = owners.get(subject_id)
        owner = subjects.get(owner_id) if owner_id else None
        owner_places_object = (
            kinds.get(subject_id) == "object"
            and isinstance(owner, dict)
            and isinstance(owner.get("possessions"), list)
            and target in {owner.get("location"), owner_targets.get(owner_id)}
        )
        if not owner_places_object:
            kept.append(movement)
    return kept


def _replay_row(row: dict, subjects: dict) -> None:
    for transition in row.get("state_transitions") or []:
        subject = subjects.setdefault(transition["subject_id"], {})
        if transition.get("from_value") != transition.get("to_value") and _get(
            subject, transition["field"]
        ) == transition.get("from_value"):
            apply_subject_transition(
                subjects,
                transition["subject_id"],
                transition["field"],
                transition.get("to_value"),
            )
    for movement in row.get("location_transitions") or []:
        apply_subject_movement(
            subjects, movement["subject_id"], movement["to_location_id"]
        )


def _get(value: dict, path: str):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
