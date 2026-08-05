"""Compact current truth and future state boundaries for the v3 auditor."""

from __future__ import annotations

import copy

from .story_novel_hard_context import SAFE_ENTITY_ATTRIBUTES


def current_state_contract(
    canon: dict,
    chapter_plan: dict,
    expected_delta: dict,
    state_before: dict,
    content_text: str = "",
) -> dict:
    """Expose current values only for subjects relevant to this chapter."""
    entities = _entities(canon)
    relevant = _relevant_subject_ids(chapter_plan, expected_delta)
    relevant.update(_mentioned_entity_ids(entities, content_text))
    subjects = state_before.get("subjects") or {}
    return {
        "state_before_hash": expected_delta.get("state_before_hash"),
        "subjects": [
            {
                **_entity_label(subject_id, entities),
                "state": copy.deepcopy(subjects.get(subject_id) or {}),
            }
            for subject_id in sorted(relevant)
            if subject_id in entities
        ],
        "open_thread_ids": sorted(
            thread_id
            for thread_id, status in (state_before.get("threads") or {}).items()
            if status == "open"
        ),
    }


def future_state_boundaries(
    plan: dict,
    chapter_plan: dict,
    expected_delta: dict,
    state_before: dict,
) -> list[dict]:
    """Return audit-only semantic boundaries without future titles or goals."""
    position = int(chapter_plan["position"])
    entities = _entities(plan.get("canon") or {})
    relevant = _relevant_subject_ids(chapter_plan, expected_delta)
    open_threads = {
        thread_id
        for thread_id, status in (state_before.get("threads") or {}).items()
        if status == "open"
    }
    rows = []
    for chapter in sorted(
        plan.get("chapters") or [], key=lambda item: int(item["position"])
    ):
        allowed = int(chapter["position"])
        if allowed <= position:
            continue
        for index, item in enumerate(chapter.get("state_transitions") or [], 1):
            if item.get("subject_id") in relevant:
                rows.append(_state_boundary(item, entities, allowed, index))
        for index, item in enumerate(chapter.get("location_transitions") or [], 1):
            if item.get("subject_id") in relevant:
                rows.append(_location_boundary(item, entities, allowed, index))
        for index, item in enumerate(chapter.get("knowledge_grants") or [], 1):
            if item.get("character_id") in relevant:
                rows.append(_knowledge_boundary(item, entities, allowed, index))
        for thread_id in chapter.get("payoffs_due") or []:
            if thread_id in open_threads:
                rows.append(
                    {
                        "boundary_id": f"thread:{allowed}:{thread_id}",
                        "kind": "thread_payoff",
                        "first_allowed_position": allowed,
                        "thread_id": thread_id,
                    }
                )
    return rows


def current_timeline_context(canon: dict, chapter_plan: dict) -> list[dict]:
    """Keep timing available for semantic review without creating proofs."""
    timeline = {item["id"]: item for item in canon.get("timeline") or []}
    return [
        {
            "timeline_id": timeline_id,
            "event_id": event_id,
            "story_time": (timeline.get(timeline_id) or {}).get("story_time"),
            "label": (timeline.get(timeline_id) or {}).get("label"),
        }
        for timeline_id, event_id in (
            chapter_plan.get("timeline_event_bindings") or {}
        ).items()
        if timeline_id in timeline
    ]


def _relevant_subject_ids(chapter_plan: dict, expected_delta: dict) -> set[str]:
    result = set(chapter_plan.get("canon_refs") or [])
    for item in chapter_plan.get("execution_contracts") or []:
        result.update(item.get("actor_ids") or [])
    for field in ("state_transitions", "location_transitions"):
        result.update(
            str(item["subject_id"])
            for item in expected_delta.get(field) or []
            if item.get("subject_id")
        )
    result.update(
        str(item["character_id"])
        for item in expected_delta.get("knowledge_grants") or []
        if item.get("character_id")
    )
    return result


def _state_boundary(item, entities, allowed, index):
    return {
        "boundary_id": f"state:{allowed}:{index}",
        "kind": "state_transition",
        "first_allowed_position": allowed,
        **_entity_label(item["subject_id"], entities),
        "field": item["field"],
        "from_value": copy.deepcopy(item.get("from_value")),
        "to_value": copy.deepcopy(item.get("to_value")),
    }


def _location_boundary(item, entities, allowed, index):
    return {
        "boundary_id": f"location:{allowed}:{index}",
        "kind": "location_transition",
        "first_allowed_position": allowed,
        **_entity_label(item["subject_id"], entities),
        "from_location": _entity_label(item.get("from_location_id"), entities),
        "to_location": _entity_label(item.get("to_location_id"), entities),
    }


def _knowledge_boundary(item, entities, allowed, index):
    return {
        "boundary_id": f"knowledge:{allowed}:{index}",
        "kind": "knowledge_grant",
        "first_allowed_position": allowed,
        **_entity_label(item["character_id"], entities),
        "fact_id": item["fact_id"],
        "source_event_id": item["source_event_id"],
    }


def _entities(canon: dict) -> dict[str, dict]:
    return {str(item["id"]): item for item in canon.get("entities") or []}


def _entity_label(entity_id, entities) -> dict:
    entity = entities.get(str(entity_id)) or {}
    result = {
        "subject_id": entity_id,
        "name": entity.get("name"),
        "aliases": list(entity.get("aliases") or []),
        "entity_kind": entity.get("kind"),
    }
    attributes = {
        key: copy.deepcopy(value)
        for key, value in (entity.get("attributes") or {}).items()
        if key in SAFE_ENTITY_ATTRIBUTES
    }
    if attributes:
        result["immutable_attributes"] = attributes
    return result


def _mentioned_entity_ids(entities: dict[str, dict], content_text: str) -> set[str]:
    if not content_text:
        return set()
    return {
        entity_id
        for entity_id, entity in entities.items()
        if any(
            str(name) in content_text
            for name in [entity.get("name"), *(entity.get("aliases") or [])]
            if str(name or "").strip()
        )
    }
