"""Deterministic state assertions for one-time novel milestones."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable
from typing import Any

from .story_novel_initial_state import (
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_location_rules import TERMINAL_OBJECT_STATUS_LITERALS


def validate_milestone_outcome_contract(canon: dict) -> None:
    """Require valid outcomes and a chapter-zero state before one repair."""
    errors = _milestone_outcome_contract_errors(canon)
    future_violations = _future_milestone_outcome_violations(
        canon,
        canonical_initial_subjects(canon),
        current_position=0,
    )
    if future_violations:
        errors.append(f"状态提前包含未来里程碑结果: {'；'.join(future_violations)}")
    if errors:
        raise ValueError("；".join(errors))


def _milestone_outcome_contract_errors(canon: dict) -> list[str]:
    entities = {item["id"]: item for item in canon.get("entities") or []}
    entity_ids = set(entities)
    errors: list[str] = []
    signatures: dict[tuple, list[str]] = {}
    for milestone in _gated_milestones(canon):
        outcomes = milestone.get("outcomes") or []
        if not outcomes:
            errors.append(f"一次性里程碑缺少 outcomes: {milestone['id']}")
            continue
        unknown = {
            outcome["subject_id"]
            for outcome in outcomes
            if outcome["subject_id"] not in entity_ids
        }
        if unknown:
            errors.append(
                f"里程碑 outcome 引用未知实体: {milestone['id']} {sorted(unknown)}"
            )
        invalid_values = [
            outcome
            for outcome in outcomes
            if _is_encoded_json_container(outcome.get("value"))
        ]
        if invalid_values:
            errors.append(
                f"里程碑 outcome value 必须使用真实 JSON 值: {milestone['id']}"
            )
        for outcome in outcomes:
            signatures.setdefault(_outcome_signature(outcome), []).append(
                milestone["id"]
            )
        errors.extend(_terminal_object_errors(milestone, outcomes, entities))
    for signature, milestone_ids in signatures.items():
        unique_ids = list(dict.fromkeys(milestone_ids))
        if len(unique_ids) > 1:
            errors.append(
                "重复 milestone outcome: "
                f"{', '.join(unique_ids)} -> "
                f"{signature[0]}.{signature[1]} {signature[2]} {signature[3]}"
            )
    return errors


def _terminal_object_errors(
    milestone: dict,
    outcomes: list[dict],
    entities: dict[str, dict],
) -> list[str]:
    terminal_statuses = set(TERMINAL_OBJECT_STATUS_LITERALS)
    destroyed_ids = {
        item["subject_id"]
        for item in outcomes
        if item["field"] == "status"
        and item["operator"] == "eq"
        and str(item.get("value") or "").strip().lower() in terminal_statuses
        and (entities.get(item["subject_id"]) or {}).get("kind") == "object"
    }
    cleared_owner_ids = {
        item["subject_id"]
        for item in outcomes
        if item["field"] == "owner_id"
        and item["operator"] == "eq"
        and item.get("value") is None
    }
    return [
        f"物件终态里程碑必须清空 owner_id: {milestone['id']} {subject_id}"
        for subject_id in sorted(destroyed_ids - cleared_owner_ids)
    ]


def validate_future_milestone_outcomes(
    canon: dict,
    subjects: dict,
    *,
    current_position: int,
) -> None:
    """Reject any one-time outcome that becomes true before its chapter."""
    violations = _future_milestone_outcome_violations(
        canon,
        subjects,
        current_position=current_position,
    )
    if violations:
        raise ValueError(f"状态提前包含未来里程碑结果: {'；'.join(violations)}")


def _future_milestone_outcome_violations(
    canon: dict,
    subjects: dict,
    *,
    current_position: int,
) -> list[str]:
    violations: list[str] = []
    milestones = sorted(
        _gated_milestones(canon), key=lambda x: int(x["planned_position"])
    )
    for milestone in milestones:
        planned_position = int(milestone["planned_position"])
        if planned_position <= current_position:
            continue
        projected = copy.deepcopy(subjects)
        for prior in milestones:
            prior_position = int(prior["planned_position"])
            if current_position < prior_position < planned_position:
                for outcome in prior.get("outcomes") or []:
                    _apply_outcome(projected, outcome)
        for outcome in milestone.get("outcomes") or []:
            if outcome_matches(subjects, outcome) and outcome_matches(
                projected, outcome
            ):
                violations.append(
                    f"第 {planned_position} 章 {milestone['id']} "
                    f"{outcome['subject_id']}.{outcome['field']}"
                )
    return violations


def _apply_outcome(subjects: dict, outcome: dict) -> None:
    value = outcome["value"]
    if outcome["operator"] == "contains":
        value = list(
            _state_value(subjects.get(outcome["subject_id"], {}), outcome["field"])
            or []
        )
        if outcome["value"] not in value:
            value.append(outcome["value"])
    apply_subject_transition(subjects, outcome["subject_id"], outcome["field"], value)


def validate_consumed_milestone_outcomes(
    canon: dict,
    subjects: dict,
    milestone_ids: Iterable[str],
    *,
    current_position: int | None = None,
) -> None:
    """Require every consumed milestone outcome to exist in state."""
    milestones = {item["id"]: item for item in canon.get("milestones") or []}
    for milestone_id in milestone_ids:
        milestone = milestones.get(milestone_id)
        if not milestone:
            raise ValueError(f"引用未知里程碑: {milestone_id}")
        planned_position = milestone.get("planned_position")
        if (
            current_position is not None
            and planned_position is not None
            and int(planned_position) != current_position
        ):
            raise ValueError(f"里程碑章节不匹配: {milestone_id}")
        for outcome in milestone.get("outcomes") or []:
            if not outcome_matches(subjects, outcome):
                raise ValueError(
                    "里程碑结果未落地: "
                    f"{milestone_id} "
                    f"{outcome['subject_id']}.{outcome['field']} "
                    f"{outcome['operator']} {outcome['value']!r}"
                )


def outcome_matches(subjects: dict, outcome: dict) -> bool:
    actual = _state_value(
        subjects.get(outcome["subject_id"], {}),
        outcome["field"],
    )
    if outcome["operator"] == "eq":
        return actual == outcome["value"]
    return isinstance(actual, (list, tuple, set)) and outcome["value"] in actual


def _gated_milestones(canon: dict) -> list[dict]:
    return [
        item
        for item in canon.get("milestones") or []
        if not item.get("repeatable") and item.get("planned_position") is not None
    ]


def _state_value(value: dict, path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _is_encoded_json_container(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() in {"null", "[]", "{}"}


def _outcome_signature(outcome: dict) -> tuple:
    value = json.dumps(
        outcome.get("value"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return (
        outcome["subject_id"],
        outcome["field"],
        outcome["operator"],
        value,
    )
