"""Reference validation for independent chapter-plan effect audits."""

_ISSUE_CODES = {
    "action_phase_conflict",
    "effect_event_attribution",
    "end_state_conflict",
    "knowledge_effect_conflict",
    "knowledge_source_attribution",
    "labor_feasibility",
    "timeline_duration_conflict",
    "world_rule_conflict",
}
_ADVISORY_ISSUE_CODES = {
    "effect_event_attribution",
    "knowledge_source_attribution",
    "labor_feasibility",
}


def validated_feasibility_issues(values, *, action_phase: str | None = None):
    result = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {
            "code",
            "severity",
            "message",
        }:
            raise ValueError("章节计划可执行性问题结构无效")
        code, message = value.get("code"), str(value.get("message") or "").strip()
        reported_severity = value.get("severity")
        if (
            code not in _ISSUE_CODES
            or reported_severity not in {"blocking", "advisory"}
            or not message
        ):
            raise ValueError("章节计划可执行性问题内容无效")
        if code == "action_phase_conflict":
            severity = (
                "advisory" if action_phase in {"start", "progress"} else "blocking"
            )
        else:
            severity = "advisory" if code in _ADVISORY_ISSUE_CODES else "blocking"
        result.append({"code": code, "severity": severity, "message": message})
    return result


def canon_fact_ids(canon):
    return {
        outcome.get("value")
        for milestone in canon.get("milestones") or []
        for outcome in milestone.get("outcomes") or []
        if outcome.get("field") == "knowledge"
        and outcome.get("operator") == "contains"
        and isinstance(outcome.get("value"), str)
    }


def chapter_actor_refs(chapter: dict, entities: list[dict]) -> set[str]:
    actors = {
        item["id"]: (item.get("kind"), {item.get("name"), *(item.get("aliases") or [])})
        for item in entities
        if item.get("kind") in {"character", "organization"}
    }
    refs = set(chapter.get("canon_refs") or [])
    for field in ("preconditions", "state_transitions", "location_transitions"):
        for row in chapter.get(field) or []:
            refs.add(row.get("subject_id"))
            for key in ("value", "from_value", "to_value"):
                value = row.get(key)
                if isinstance(value, str):
                    refs.add(value)
    refs.update(
        row.get("character_id") for row in chapter.get("knowledge_grants") or []
    )
    focus = {
        str(value).strip()
        for value in chapter.get("character_focus") or []
        if str(value).strip()
    }
    events = "\n".join(str(value) for value in chapter.get("key_events") or [])
    refs.update(
        actor_id
        for actor_id, (kind, names) in actors.items()
        if any(
            name
            and (
                any(value in str(name) or str(name) in value for value in focus)
                or _name_appears_in_events(str(name), events, kind)
            )
            for name in names
        )
    )
    return set(actors).intersection(refs)


def _name_appears_in_events(name: str, events: str, kind: str) -> bool:
    if name in events:
        return True
    if kind != "organization":
        return False
    return any(name[offset:] in events for offset in range(1, max(1, len(name) - 2)))


def validate_effect_refs(
    event_id,
    grants,
    transitions,
    movements,
    consumed,
    known,
    locations,
    milestones,
    canon_facts,
    existing_facts,
):
    if any(
        grant["source_event_id"] != event_id
        or not _valid_fact_id(grant["fact_id"], event_id, canon_facts, existing_facts)
        for grant in grants
    ):
        raise ValueError(f"语义审计知识引用无效: {event_id}")
    if any(row["subject_id"] not in known for row in transitions):
        raise ValueError(f"语义审计状态主体无效: {event_id}")
    if any(
        row["subject_id"] not in known
        or {row["from_location_id"], row["to_location_id"]} - locations - {None}
        for row in movements
    ):
        raise ValueError(f"语义审计地点引用无效: {event_id}")
    if not set(consumed).issubset(milestones):
        raise ValueError(f"语义审计里程碑引用无效: {event_id}")


def assign_generated_fact_ids(
    event_id: str,
    grants: list[dict],
    canon_facts: set,
    existing_facts: set[tuple],
) -> list[dict]:
    """Keep semantic refs strict while assigning IDs for new event-local facts."""
    aliases: dict[str, str] = {}
    used = {
        fact_id
        for source_event_id, fact_id in existing_facts
        if source_event_id == event_id
    }
    assigned = []
    for grant in grants:
        fact_id = str(grant.get("fact_id") or "")
        if (
            fact_id in canon_facts
            or (event_id, fact_id) in existing_facts
            or _valid_fact_id(fact_id, event_id, canon_facts, existing_facts)
            or fact_id.startswith("fact-evt-")
        ):
            assigned.append(grant)
            continue
        if fact_id not in aliases:
            index = 1
            candidate = f"fact-{event_id}-{index}"
            while candidate in used:
                index += 1
                candidate = f"fact-{event_id}-{index}"
            aliases[fact_id] = candidate
            used.add(candidate)
        assigned.append({**grant, "fact_id": aliases[fact_id]})
    return assigned


def bind_missing_knowledge_sources(chapter: dict, grants: list) -> list:
    """Bind a missing source only when execution contracts prove one event."""
    events_by_fact: dict[str, set[str]] = {}
    for execution in chapter.get("execution_contracts") or []:
        if not isinstance(execution, dict):
            continue
        event_id = execution.get("event_id")
        for fact_id in execution.get("knowledge_fact_ids") or []:
            if event_id and fact_id:
                events_by_fact.setdefault(str(fact_id), set()).add(str(event_id))
    result = []
    for raw in grants:
        if not isinstance(raw, dict) or raw.get("source_event_id"):
            result.append(raw)
            continue
        candidates = events_by_fact.get(str(raw.get("fact_id") or ""), set())
        result.append(
            {**raw, "source_event_id": next(iter(candidates))}
            if len(candidates) == 1
            else raw
        )
    return result


def _valid_fact_id(fact_id, event_id, canon_facts, existing_facts):
    if fact_id in canon_facts or (event_id, fact_id) in existing_facts:
        return True
    prefix = f"fact-{event_id}-"
    suffix = fact_id[len(prefix) :] if fact_id.startswith(prefix) else ""
    return suffix.isdigit() and int(suffix) > 0
