"""Focused deterministic rules used by the long-form chapter state gate."""

from __future__ import annotations

import copy

from .story_novel_initial_state import apply_subject_movement, apply_subject_transition
from .story_novel_location_rules import is_initial_object_placement
from .story_novel_state_service import get_state_value


def validate_transitions(plan, delta, subjects, known, violations) -> dict:
    planned = {_transition_key(item) for item in plan.get("state_transitions") or []}
    actual = {_transition_key(item) for item in delta.get("state_transitions") or []}
    require_subset(
        planned,
        actual,
        violations,
        "canon_violation",
        "正文缺少计划状态转移",
    )
    require_subset(
        actual,
        planned,
        violations,
        "canon_violation",
        "正文出现未规划状态转移",
    )
    replayed = copy.deepcopy(subjects)
    for item in delta.get("state_transitions") or []:
        subject_id = item["subject_id"]
        if subject_id not in known:
            add_violation(
                violations, "canon_violation", f"状态转移引用未知实体: {subject_id}"
            )
            continue
        if item["field"] in {"knowledge", "location", "possessions"}:
            add_violation(
                violations,
                "canon_violation",
                f"{item['field']} 不能写入 state_transitions: {subject_id}",
            )
            continue
        if item.get("from_value") == item.get("to_value"):
            add_violation(
                violations,
                "canon_violation",
                f"状态转移起终值相同: {subject_id}.{item['field']}",
            )
            continue
        actual_value = get_state_value(replayed.get(subject_id, {}), item["field"])
        if actual_value != item.get("from_value"):
            add_violation(
                violations,
                "state_reversion",
                f"状态被回滚: {subject_id}.{item['field']}",
            )
        else:
            apply_subject_transition(
                replayed,
                subject_id,
                item["field"],
                item.get("to_value"),
            )
    return replayed


def validate_movements(
    plan,
    delta,
    subjects,
    original_subjects,
    known,
    locations,
    kinds,
    initial,
    violations,
) -> None:
    planned = {_movement_key(item) for item in plan.get("location_transitions") or []}
    actual = {_movement_key(item) for item in delta.get("location_transitions") or []}
    require_subset(
        planned,
        actual,
        violations,
        "unexplained_location",
        "正文缺少计划移动",
    )
    require_subset(
        actual,
        planned,
        violations,
        "unexplained_location",
        "正文出现未规划移动",
    )
    replayed = copy.deepcopy(subjects)
    for item in delta.get("location_transitions") or []:
        subject_id = item["subject_id"]
        subject = replayed.get(subject_id) or {}
        original = original_subjects.get(subject_id) or {}
        current = subject.get("location")
        origin = item.get("from_location_id")
        valid_start = (
            current == origin
            if origin is not None
            else is_initial_object_placement(
                delta,
                item,
                kinds=kinds,
                initial=initial,
                current_location=current,
                current_status=original.get("status"),
            )
        )
        if (
            subject_id not in known
            or item["to_location_id"] not in locations
            or (origin is not None and origin not in locations)
            or origin == item.get("to_location_id")
            or not valid_start
            or not str(item.get("means") or "").strip()
        ):
            add_violation(
                violations,
                "unexplained_location",
                f"地点移动无有效过场: {subject_id}",
            )
        else:
            apply_subject_movement(replayed, subject_id, item["to_location_id"])


def validate_knowledge(plan, delta, known, occurred, violations) -> None:
    planned = {_grant_key(item) for item in plan.get("knowledge_grants") or []}
    actual = {_grant_key(item) for item in delta.get("knowledge_grants") or []}
    require_subset(
        planned,
        actual,
        violations,
        "illegal_knowledge",
        "正文缺少计划知识授予",
    )
    require_subset(
        actual,
        planned,
        violations,
        "illegal_knowledge",
        "正文出现未规划知识授予",
    )
    for item in delta.get("knowledge_grants") or []:
        if item["character_id"] not in known or item["source_event_id"] not in occurred:
            add_violation(
                violations,
                "illegal_knowledge",
                f"角色无来源地获知事实: {item['character_id']}->{item['fact_id']}",
            )


def validate_milestones(canon, plan, state, delta, violations) -> None:
    planned = set(plan.get("milestones_consumed") or [])
    actual = set(delta.get("milestones_consumed") or [])
    require_subset(
        planned,
        actual,
        violations,
        "canon_violation",
        "正文遗漏计划里程碑",
    )
    milestones = {item["id"]: item for item in canon.get("milestones") or []}
    completed = set(state.get("completed_milestone_ids") or [])
    for milestone_id in actual:
        milestone = milestones.get(milestone_id)
        if not milestone:
            add_violation(violations, "canon_violation", f"未知里程碑: {milestone_id}")
        elif milestone_id not in planned:
            add_violation(
                violations, "canon_violation", f"提前消费里程碑: {milestone_id}"
            )
        elif (
            not milestone.get("repeatable")
            and milestone.get("planned_position") is None
        ):
            add_violation(
                violations,
                "canon_violation",
                f"未指定章节的不可逆里程碑不能消费: {milestone_id}",
            )
        elif milestone_id in completed:
            add_violation(
                violations,
                "duplicate_milestone",
                f"里程碑重复发生: {milestone_id}",
            )


def add_violation(violations: list[dict], code: str, message: str) -> None:
    violations.append({"code": code, "message": message})


def require_subset(required, actual: set, violations, code: str, label: str) -> None:
    missing = set(required or []) - actual
    for item in sorted(missing, key=str):
        add_violation(violations, code, f"{label}: {item}")


def _transition_key(item: dict) -> tuple:
    return (
        item["subject_id"],
        item["field"],
        repr(item.get("from_value")),
        repr(item.get("to_value")),
    )


def _movement_key(item: dict) -> tuple:
    return (item["subject_id"], item["from_location_id"], item["to_location_id"])


def _grant_key(item: dict) -> tuple:
    return (item["character_id"], item["fact_id"], item["source_event_id"])
