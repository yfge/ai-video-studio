"""Deterministic validation for Canon-backed novel chapter plans."""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import story_novel_initial_state as state
from . import story_novel_location_rules as location_rules
from .story_novel_milestone_state import (
    validate_consumed_milestone_outcomes,
    validate_future_milestone_outcomes,
)
from .story_novel_plan_diagnostics import generation_plan_diagnostic
from .story_novel_plan_value_rules import predicate_matches, reject_encoded_json


def validate_generation_plan(canon: dict, chapters: list[dict]) -> None:
    diagnostic = generation_plan_diagnostic(canon, chapters)
    if diagnostic:
        raise ValueError(diagnostic)
    _validate_generation_plan_strict(canon, chapters)


def _validate_generation_plan_strict(canon: dict, chapters: list[dict]) -> None:
    if not chapters:
        raise ValueError("章节计划为空")
    counts = Counter(
        item for row in chapters for item in row.get("milestones_consumed") or []
    )
    once_only = {
        item["id"]
        for item in canon.get("milestones") or []
        if not item.get("repeatable")
    }
    duplicates = {item for item, count in counts.items() if count > 1} & once_only
    if duplicates:
        raise ValueError(f"里程碑重复消费: {sorted(duplicates)}")
    context = _validation_context(canon)
    for chapter in chapters:
        _validate_chapter(chapter, context)
    _validate_completion(canon, chapters, context)


def _validation_context(canon: dict) -> dict:
    entities = canon.get("entities") or []
    sections = ("timeline", "entities", "world_rules", "milestones", "character_arcs")
    return {
        "known": {
            str(item["character_id"] if section == "character_arcs" else item["id"])
            for section in sections
            for item in canon.get(section) or []
        },
        "entity_ids": {item["id"] for item in entities},
        **location_rules.location_context(canon),
        "milestones": {item["id"]: item for item in canon.get("milestones") or []},
        "seen_events": set(),
        "seen_milestones": set(),
        "open_threads": set(),
        "state": state.canonical_initial_subjects(canon),
    }


def _validate_chapter(chapter: dict, context: dict) -> None:
    position = int(chapter["position"])
    required = list(chapter.get("required_event_ids") or [])
    context["movement_state"] = location_rules.movement_start_state(
        chapter, context["state"]
    )
    _validate_events(chapter, position, required, context)
    _validate_refs(chapter, position, context)
    _validate_preconditions(chapter, position, context)
    _apply_transitions(chapter, position, context)
    _apply_movements(chapter, position, context)
    _apply_knowledge(chapter, position, required, context)
    _consume_milestones(chapter, position, context)
    _validate_milestone_outcomes(chapter, position, context)
    _update_threads(chapter, position, context)
    context["seen_events"].update(required)


def _validate_events(
    chapter: dict, position: int, required: list[str], context: dict
) -> None:
    if not required:
        raise ValueError(f"第 {position} 章缺少 required_event_ids")
    if any(not isinstance(item, str) or not item.strip() for item in required):
        raise ValueError(f"第 {position} 章 required_event_ids 包含空 ID")
    if len(required) != len(chapter.get("key_events") or []):
        raise ValueError(
            f"第 {position} 章 required_event_ids 与 key_events 不一一对应"
        )
    duplicates = context["seen_events"].intersection(required)
    if duplicates or len(required) != len(set(required)):
        raise ValueError(f"事件 ID 重复: {sorted(duplicates or set(required))}")
    invalid = set(chapter.get("forbidden_event_ids") or []) - context["seen_events"]
    if invalid:
        raise ValueError(f"第 {position} 章禁止事件尚未发生: {sorted(invalid)}")


def _validate_refs(chapter: dict, position: int, context: dict) -> None:
    refs = set(chapter.get("canon_refs") or [])
    invalid = refs - context["known"]
    if invalid:
        raise ValueError(f"第 {position} 章引用未知 Canon: {sorted(invalid)}")
    future_milestones = refs.intersection(context["milestones"]) - set(
        chapter.get("milestones_consumed") or []
    )
    if future_milestones:
        raise ValueError(f"第 {position} 章提前引用里程碑: {sorted(future_milestones)}")


def _validate_preconditions(chapter: dict, position: int, context: dict) -> None:
    for predicate in chapter.get("preconditions") or []:
        reject_encoded_json(predicate["value"], position)
        subject_id = predicate["subject_id"]
        _require_subject(subject_id, context["entity_ids"], position)
        actual = _get(context["state"].get(subject_id, {}), predicate["field"])
        if not predicate_matches(actual, predicate["operator"], predicate["value"]):
            raise ValueError(f"第 {position} 章前置状态不连续: {predicate}")


def _apply_transitions(chapter: dict, position: int, context: dict) -> None:
    for transition in chapter.get("state_transitions") or []:
        reject_encoded_json(transition.get("from_value"), position)
        reject_encoded_json(transition["to_value"], position)
        if transition["field"] in {"knowledge", "location", "possessions"}:
            raise ValueError(
                f"第 {position} 章 {transition['field']} 不能写入 state_transitions"
            )
        if transition.get("from_value") == transition.get("to_value"):
            raise ValueError(f"第 {position} 章状态转移起终值相同: {transition}")
        subject_id = transition["subject_id"]
        _require_subject(subject_id, context["entity_ids"], position)
        subject = context["state"].setdefault(subject_id, {})
        actual = _get(subject, transition["field"])
        if actual != transition.get("from_value"):
            raise ValueError(f"第 {position} 章状态起点不连续: {transition}")
        state.apply_subject_transition(
            context["state"],
            subject_id,
            transition["field"],
            transition["to_value"],
        )


def _apply_movements(chapter: dict, position: int, context: dict) -> None:
    for movement in chapter.get("location_transitions") or []:
        subject_id = movement["subject_id"]
        _require_subject(subject_id, context["entity_ids"], position)
        start = context["movement_state"].get(subject_id, {})
        subject = context["state"].setdefault(subject_id, {})
        issue = location_rules.planned_movement_issue(
            chapter,
            movement,
            kinds=context["entity_kinds"],
            initial=context["initial_statuses"],
            locations=context["locations"],
            current_location=subject.get("location"),
            current_status=start.get("status"),
        )
        if issue:
            raise ValueError(f"第 {position} 章{issue}")
        state.apply_subject_movement(
            context["state"], subject_id, movement["to_location_id"]
        )


def _apply_knowledge(
    chapter: dict, position: int, required: list[str], context: dict
) -> None:
    for grant in chapter.get("knowledge_grants") or []:
        character_id = grant["character_id"]
        _require_subject(character_id, context["entity_ids"], position)
        if grant["source_event_id"] not in required:
            raise ValueError(
                f"第 {position} 章知识来源不是本章事件: {grant['fact_id']}"
            )
        knowledge = (
            context["state"].setdefault(character_id, {}).setdefault("knowledge", [])
        )
        if grant["fact_id"] in knowledge:
            raise ValueError(f"第 {position} 章知识重复授予: {grant['fact_id']}")
        knowledge.append(grant["fact_id"])


def _consume_milestones(chapter: dict, position: int, context: dict) -> None:
    for milestone_id in chapter.get("milestones_consumed") or []:
        item = context["milestones"].get(milestone_id)
        if not item:
            raise ValueError(f"第 {position} 章引用未知里程碑: {milestone_id}")
        if not item.get("repeatable") and milestone_id in context["seen_milestones"]:
            raise ValueError(f"里程碑重复消费: {milestone_id}")
        if not item.get("repeatable") and item.get("planned_position") is None:
            raise ValueError(f"未指定章节的不可逆里程碑不能消费: {milestone_id}")
        if item.get("planned_position") not in {None, position}:
            raise ValueError(f"里程碑章节不匹配: {milestone_id}")
        context["seen_milestones"].add(milestone_id)


def _validate_milestone_outcomes(chapter: dict, position: int, context: dict) -> None:
    validate_consumed_milestone_outcomes(
        {"milestones": list(context["milestones"].values())},
        context["state"],
        chapter.get("milestones_consumed") or [],
        current_position=position,
    )
    validate_future_milestone_outcomes(
        {"milestones": list(context["milestones"].values())},
        context["state"],
        current_position=position,
    )


def _update_threads(chapter: dict, position: int, context: dict) -> None:
    payoffs = set(chapter.get("payoffs_due") or [])
    missing = payoffs - context["open_threads"]
    if missing:
        raise ValueError(f"第 {position} 章回收未知伏笔: {sorted(missing)}")
    context["open_threads"].difference_update(payoffs)
    context["open_threads"].update(chapter.get("open_threads") or [])


def _validate_completion(canon: dict, chapters: list[dict], context: dict) -> None:
    count = len(chapters)
    for milestone in context["milestones"].values():
        planned = milestone.get("planned_position")
        if planned and (
            planned > count or milestone["id"] not in context["seen_milestones"]
        ):
            raise ValueError(f"计划遗漏里程碑: {milestone['id']}")
    for arc in canon.get("character_arcs") or []:
        if any(item["position"] > count for item in arc.get("checkpoints") or []):
            raise ValueError(f"角色弧超出章节范围: {arc['character_id']}")
    if context["open_threads"]:
        raise ValueError(f"计划存在未回收伏笔: {sorted(context['open_threads'])}")


def _require_subject(subject_id: str, known: set[str], position: int) -> None:
    if subject_id not in known:
        raise ValueError(f"第 {position} 章引用未知实体: {subject_id}")


def _get(value: dict, path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current
