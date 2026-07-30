"""Typed event execution contracts produced by the independent plan audit."""

from __future__ import annotations

from copy import deepcopy

from app.schemas.story_novel_longform import (
    StoryNovelEventExecution,
    StoryNovelKnowledgeGrant,
    StoryNovelLocationTransition,
    StoryNovelStateTransition,
)
from app.utils.json_utils import extract_json_block
from pydantic import ValidationError

from .story_novel_plan_effect_refs import (
    assign_generated_fact_ids,
    canon_fact_ids,
    chapter_actor_refs,
    validate_effect_refs,
    validated_feasibility_issues,
)
from .story_novel_plan_semantic_effects import validated_unsupported_effects


def parse_plan_semantic_audit(text: str, canon: dict, chapters: list[dict]):
    payload = _audit_payload(text)
    events = payload["events"]
    expected = _expected_events(chapters)
    actual = [
        (int(item.get("position") or 0), str(item.get("event_id") or ""))
        for item in events
        if isinstance(item, dict)
    ]
    if actual != expected or len(events) != len(expected):
        raise ValueError(
            f"章节计划语义审计事件覆盖不完整: expected={expected}, actual={actual}"
        )
    return _validated_events(events, canon, chapters)


def apply_execution_contracts(chapters: list[dict], audit: list[dict]) -> list[dict]:
    result = deepcopy(chapters)
    by_position: dict[int, list[dict]] = {}
    for event in audit:
        by_position.setdefault(event["position"], []).append(
            event["execution_contract"]
        )
    for chapter in result:
        chapter["execution_contracts"] = by_position.get(int(chapter["position"]), [])
    return result


def execution_issues(audit: list[dict], *, severity: str | None = None) -> list[dict]:
    return [
        {"position": event["position"], "event_id": event["event_id"], **issue}
        for event in audit
        for issue in event["feasibility_issues"]
        if severity is None or issue["severity"] == severity
    ]


def execution_contracts_valid(chapter: dict) -> bool:
    required = list(chapter.get("required_event_ids") or [])
    rows = list(chapter.get("execution_contracts") or [])
    try:
        parsed = [
            StoryNovelEventExecution.model_validate(row).model_dump() for row in rows
        ]
    except (TypeError, ValidationError):
        return False
    if [row["event_id"] for row in parsed] != required:
        return False
    bindings = chapter.get("timeline_event_bindings") or {}
    grants = chapter.get("knowledge_grants") or []
    return all(
        row["timeline_ids"]
        == [key for key, value in bindings.items() if value == row["event_id"]]
        and list(dict.fromkeys(row["knowledge_fact_ids"]))
        == list(
            dict.fromkeys(
                item["fact_id"]
                for item in grants
                if item.get("source_event_id") == row["event_id"]
            )
        )
        for row in parsed
    )


def _audit_payload(text: str) -> dict:
    payload = extract_json_block(text)
    if payload is None and text.strip().startswith("["):
        payload = extract_json_block(f'{{"events":{text.strip()}}}')
    if isinstance(payload, dict) and set(payload) == {"output_skeleton"}:
        payload = payload["output_skeleton"]
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError("章节计划语义审计未返回 events JSON")
    return payload


def _expected_events(chapters: list[dict]) -> list[tuple[int, str]]:
    return [
        (int(chapter["position"]), event_id)
        for chapter in chapters
        for event_id in chapter.get("required_event_ids") or []
    ]


def _validated_events(events: list[dict], canon: dict, chapters: list[dict]):
    entities = list(canon.get("entities") or [])
    known = {item["id"] for item in entities}
    characters = {item["id"] for item in entities if item.get("kind") == "character"}
    locations = {item["id"] for item in entities if item.get("kind") == "location"}
    milestones = {item["id"] for item in canon.get("milestones") or []}
    canon_facts = canon_fact_ids(canon)
    existing_facts = {
        (grant.get("source_event_id"), grant.get("fact_id"))
        for chapter in chapters
        for grant in chapter.get("knowledge_grants") or []
    }
    by_position = {int(item["position"]): item for item in chapters}
    try:
        return [
            _validated_event(
                item,
                by_position[int(item["position"])],
                known,
                characters,
                locations,
                milestones,
                canon_facts,
                existing_facts,
                entities,
            )
            for item in events
        ]
    except (KeyError, TypeError, ValidationError) as exc:
        raise ValueError(f"章节计划语义审计结构无效: {exc}") from exc


def _validated_event(
    item,
    chapter,
    known,
    characters,
    locations,
    milestones,
    canon_facts,
    existing_facts,
    entities,
):
    event_id = str(item["event_id"])
    effects = item.get("missing_effects") or {}
    grants = [
        StoryNovelKnowledgeGrant.model_validate(
            {"source_event_id": event_id, **value}
        ).model_dump()
        for value in effects.get("knowledge_grants") or []
    ]
    grants = [row for row in grants if row["character_id"] in characters]
    grants = assign_generated_fact_ids(event_id, grants, canon_facts, existing_facts)
    transitions = [
        StoryNovelStateTransition.model_validate(value).model_dump()
        for value in effects.get("state_transitions") or []
    ]
    movements = [
        StoryNovelLocationTransition.model_validate(value).model_dump()
        for value in effects.get("location_transitions") or []
    ]
    consumed = [str(value) for value in effects.get("milestones_consumed") or []]
    validate_effect_refs(
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
    )
    execution = _validated_execution(item, chapter, entities, event_id)
    issues = validated_feasibility_issues(
        item.get("feasibility_issues") or [], action_phase=execution["action_phase"]
    )
    event_ids = list(chapter.get("required_event_ids") or [])
    return {
        "position": int(item["position"]),
        "event_id": event_id,
        "event_order": event_ids.index(event_id),
        "execution_contract": execution,
        "feasibility_issues": issues,
        "missing_effects": {
            "knowledge_grants": grants,
            "state_transitions": transitions,
            "location_transitions": movements,
            "milestones_consumed": consumed,
        },
        "unsupported_effects": validated_unsupported_effects(item, chapter),
    }


def _validated_execution(item, chapter, entities, event_id):
    execution = StoryNovelEventExecution.model_validate(
        {"event_id": event_id, **(item.get("execution_contract") or {})}
    ).model_dump()
    if execution["event_id"] != event_id:
        raise ValueError(f"语义审计 execution event_id 无效: {event_id}")
    allowed_actors = chapter_actor_refs(chapter, entities)
    actor_entities = {
        item["id"]
        for item in entities
        if item.get("kind") in {"character", "organization"}
    }
    reported_actors = list(execution["actor_ids"])
    if set(reported_actors) - actor_entities:
        raise ValueError(f"语义审计 actor 引用无效: {event_id}")
    execution["actor_ids"] = [
        actor_id for actor_id in reported_actors if actor_id in allowed_actors
    ]
    expected_timeline = [
        timeline_id
        for timeline_id, bound in (chapter.get("timeline_event_bindings") or {}).items()
        if bound == event_id
    ]
    expected_facts = list(
        dict.fromkeys(
            grant["fact_id"]
            for grant in chapter.get("knowledge_grants") or []
            if grant.get("source_event_id") == event_id
        )
    )
    execution["timeline_ids"] = expected_timeline
    execution["knowledge_fact_ids"] = expected_facts
    return execution
