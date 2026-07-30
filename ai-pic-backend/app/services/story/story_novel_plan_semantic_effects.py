"""Deterministic checks for semantic-audit suggestions."""

import json
from copy import deepcopy

from .story_novel_plan_validator import _validate_chapter, _validation_context

_FIELDS = (
    "knowledge_grants",
    "state_transitions",
    "location_transitions",
    "milestones_consumed",
)


def validated_unsupported_effects(item, chapter):
    effects = item.get("unsupported_effects") or {}
    unknown = set(effects) - set(_FIELDS)
    if unknown:
        raise ValueError(f"语义审计 unsupported effect 字段无效: {sorted(unknown)}")
    result = {field: list(effects.get(field) or []) for field in _FIELDS}
    for field, values in result.items():
        if any(value not in (chapter.get(field) or []) for value in values):
            raise ValueError(f"语义审计试图删除不存在的 effect: {field}")
    return result


def remove_unsupported_effects(chapters, audit):
    result = deepcopy(chapters)
    audit_by_position = {}
    for event in audit:
        audit_by_position.setdefault(event["position"], []).append(event)
    count = 0
    for chapter in result:
        reports = audit_by_position.get(int(chapter["position"])) or []
        for field in _FIELDS:
            values = list(chapter.get(field) or [])
            chapter[field] = [
                value
                for value in values
                if not _is_safely_unsupported(value, field, chapter, reports)
            ]
            count += len(values) - len(chapter[field])
    return result, count


def _is_safely_unsupported(value, field, chapter, reports) -> bool:
    if field == "knowledge_grants":
        source_event_id = (
            value.get("source_event_id") if isinstance(value, dict) else None
        )
        return bool(
            source_event_id
            and any(
                event["event_id"] == source_event_id
                and value in event["unsupported_effects"][field]
                for event in reports
            )
        )
    event_ids = list(chapter.get("required_event_ids") or [])
    return bool(
        event_ids
        and all(
            any(
                event["event_id"] == event_id
                and value in event["unsupported_effects"][field]
                for event in reports
            )
            for event_id in event_ids
        )
    )


def audit_has_effects(audit):
    return any(
        event[kind][field]
        for event in audit
        for kind in ("missing_effects", "unsupported_effects")
        for field in _FIELDS
    )


def filter_redundant_audit_effects(audit, canon, prior_chapters, chapters):
    _drop_refined_state_chains(audit, chapters)
    context = _validation_context(canon)
    for chapter in prior_chapters:
        _validate_chapter(chapter, context)
    known_before = _known_facts(context["state"])
    knowledge_sources = _knowledge_sources(chapters)
    audit_by_event = {(event["position"], event["event_id"]): event for event in audit}
    state_after, by_position, state_keys = {}, {}, {}
    for chapter in chapters:
        position = int(chapter["position"])
        by_position[position] = chapter
        state_keys[position] = {
            _state_transition_key(item)
            for item in chapter.get("state_transitions") or []
        }
        _validate_chapter(chapter, context)
        state_after[position] = deepcopy(context["state"])
    for event in audit:
        position = event["position"]
        chapter = by_position[position]
        effects = event["missing_effects"]
        effects["knowledge_grants"] = _new_knowledge_grants(
            effects["knowledge_grants"],
            event,
            known_before,
            knowledge_sources,
            audit_by_event,
        )
        kept_transitions = []
        for transition in effects["state_transitions"]:
            key = _state_transition_key(transition)
            if key in state_keys[position]:
                continue
            kept_transitions.append(transition)
            state_keys[position].add(key)
        effects["state_transitions"] = kept_transitions
        existing_milestones = chapter.get("milestones_consumed") or []
        effects["milestones_consumed"] = [
            value
            for value in effects["milestones_consumed"]
            if value not in existing_milestones
        ]
        existing = {
            (item["subject_id"], item.get("from_location_id"), item["to_location_id"])
            for item in chapter.get("location_transitions") or []
        }
        kept = []
        for movement in effects["location_transitions"]:
            key = (
                movement["subject_id"],
                movement.get("from_location_id"),
                movement["to_location_id"],
            )
            subject = state_after[position].setdefault(movement["subject_id"], {})
            if key in existing or subject.get("location") == movement["to_location_id"]:
                continue
            kept.append(movement)
            subject["location"] = movement["to_location_id"]
        effects["location_transitions"] = kept
    return audit


def _drop_refined_state_chains(audit, chapters):
    """Ignore an event-level chain already represented by one chapter net edge."""
    reports = {}
    for event in audit:
        reports.setdefault(event["position"], []).append(event)
    for chapter in chapters:
        events = reports.get(int(chapter["position"])) or []
        for existing in chapter.get("state_transitions") or []:
            candidates = [
                (event, item)
                for event in events
                for item in event["missing_effects"]["state_transitions"]
                if item.get("subject_id") == existing.get("subject_id")
                and item.get("field") == existing.get("field")
            ]
            current = existing.get("from_value")
            for _event, item in candidates:
                if item.get("from_value") != current:
                    break
                current = item.get("to_value")
            else:
                if candidates and current == existing.get("to_value"):
                    for event, item in candidates:
                        event["missing_effects"]["state_transitions"].remove(item)


def _state_transition_key(value: dict) -> tuple:
    def frozen(item):
        return json.dumps(
            item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    return (
        value.get("subject_id"),
        value.get("field"),
        frozen(value.get("from_value")),
        frozen(value.get("to_value")),
    )


def _new_knowledge_grants(
    grants, event, known_before, knowledge_sources, audit_by_event
):
    kept = []
    position, event_id = event["position"], event["event_id"]
    event_order = event["event_order"]
    for grant in grants:
        key = (grant["character_id"], grant["fact_id"])
        proposed = (position, event_order)
        existing = knowledge_sources.get(key)
        if key in known_before or (existing and existing[:2] <= proposed):
            continue
        if existing:
            target = audit_by_event[(existing[0], existing[2]["source_event_id"])]
            unsupported = target["unsupported_effects"]["knowledge_grants"]
            if existing[2] not in unsupported:
                unsupported.append(existing[2])
        kept.append(grant)
        knowledge_sources[key] = (position, event_order, grant)
    return kept


def _known_facts(subjects):
    return {
        (character_id, fact_id)
        for character_id, state in subjects.items()
        for fact_id in state.get("knowledge") or []
    }


def _knowledge_sources(chapters):
    sources = {}
    for chapter in chapters:
        position = int(chapter["position"])
        order = {
            event_id: index
            for index, event_id in enumerate(chapter.get("required_event_ids") or [])
        }
        for grant in chapter.get("knowledge_grants") or []:
            sources[(grant["character_id"], grant["fact_id"])] = (
                position,
                order[grant["source_event_id"]],
                grant,
            )
    return sources
