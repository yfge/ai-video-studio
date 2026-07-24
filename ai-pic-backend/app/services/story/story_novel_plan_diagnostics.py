from . import story_novel_initial_state as initial_state
from . import story_novel_location_rules as location_rules
from .story_novel_milestone_state import outcome_matches
from .story_novel_plan_diagnostic_format import format_plan_diagnostics
from .story_novel_plan_refs import generation_canon_ref_issues
from .story_novel_timeline_contract import generation_timeline_binding_issues


def generation_plan_diagnostic(canon: dict, chapters: list[dict]) -> str | None:
    if not chapters:
        return format_plan_diagnostics(["章节计划为空"])
    context = _context(canon)
    errors = [
        *generation_timeline_binding_issues(canon, chapters),
        *generation_canon_ref_issues(canon, chapters),
    ]
    for chapter in chapters:
        _diagnose_chapter(chapter, context, errors)
    _diagnose_completion(canon, chapters, context, errors)
    return format_plan_diagnostics(errors) if errors else None


def _context(canon: dict) -> dict:
    entities = canon.get("entities") or []
    return {
        "entity_ids": {item["id"] for item in entities},
        **location_rules.location_context(canon),
        "milestones": {item["id"]: item for item in canon.get("milestones") or []},
        "seen_events": set(),
        "seen_milestones": set(),
        "open_threads": set(),
        "state": initial_state.canonical_initial_subjects(canon),
    }


def _diagnose_chapter(chapter: dict, context: dict, errors: list[str]) -> None:
    position = int(chapter["position"])
    required = list(chapter.get("required_event_ids") or [])
    context["movement_state"] = location_rules.movement_start_state(
        chapter, context["state"]
    )
    _diagnose_events(chapter, position, required, context, errors)
    _diagnose_preconditions(chapter, position, context, errors)
    _diagnose_transitions(chapter, position, context, errors)
    _diagnose_movements(chapter, position, context, errors)
    _diagnose_knowledge(chapter, position, required, context, errors)
    _diagnose_milestones(chapter, position, context, errors)
    _diagnose_threads(chapter, position, context, errors)
    context["seen_events"].update(required)


def _diagnose_events(chapter, position, required, context, errors) -> None:
    if not required:
        errors.append(f"第 {position} 章缺少 required_event_ids")
    if any(not isinstance(item, str) or not item.strip() for item in required):
        errors.append(f"第 {position} 章 required_event_ids 包含空 ID")
    if len(required) != len(chapter.get("key_events") or []):
        errors.append(f"第 {position} 章 required_event_ids 与 key_events 不一一对应")
    duplicates = context["seen_events"].intersection(required)
    if duplicates or len(required) != len(set(required)):
        errors.append(f"事件 ID 重复: {sorted(duplicates or set(required))}")
    invalid = set(chapter.get("forbidden_event_ids") or []) - context["seen_events"]
    if invalid:
        errors.append(f"第 {position} 章禁止事件尚未发生: {sorted(invalid)}")


def _diagnose_preconditions(chapter, position, context, errors) -> None:
    for predicate in chapter.get("preconditions") or []:
        if _reject_encoded(predicate["value"], position, errors):
            continue
        subject = _subject(predicate["subject_id"], position, context, errors)
        if subject is None:
            continue
        actual = _get(subject, predicate["field"])
        if not _matches(actual, predicate["operator"], predicate["value"]):
            errors.append(f"第 {position} 章前置状态不连续: {predicate}")


def _diagnose_transitions(chapter, position, context, errors) -> None:
    for transition in chapter.get("state_transitions") or []:
        bad_value = _reject_encoded(transition.get("from_value"), position, errors)
        bad_value |= _reject_encoded(transition["to_value"], position, errors)
        if transition["field"] in {"knowledge", "location"}:
            errors.append(
                f"第 {position} 章 {transition['field']} 不能写入 state_transitions"
            )
            continue
        if transition.get("from_value") == transition.get("to_value"):
            errors.append(f"第 {position} 章状态转移起终值相同: {transition}")
            continue
        subject = _subject(transition["subject_id"], position, context, errors)
        if subject is None:
            continue
        actual = _get(subject, transition["field"])
        if actual != transition.get("from_value"):
            errors.append(f"第 {position} 章状态起点不连续: {transition}")
            continue
        if not bad_value:
            initial_state.apply_subject_transition(
                context["state"],
                transition["subject_id"],
                transition["field"],
                transition["to_value"],
            )


def _diagnose_movements(chapter, position, context, errors) -> None:
    for movement in chapter.get("location_transitions") or []:
        subject = _subject(movement["subject_id"], position, context, errors)
        if subject is None:
            continue
        start = context["movement_state"].get(movement["subject_id"], {})
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
            errors.append(f"第 {position} 章{issue}")
            continue
        initial_state.apply_subject_movement(
            context["state"], movement["subject_id"], movement["to_location_id"]
        )


def _diagnose_knowledge(chapter, position, required, context, errors) -> None:
    available_events = context["seen_events"] | set(required)
    for grant in chapter.get("knowledge_grants") or []:
        subject = _subject(grant["character_id"], position, context, errors)
        source_valid = grant["source_event_id"] in available_events
        if not source_valid:
            errors.append(
                f"第 {position} 章知识早于事件: {grant['fact_id']} "
                f"(source_event_id={grant['source_event_id']})"
            )
        if subject is None:
            continue
        knowledge = subject.setdefault("knowledge", [])
        duplicate = grant["fact_id"] in knowledge
        if duplicate:
            errors.append(f"第 {position} 章知识重复授予: {grant['fact_id']}")
        if source_valid and not duplicate:
            knowledge.append(grant["fact_id"])


def _diagnose_milestones(chapter, position, context, errors) -> None:
    consumed = list(chapter.get("milestones_consumed") or [])
    for milestone_id in consumed:
        milestone = context["milestones"].get(milestone_id)
        if not milestone:
            errors.append(f"第 {position} 章引用未知里程碑: {milestone_id}")
            continue
        if (
            not milestone.get("repeatable")
            and milestone_id in context["seen_milestones"]
        ):
            errors.append(f"里程碑重复消费: {milestone_id}")
        planned = milestone.get("planned_position")
        if planned not in {None, position}:
            errors.append(f"里程碑章节不匹配: {milestone_id}")
        context["seen_milestones"].add(milestone_id)
        for outcome in milestone.get("outcomes") or []:
            if not outcome_matches(context["state"], outcome):
                errors.append(
                    "里程碑结果未落地: "
                    f"{milestone_id} {outcome['subject_id']}.{outcome['field']} "
                    f"{outcome['operator']} {outcome['value']!r}"
                )
    for milestone in context["milestones"].values():
        planned = milestone.get("planned_position")
        if milestone.get("repeatable") or planned is None or int(planned) <= position:
            continue
        for outcome in milestone.get("outcomes") or []:
            if outcome_matches(context["state"], outcome):
                errors.append(
                    "状态提前包含未来里程碑结果: "
                    f"第 {planned} 章 {milestone['id']} "
                    f"{outcome['subject_id']}.{outcome['field']}"
                )


def _diagnose_threads(chapter, position, context, errors) -> None:
    payoffs = set(chapter.get("payoffs_due") or [])
    missing = payoffs - context["open_threads"]
    if missing:
        errors.append(f"第 {position} 章回收未知伏笔: {sorted(missing)}")
    context["open_threads"].difference_update(payoffs & context["open_threads"])
    context["open_threads"].update(chapter.get("open_threads") or [])


def _diagnose_completion(canon, chapters, context, errors) -> None:
    count = len(chapters)
    for milestone in context["milestones"].values():
        planned = milestone.get("planned_position")
        if planned and (
            int(planned) > count or milestone["id"] not in context["seen_milestones"]
        ):
            errors.append(f"计划遗漏里程碑: {milestone['id']}")
    if context["open_threads"]:
        errors.append(f"计划存在未回收伏笔: {sorted(context['open_threads'])}")


def _subject(subject_id, position, context, errors) -> dict | None:
    if subject_id not in context["entity_ids"]:
        errors.append(f"第 {position} 章引用未知实体: {subject_id}")
        return None
    return context["state"].setdefault(subject_id, {})


def _get(value: dict, path: str) -> object:
    current: object = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _matches(actual: object, operator: str, expected: object) -> bool:
    if operator in {"eq", "ne"}:
        equal = actual == expected
        return equal if operator == "eq" else not equal
    contains = expected in (actual or [])
    return contains if operator == "contains" else not contains


def _reject_encoded(value, position, errors) -> bool:
    invalid = isinstance(value, str) and value.strip().lower() in {"null", "[]", "{}"}
    if invalid:
        errors.append(
            f"第 {position} 章状态值必须使用真实 JSON 类型，不能写字符串 {value!r}"
        )
    return invalid
