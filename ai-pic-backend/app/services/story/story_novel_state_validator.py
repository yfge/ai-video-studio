"""Deterministic hard gate for state extracted from a novel chapter body."""

from __future__ import annotations

from typing import Any

from .story_novel_location_rules import entity_kinds, initial_statuses
from .story_novel_milestone_state import (
    validate_consumed_milestone_outcomes,
    validate_future_milestone_outcomes,
)
from .story_novel_state_rules import (
    add_violation,
    require_subset,
    validate_knowledge,
    validate_milestones,
    validate_movements,
    validate_transitions,
)
from .story_novel_state_service import apply_state_delta, get_state_value


def validate_state_delta(
    canon: dict,
    chapter_plan: dict,
    state_before: dict,
    delta: dict,
) -> tuple[dict, dict]:
    violations: list[dict] = []
    context = _validation_context(canon, state_before, delta)
    _validate_events(chapter_plan, delta, context, violations)
    _validate_preconditions(chapter_plan, context["subjects"], violations)
    _validate_state_changes(chapter_plan, delta, context, violations)
    validate_milestones(canon, chapter_plan, state_before, delta, violations)
    _validate_threads(chapter_plan, delta, violations)
    _validate_world_rules(delta, violations)
    state_after = apply_state_delta(state_before, delta)
    _validate_outcome_boundaries(canon, chapter_plan, state_after, violations)
    return {
        "status": "failed" if violations else "passed",
        "violations": violations,
    }, state_after


def _validation_context(canon: dict, state_before: dict, delta: dict) -> dict:
    entities = canon.get("entities") or []
    return {
        "subjects": state_before.get("subjects") or {},
        "known_entities": {item["id"] for item in entities},
        "known_locations": {
            item["id"] for item in entities if item.get("kind") == "location"
        },
        "entity_kinds": entity_kinds(canon),
        "initial_statuses": initial_statuses(canon),
        "occurred_before": set(state_before.get("occurred_event_ids") or []),
        "occurred": set(delta.get("occurred_event_ids") or []),
    }


def _validate_events(plan: dict, delta: dict, context: dict, violations) -> None:
    occurred = context["occurred"]
    require_subset(
        plan.get("required_event_ids"),
        occurred,
        violations,
        "canon_violation",
        "正文缺少计划事件",
    )
    require_subset(
        occurred,
        set(plan.get("required_event_ids") or []),
        violations,
        "canon_violation",
        "正文出现未规划事件",
    )
    for event_id in delta.get("premature_future_event_ids") or []:
        add_violation(
            violations, "canon_violation", f"正文提前完成未来事件: {event_id}"
        )
    forbidden = set(plan.get("forbidden_event_ids") or [])
    for event_id in sorted(forbidden.intersection(occurred)):
        add_violation(
            violations, "canon_violation", f"重复或禁止事件再次发生: {event_id}"
        )
    for event_id in sorted(context["occurred_before"].intersection(occurred)):
        add_violation(violations, "canon_violation", f"事件 ID 再次发生: {event_id}")


def _validate_preconditions(plan: dict, subjects: dict, violations) -> None:
    for predicate in plan.get("preconditions") or []:
        actual = get_state_value(
            subjects.get(predicate["subject_id"], {}), predicate["field"]
        )
        if not _matches(actual, predicate["operator"], predicate["value"]):
            add_violation(
                violations,
                "state_reversion",
                f"前置状态不满足: {predicate['subject_id']}.{predicate['field']}",
            )


def _validate_state_changes(plan: dict, delta: dict, context: dict, violations) -> None:
    subjects = context["subjects"]
    known = context["known_entities"]
    transitioned = validate_transitions(plan, delta, subjects, known, violations)
    validate_movements(
        plan,
        delta,
        transitioned,
        subjects,
        known,
        context["known_locations"],
        context["entity_kinds"],
        context["initial_statuses"],
        violations,
    )
    validate_knowledge(
        plan,
        delta,
        known,
        context["occurred"],
        violations,
    )


def _validate_threads(plan: dict, delta: dict, violations) -> None:
    opened = set(delta.get("opened_thread_ids") or [])
    planned_opened = set(plan.get("open_threads") or [])
    resolved = set(delta.get("resolved_thread_ids") or [])
    planned_resolved = set(plan.get("payoffs_due") or [])
    for required, actual, label in (
        (planned_opened, opened, "正文遗漏计划伏笔"),
        (opened, planned_opened, "正文提前打开未规划伏笔"),
        (planned_resolved, resolved, "正文未回收到期伏笔"),
        (resolved, planned_resolved, "正文提前回收未来伏笔"),
    ):
        require_subset(required, actual, violations, "canon_violation", label)


def _validate_world_rules(delta: dict, violations) -> None:
    for rule_id in delta.get("world_rule_violations") or []:
        add_violation(violations, "canon_violation", f"正文违反世界规则: {rule_id}")


def _validate_outcome_boundaries(canon, plan, state_after, violations) -> None:
    subjects = state_after.get("subjects") or {}
    position = int(plan["position"])
    checks = (
        lambda: validate_consumed_milestone_outcomes(
            canon,
            subjects,
            plan.get("milestones_consumed") or [],
            current_position=position,
        ),
        lambda: validate_future_milestone_outcomes(
            canon,
            subjects,
            current_position=position,
        ),
    )
    for check in checks:
        try:
            check()
        except ValueError as exc:
            add_violation(violations, "canon_violation", str(exc))


def _matches(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "contains":
        return expected in (actual or [])
    return expected not in (actual or [])
