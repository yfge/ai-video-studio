from __future__ import annotations

from .story_novel_initial_state import (
    apply_subject_movement,
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_location_hierarchy import (
    normalize_persistent_locations,
    persistent_location_id,
)
from .story_novel_location_rules import entity_kinds
from .story_novel_milestone_knowledge_normalizer import normalize_milestone_knowledge
from .story_novel_plan_effect_refs import bind_missing_knowledge_sources
from .story_novel_plan_value_rules import normalize_predicate_operators


def normalize_plan_payload(
    payload, canon: dict | None = None, thread_payoffs: list[dict] | None = None
):
    """Normalize provider field aliases before Pydantic validation."""
    if not isinstance(payload, dict) or not isinstance(payload.get("chapters"), list):
        return payload
    normalized = dict(payload)
    normalized["chapters"] = [
        _normalize_chapter_aliases(chapter, canon, thread_payoffs)
        for chapter in payload["chapters"]
    ]
    return normalized


def _normalize_chapter_aliases(chapter, canon, thread_payoffs):
    if not isinstance(chapter, dict):
        return chapter
    row = normalize_predicate_operators(chapter)
    movements = []
    transitions = []
    for raw in row.get("state_transitions") or []:
        movement = _typed_location_movement(raw, canon)
        if movement is None:
            transitions.append(raw)
        elif movement:
            movements.append(movement)
    row["state_transitions"] = transitions
    for raw in row.get("location_transitions") or []:
        if not isinstance(raw, dict):
            movements.append(raw)
            continue
        movement = dict(raw)
        if (
            "to_location_id" in movement
            and not str(movement.get("to_location_id") or "").strip()
        ):
            continue
        means = movement.get("means")
        reason = movement.get("reason")
        if (not isinstance(means, str) or not means.strip()) and isinstance(
            reason, str
        ):
            if reason.strip():
                movement["means"] = reason
        movements.append(movement)
    row["location_transitions"] = movements
    row["knowledge_grants"] = _character_memory_grants(
        canon,
        bind_missing_knowledge_sources(
            row, normalize_milestone_knowledge(row, canon, thread_payoffs)
        ),
    )
    return row


def _typed_location_movement(raw, canon):
    if not isinstance(raw, dict) or raw.get("field") != "location":
        return None
    kinds = entity_kinds(canon or {})
    subject_id = raw.get("subject_id")
    start, target = raw.get("from_value"), raw.get("to_value")
    reason = raw.get("reason")
    if start is None and kinds.get(subject_id) == "character":
        return {} if kinds.get(target) == "location" else None
    if (
        subject_id not in kinds
        or kinds.get(target) != "location"
        or (start is not None and kinds.get(start) != "location")
        or not isinstance(reason, str)
        or not reason.strip()
    ):
        return None
    return {
        "subject_id": subject_id,
        "from_location_id": start,
        "to_location_id": target,
        "means": reason.strip(),
    }


def _character_memory_grants(canon, grants):
    """Drop known non-character memory subjects; unknown IDs stay fail-closed."""
    kinds = entity_kinds(canon or {})
    return [
        item
        for item in grants
        if not (
            isinstance(item, dict)
            and kinds.get(item.get("character_id")) not in {None, "character"}
        )
    ]


def normalize_redundant_location_state(canon: dict, chapters: list[dict]) -> list[dict]:
    subjects = canonical_initial_subjects(canon)
    for subject in subjects.values():
        if isinstance(subject, dict) and "location" in subject:
            subject["location"] = persistent_location_id(canon, subject.get("location"))
    kinds = entity_kinds(canon)
    normalized = []
    for chapter in chapters:
        row = normalize_persistent_locations(canon, chapter)
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
    current_locations = {key: value.get("location") for key, value in subjects.items()}
    kept = []
    for movement in movements:
        subject_id = movement["subject_id"]
        current = subjects.get(subject_id) or {}
        target = movement.get("to_location_id")
        if current_locations.get(subject_id) == target:
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
                current_locations[subject_id] = target
                continue
            kept.append(movement)
            current_locations[subject_id] = target
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
        current_locations[subject_id] = target
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
        current = current.get(part) if isinstance(current, dict) else None
    return current
