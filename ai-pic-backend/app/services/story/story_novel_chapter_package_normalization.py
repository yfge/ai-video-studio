"""Deterministic normalization for non-authoritative chapter package fields."""

import copy

from .story_novel_execution_normalization import normalize_execution_aliases

_EXECUTION_ENUMS = {
    "action_phase": ("start", "progress", "complete", "instant"),
    "time_scope": ("instant", "same_day", "multi_day", "unspecified"),
    "effort": ("none", "light", "moderate", "heavy", "unspecified"),
}


def strip_invalid_model_fields(
    contract: dict, state_before: dict | None = None
) -> dict:
    result = copy.deepcopy(contract)
    subjects = None
    if state_before is not None:
        subjects = state_before.get("subjects") or {}
    thread_ids = {
        str(value)
        for value in [
            *(result.get("open_threads") or []),
            *(result.get("payoffs_due") or []),
        ]
    }
    result["state_transitions"] = [
        item
        for item in result.get("state_transitions") or []
        if str(item.get("subject_id") or item.get("thread_id") or "") not in thread_ids
        and item.get("field") != "location"
        and (
            subjects is None
            or (
                isinstance(subjects.get(item.get("subject_id")), dict)
                and item.get("field") in subjects[item.get("subject_id")]
            )
        )
    ]
    result["preconditions"] = [
        item
        for item in result.get("preconditions") or []
        if not (isinstance(item, dict) and set(item) == {"predicate"})
    ]
    return result


def normalize_missing_contract_fields(
    contract: dict, canon: dict, state_before: dict | None = None
) -> dict:
    result = copy.deepcopy(contract)
    executions = result.get("execution_contracts") or []
    normalize_execution_aliases(executions)
    for transition in result.get("state_transitions") or []:
        _normalize_legacy_transition(transition, state_before)
        if (
            "field" not in transition
            and "from_status" in transition
            and "to_status" in transition
        ):
            transition["field"] = "status"
            transition["from_value"] = transition.pop("from_status")
            transition["to_value"] = transition.pop("to_status")
        if transition.get("field") and "from_value" not in transition:
            if "from" in transition:
                transition["from_value"] = transition.pop("from")
        if transition.get("field") and "to_value" not in transition:
            if "to" in transition:
                transition["to_value"] = transition.pop("to")
    result["knowledge_grants"] = _normalize_knowledge_grants(
        result.get("knowledge_grants") or [], executions
    )
    for grant in result["knowledge_grants"]:
        alias = grant.pop("subject_id", None)
        if grant.get("character_id") or alias:
            grant["character_id"] = grant.get("character_id") or alias
        else:
            grant.pop("character_id", None)
    for movement in result.get("location_transitions") or []:
        movement["subject_id"] = movement.get("subject_id") or movement.pop(
            "entity_id", None
        )
        movement["to_location_id"] = movement.get("to_location_id") or movement.pop(
            "to_location", None
        )
        if not movement.get("to_location_id") and "to" in movement:
            movement["to_location_id"] = movement.pop("to")
        if "from_location_id" not in movement and "from_location" in movement:
            movement["from_location_id"] = movement.pop("from_location")
        if "from_location_id" not in movement and "from" in movement:
            movement["from_location_id"] = movement.pop("from")
    result["location_transitions"] = [
        item
        for item in result.get("location_transitions") or []
        if not (
            isinstance(item.get("from_location_id"), str)
            and item.get("from_location_id") == item.get("to_location_id")
        )
    ]
    return result


def _normalize_legacy_transition(transition: dict, state_before: dict | None) -> None:
    """Translate predicate-shaped effects only when current state makes them exact."""
    if (
        "to_value" in transition
        or "value" not in transition
        or transition.get("preconditions")
    ):
        return
    subject_id, field = transition.get("subject_id"), transition.get("field")
    subject = ((state_before or {}).get("subjects") or {}).get(subject_id)
    if not isinstance(subject, dict) or field not in subject:
        return
    current = subject[field]
    operator = transition.get("operator")
    if operator in {"eq", "set"}:
        target = transition["value"]
    elif (
        operator in {"add", "add_to_set"}
        and isinstance(current, list)
        and not isinstance(transition["value"], (dict, list))
    ):
        target = copy.deepcopy(current)
        if transition["value"] not in target:
            target.append(copy.deepcopy(transition["value"]))
    else:
        return
    transition["from_value"] = copy.deepcopy(current)
    transition["to_value"] = target
    transition.pop("value", None)
    transition.pop("operator", None)
    transition.pop("preconditions", None)


def repairable_contract_issues(contract: dict) -> list[str]:
    """Report missing/invalid semantic fields together for the one repair call."""
    issues = []
    for index, execution in enumerate(contract.get("execution_contracts") or []):
        for field, allowed in _EXECUTION_ENUMS.items():
            value = execution.get(field)
            if value not in allowed:
                issues.append(
                    f"execution_contracts[{index}].{field}={value!r} 无效；"
                    f"必须选择 {'/'.join(allowed)}"
                )
    for index, grant in enumerate(contract.get("knowledge_grants") or []):
        for field in ("character_id", "fact_id", "source_event_id"):
            if not str(grant.get(field) or "").strip():
                issues.append(f"knowledge_grants[{index}].{field} 缺失，禁止服务端猜测")
        fact_id = grant.get("fact_id")
        source_event_id = grant.get("source_event_id")
        sources = {
            execution.get("event_id")
            for execution in contract.get("execution_contracts") or []
            if fact_id in (execution.get("knowledge_fact_ids") or [])
            and execution.get("event_id")
        }
        if fact_id and source_event_id and sources and source_event_id not in sources:
            issues.append(
                f"knowledge_grants[{index}].source_event_id={source_event_id!r} "
                f"与 execution_contracts 冲突；fact_id={fact_id!r} 只能绑定 "
                f"{'/'.join(sorted(sources))}"
            )
    transitions = contract.get("state_transitions") or []
    for index, movement in enumerate(contract.get("location_transitions") or []):
        for field in ("subject_id", "to_location_id"):
            if not str(movement.get(field) or "").strip():
                issues.append(f"location_transitions[{index}].{field} 缺失")
        if not str(movement.get("means") or "").strip():
            issues.append(f"location_transitions[{index}].means 缺少真实移动过程")
        origin_missing = "from_location_id" not in movement
        if origin_missing:
            issues.append(
                f"location_transitions[{index}].from_location_id 缺失；"
                "必须显式提供起点，若为 null 还必须同章提供该物件唯一 status 创建转换"
            )
        if origin_missing or movement.get("from_location_id") is None:
            subject_id = movement.get("subject_id")
            creations = [
                item
                for item in transitions
                if item.get("subject_id") == subject_id
                and item.get("field") == "status"
            ]
            if len(creations) != 1 and (not origin_missing or creations):
                issues.append(
                    f"location_transitions[{index}] 缺失或使用 null 起点时，"
                    "必须同章提供该物件唯一 status 创建转换，字段为 "
                    "subject_id/field=status/from_value/to_value/reason；"
                    "from_value 必须是 state_before 的显式缺席状态，"
                    "to_value 必须是非缺席状态且 reason 非空"
                )
            elif len(creations) == 1 and (
                not str(creations[0].get("from_value") or "").strip()
                or not str(creations[0].get("to_value") or "").strip()
                or not str(creations[0].get("reason") or "").strip()
            ):
                issues.append(
                    f"state_transitions 对 {subject_id} 的创建转换必须包含"
                    "显式 from_value、to_value 和非空 reason"
                )
    return issues


def _normalize_knowledge_grants(values: list[dict], executions: list[dict]):
    result = []
    for raw in values:
        item = dict(raw)
        facts = _explicit_fact_ids(item)
        if not isinstance(facts, list) or not facts:
            result.append(item)
            continue
        for fact_id in facts:
            grant = {**item, "fact_id": fact_id}
            sources = {
                execution.get("event_id")
                for execution in executions
                if fact_id in (execution.get("knowledge_fact_ids") or [])
                and execution.get("event_id")
            }
            if (
                grant.get("character_id")
                and not grant.get("source_event_id")
                and len(sources) == 1
            ):
                grant["source_event_id"] = sources.pop()
            result.append(grant)
    return result


def _explicit_fact_ids(item: dict) -> list:
    if item.get("fact_id"):
        return [item["fact_id"]]
    aliases = [
        item.get(key)
        for key in ("fact_ids", "knowledge_ids", "knowledge")
        if item.get(key)
    ]
    if not aliases or any(not isinstance(value, list) for value in aliases):
        return []
    if any(value != aliases[0] for value in aliases[1:]):
        return []
    for key in ("fact_ids", "knowledge_ids", "knowledge"):
        item.pop(key, None)
    return list(dict.fromkeys(aliases[0]))
