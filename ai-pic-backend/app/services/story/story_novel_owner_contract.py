"""Outcome-reference rules shared by Canon and state compilation."""

from __future__ import annotations


def owner_outcome_target_valid(entities: dict[str, dict], outcome: dict) -> bool:
    """Owner outcomes may clear ownership or target a real actor entity."""
    if outcome.get("field") != "owner_id" or outcome.get("operator") != "eq":
        return True
    owner_id = outcome.get("value")
    return owner_id is None or (entities.get(owner_id) or {}).get("kind") in {
        "character",
        "organization",
    }


def owner_outcome_errors(
    entities: dict[str, dict], outcomes: list[dict], milestone_id: str
) -> list[str]:
    invalid = [
        outcome.get("value")
        for outcome in outcomes
        if not owner_outcome_target_valid(entities, outcome)
    ]
    return (
        [f"里程碑 owner_id 指向非法所有者: {milestone_id} {invalid}"] if invalid else []
    )


def memory_outcome_subject_valid(entities: dict[str, dict], outcome: dict) -> bool:
    return (
        outcome.get("field") != "knowledge"
        or (entities.get(outcome.get("subject_id")) or {}).get("kind") == "character"
    )


def memory_outcome_errors(entities, outcomes, milestone_id):
    invalid = {
        item["subject_id"]
        for item in outcomes
        if item["subject_id"] in entities
        and not memory_outcome_subject_valid(entities, item)
    }
    return (
        [f"里程碑 knowledge outcome 只能授予角色: {milestone_id} {sorted(invalid)}"]
        if invalid
        else []
    )
