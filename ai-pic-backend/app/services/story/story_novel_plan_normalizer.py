"""Compile deterministic Canon effects before strict plan validation."""

from __future__ import annotations

from .story_novel_initial_state import (
    apply_subject_movement,
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_location_rules import entity_kinds


def normalize_plan_payload(payload):
    """Normalize provider field aliases before Pydantic validation."""
    if not isinstance(payload, dict) or not isinstance(payload.get("chapters"), list):
        return payload
    normalized = dict(payload)
    normalized["chapters"] = [
        _normalize_chapter_aliases(chapter) for chapter in payload["chapters"]
    ]
    return normalized


def _normalize_chapter_aliases(chapter):
    if not isinstance(chapter, dict):
        return chapter
    row = dict(chapter)
    movements = []
    for raw in row.get("location_transitions") or []:
        if not isinstance(raw, dict):
            movements.append(raw)
            continue
        movement = dict(raw)
        means = movement.get("means")
        reason = movement.get("reason")
        if (not isinstance(means, str) or not means.strip()) and isinstance(
            reason, str
        ):
            if reason.strip():
                movement["means"] = reason
        movements.append(movement)
    row["location_transitions"] = movements
    return row


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
        current = subjects.get(subject_id) or {}
        target = movement.get("to_location_id")
        if current.get("location") == target:
            continue
        new_owner_id = owners.get(subject_id)
        new_owner_move = next(
            (
                item
                for item in movements
                if item.get("subject_id") == new_owner_id
                and item.get("to_location_id") == target
            ),
            None,
        )
        if kinds.get(subject_id) == "object" and new_owner_move:
            continue
        if movement.get("from_location_id") is not None:
            if _carried_by_owner_movement(
                movement, movements, transitions, subjects, kinds
            ):
                continue
            kept.append(movement)
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


def _carried_by_owner_movement(movement, movements, transitions, subjects, kinds):
    subject_id = movement["subject_id"]
    current = subjects.get(subject_id) or {}
    owner_id = current.get("owner_id")
    owner = subjects.get(owner_id) or {}
    if (
        kinds.get(subject_id) != "object"
        or kinds.get(owner_id) != "character"
        or subject_id not in (owner.get("possessions") or [])
        or any(
            item.get("subject_id") == subject_id and item.get("field") == "owner_id"
            for item in transitions
        )
    ):
        return False
    start = movement.get("from_location_id")
    owner_movements = [item for item in movements if item.get("subject_id") == owner_id]
    if len(owner_movements) != 1:
        return False
    owner_movement = owner_movements[0]
    return (
        current.get("location") == start
        and owner.get("location") == start
        and owner_movement.get("from_location_id") == start
        and owner_movement.get("to_location_id") == movement.get("to_location_id")
    )


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
