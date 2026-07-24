"""Build the single chapter-zero state view from Canon."""

from __future__ import annotations

import copy


def canonical_initial_subjects(canon: dict) -> dict:
    """Overlay explicit initial state on static entity attributes."""
    explicit = canon.get("initial_state") or {}
    subjects: dict = {}
    character_ids: list[str] = []
    for entity in canon.get("entities") or []:
        subject_id = entity["id"]
        if entity.get("kind") == "character":
            character_ids.append(subject_id)
        attributes = copy.deepcopy(entity.get("attributes") or {})
        if attributes or subject_id in explicit:
            subjects[subject_id] = _overlay(
                attributes,
                copy.deepcopy(explicit.get(subject_id) or {}),
            )
    for subject_id, value in explicit.items():
        subjects.setdefault(subject_id, copy.deepcopy(value))
    for character_id in character_ids:
        subject = subjects.setdefault(character_id, {})
        if not isinstance(subject.get("possessions"), list):
            subject["possessions"] = []
    _normalize_possessions(subjects)
    return subjects


def _overlay(base: dict, explicit: dict) -> dict:
    for key, value in explicit.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _overlay(base[key], value)
        else:
            base[key] = value
    return base


def apply_subject_transition(
    subjects: dict, subject_id: str, field: str, new_value
) -> None:
    subject = subjects.setdefault(subject_id, {})
    old_value = _get(subject, field)
    if old_value == new_value:
        return
    _set(subject, field, new_value)
    if field != "owner_id":
        return
    _remove_possession(subjects.get(old_value), subject_id)
    owner = subjects.get(new_value)
    if isinstance(owner, dict):
        possessions = owner.get("possessions")
        if not isinstance(possessions, list):
            possessions = owner["possessions"] = []
        if subject_id not in possessions:
            possessions.append(subject_id)
        if owner.get("location"):
            subject["location"] = owner["location"]


def apply_subject_movement(subjects: dict, subject_id: str, location_id: str) -> None:
    subject = subjects.setdefault(subject_id, {})
    subject["location"] = location_id
    possessions = set(subject.get("possessions") or [])
    for object_id, value in subjects.items():
        if object_id in possessions and value.get("owner_id") == subject_id:
            value["location"] = location_id


def _normalize_possessions(subjects: dict) -> None:
    for subject_id, subject in list(subjects.items()):
        owner_id = subject.get("owner_id")
        owner = subjects.get(owner_id)
        if isinstance(owner, dict):
            possessions = owner.get("possessions")
            if not isinstance(possessions, list):
                possessions = owner["possessions"] = []
            if subject_id not in possessions:
                possessions.append(subject_id)


def _remove_possession(owner, subject_id: str) -> None:
    if isinstance(owner, dict) and isinstance(owner.get("possessions"), list):
        owner["possessions"] = [
            item for item in owner["possessions"] if item != subject_id
        ]


def _get(value: dict, path: str):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _set(value: dict, path: str, new_value) -> None:
    parts = path.split(".")
    current = value
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = new_value
