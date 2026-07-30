"""Compile executable state edges from model-authored narrative effects."""

from __future__ import annotations

import hashlib
import json

from .story_novel_initial_state import (
    apply_subject_movement,
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_location_hierarchy import persistent_location_id
from .story_novel_location_rules import entity_kinds
from .story_novel_milestone_effect_compiler import compile_milestone_effects
from .story_novel_plan_normalizer import normalize_redundant_location_state

STATE_COMPILER_VERSION = 1
_RESERVED_STATE_FIELDS = {"knowledge", "location", "possessions"}


def compile_plan_state(canon: dict, chapters: list[dict]) -> list[dict]:
    """Treat provider arrays as effects while the service owns state origins."""
    rows = normalize_redundant_location_state(canon, chapters)
    subjects = canonical_initial_subjects(canon)
    for subject in subjects.values():
        if isinstance(subject, dict) and "location" in subject:
            subject["location"] = persistent_location_id(canon, subject.get("location"))
    kinds = entity_kinds(canon)
    compiled = []
    for source in rows:
        row = dict(source)
        source_hash = _effect_hash(row)
        row = compile_milestone_effects(canon, row, subjects)
        row = _drop_redundant_knowledge_state(row, subjects, kinds)
        row = _drop_mirrored_possession_state(row, subjects, kinds)
        transitions, predicates = _compile_transitions(row, subjects, kinds)
        row["state_transitions"] = transitions
        row["location_transitions"] = _compile_movements(canon, row, subjects, kinds)
        _compile_knowledge(row, subjects, predicates, kinds)
        row["preconditions"] = _unique_predicates(predicates)
        row["state_compiler"] = {
            "version": STATE_COMPILER_VERSION,
            "source_effect_hash": source_hash,
        }
        compiled.append(row)
    return compiled


def _drop_redundant_knowledge_state(row, subjects, kinds):
    """Drop only knowledge arrays already expressed by exact typed grants."""
    grants: dict[str, set[str]] = {}
    for item in row.get("knowledge_grants") or []:
        grants.setdefault(item.get("character_id"), set()).add(item.get("fact_id"))
    kept = []
    for raw in row.get("state_transitions") or []:
        item = dict(raw)
        character_id = item.get("subject_id")
        current = (subjects.get(character_id) or {}).get("knowledge") or []
        target = item.get("to_value")
        if (
            item.get("field") == "knowledge"
            and kinds.get(character_id) == "character"
            and isinstance(current, list)
            and isinstance(target, list)
            and set(current).issubset(target)
            and (set(target) - set(current)).issubset(grants.get(character_id, set()))
        ):
            continue
        kept.append(item)
    return {**row, "state_transitions": kept}


def _drop_mirrored_possession_state(row, subjects, kinds):
    """Let object owner_id edges own their derived character possessions."""
    transfers = {}
    for raw in row.get("state_transitions") or []:
        item = dict(raw)
        subject_id = item.get("subject_id")
        if item.get("field") == "owner_id" and kinds.get(subject_id) == "object":
            transfers[subject_id] = (
                (subjects.get(subject_id) or {}).get("owner_id"),
                item.get("to_value"),
            )
    kept = []
    for raw in row.get("state_transitions") or []:
        item = dict(raw)
        if item.get("field") != "possessions":
            kept.append(item)
            continue
        if not _mirrors_owner_transfer(item, transfers):
            kept.append(item)
    return {**row, "state_transitions": kept}


def _mirrors_owner_transfer(item: dict, transfers: dict) -> bool:
    subject_id = item.get("subject_id")
    object_id = item.get("to_value")
    if isinstance(object_id, str):
        old_owner, new_owner = transfers.get(object_id, (None, None))
        return (subject_id, item.get("operation")) in {
            (old_owner, "remove"),
            (new_owner, "add"),
        }
    before, after = item.get("from_value"), item.get("to_value")
    if not (
        isinstance(before, list)
        and isinstance(after, list)
        and all(isinstance(value, str) for value in [*before, *after])
    ):
        return False
    changes = [
        *((value, "remove") for value in set(before) - set(after)),
        *((value, "add") for value in set(after) - set(before)),
    ]
    return bool(changes) and all(
        (subject_id, operation)
        in {
            (transfers.get(value) or (None, None))[0:1] + ("remove",),
            (transfers.get(value) or (None, None))[1:2] + ("add",),
        }
        for value, operation in changes
    )


def _compile_transitions(row, subjects, kinds):
    transitions, predicates = [], []
    for raw in row.get("state_transitions") or []:
        item = dict(raw)
        subject_id, field = item.get("subject_id"), item.get("field")
        if subject_id not in kinds or field in _RESERVED_STATE_FIELDS:
            transitions.append(item)
            continue
        actual = _get(subjects.get(subject_id) or {}, field)
        item["from_value"] = actual
        if actual == item.get("to_value"):
            continue
        transitions.append(item)
        predicates.append(_predicate(subject_id, field, "eq", actual))
        apply_subject_transition(subjects, subject_id, field, item.get("to_value"))
    return transitions, predicates


def _compile_movements(canon, row, subjects, kinds):
    movements = []
    for raw in row.get("location_transitions") or []:
        item = dict(raw)
        subject_id = item.get("subject_id")
        if subject_id not in kinds:
            movements.append(item)
            continue
        current = (subjects.get(subject_id) or {}).get("location")
        target = persistent_location_id(canon, item.get("to_location_id"))
        item["to_location_id"] = target
        if current == target:
            continue
        item["from_location_id"] = current
        movements.append(item)
        if isinstance(target, str) and target:
            apply_subject_movement(subjects, subject_id, target)
    return movements


def _compile_knowledge(row, subjects, predicates, kinds):
    for grant in row.get("knowledge_grants") or []:
        character_id, fact_id = grant.get("character_id"), grant.get("fact_id")
        if kinds.get(character_id) != "character" or not fact_id:
            continue
        knowledge = subjects.setdefault(character_id, {}).setdefault("knowledge", [])
        predicates.append(
            _predicate(character_id, "knowledge", "not_contains", fact_id)
        )
        if fact_id not in knowledge:
            knowledge.append(fact_id)


def _predicate(subject_id, field, operator, value):
    return {
        "subject_id": subject_id,
        "field": field,
        "operator": operator,
        "value": value,
    }


def _unique_predicates(values):
    seen, result = set(), []
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _effect_hash(row):
    value = {
        key: row.get(key) or []
        for key in (
            "preconditions",
            "state_transitions",
            "knowledge_grants",
            "location_transitions",
            "milestones_consumed",
        )
    }
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def _get(value: dict, path: str):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
