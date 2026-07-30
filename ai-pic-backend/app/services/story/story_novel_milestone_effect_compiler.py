"""Compile consumed Canon milestone outcomes into executable chapter effects."""

from __future__ import annotations

from .story_novel_location_hierarchy import persistent_location_id
from .story_novel_owner_contract import owner_outcome_target_valid


def compile_milestone_effects(canon: dict, chapter: dict, subjects: dict) -> dict:
    """Make typed Canon outcomes authoritative instead of trusting provider arrays."""
    row = {
        **chapter,
        "state_transitions": [
            dict(item) for item in chapter.get("state_transitions") or []
        ],
        "knowledge_grants": [
            dict(item) for item in chapter.get("knowledge_grants") or []
        ],
        "location_transitions": [
            dict(item) for item in chapter.get("location_transitions") or []
        ],
    }
    milestones = {item["id"]: item for item in canon.get("milestones") or []}
    for milestone_id in row.get("milestones_consumed") or []:
        milestone = milestones.get(milestone_id)
        if not milestone:
            continue
        for outcome in milestone.get("outcomes") or []:
            _compile_outcome(canon, row, subjects, milestone_id, outcome)
    return row


def _compile_outcome(canon, row, subjects, milestone_id, outcome):
    field, operator = outcome.get("field"), outcome.get("operator")
    entities = {item["id"]: item for item in canon.get("entities") or []}
    if not owner_outcome_target_valid(entities, outcome):
        raise ValueError(f"里程碑 owner_id 指向非法所有者: {milestone_id}")
    if field == "knowledge" and operator == "contains":
        _ensure_knowledge(row, subjects, outcome)
    elif field == "location" and operator == "eq":
        _ensure_location(canon, row, subjects, milestone_id, outcome)
    elif field not in {"knowledge", "location", "possessions"}:
        _ensure_state(row, subjects, milestone_id, outcome)


def _ensure_state(row, subjects, milestone_id, outcome):
    subject_id, field = outcome["subject_id"], outcome["field"]
    matches = [
        item
        for item in row["state_transitions"]
        if item.get("subject_id") == subject_id and item.get("field") == field
    ]
    if len(matches) > 1:
        raise ValueError(f"里程碑状态存在多段冲突: {milestone_id} {subject_id}.{field}")
    current = _get(subjects.get(subject_id) or {}, field)
    target = outcome.get("value")
    if outcome.get("operator") == "contains":
        base = matches[0].get("to_value") if matches else current
        if base is None:
            base = []
        if not isinstance(base, list):
            raise ValueError(f"里程碑 contains outcome 目标不是数组: {milestone_id}")
        target = list(base)
        if outcome.get("value") not in target:
            target.append(outcome.get("value"))
    if matches:
        matches[0]["to_value"] = target
        return
    if current != target:
        row["state_transitions"].append(
            {
                "subject_id": subject_id,
                "field": field,
                "from_value": current,
                "to_value": target,
                "reason": f"Canon milestone {milestone_id}",
            }
        )


def _ensure_knowledge(row, subjects, outcome):
    character_id, fact_id = outcome.get("subject_id"), outcome.get("value")
    knowledge = (subjects.get(character_id) or {}).get("knowledge") or []
    if fact_id in knowledge:
        return
    grants = row["knowledge_grants"]
    matches = [
        item
        for item in grants
        if item.get("character_id") == character_id and item.get("fact_id") == fact_id
    ]
    if matches:
        return
    event_ids = list(row.get("required_event_ids") or [])
    if isinstance(fact_id, str) and event_ids:
        grants.append(
            {
                "character_id": character_id,
                "fact_id": fact_id,
                "source_event_id": event_ids[-1],
            }
        )


def _ensure_location(canon, row, subjects, milestone_id, outcome):
    subject_id = outcome["subject_id"]
    target = persistent_location_id(canon, outcome.get("value"))
    current = (subjects.get(subject_id) or {}).get("location")
    matches = [
        item
        for item in row["location_transitions"]
        if item.get("subject_id") == subject_id
    ]
    if len(matches) > 1:
        raise ValueError(f"里程碑地点存在多段冲突: {milestone_id} {subject_id}")
    if matches:
        matches[0]["to_location_id"] = target
        matches[0].setdefault("means", f"Canon milestone {milestone_id}")
    elif current != target and isinstance(target, str) and target:
        row["location_transitions"].append(
            {
                "subject_id": subject_id,
                "from_location_id": current,
                "to_location_id": target,
                "means": f"Canon milestone {milestone_id}",
            }
        )


def _get(value: dict, path: str):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
