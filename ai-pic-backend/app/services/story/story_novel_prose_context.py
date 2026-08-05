"""Compile current-chapter people and events for the prose model."""

from __future__ import annotations

import copy

_PROSE_EXECUTION_FIELDS = {"action_phase", "time_scope", "effort", "actor_ids"}
PROSE_EXECUTION_BOUNDARY_VERSION = 1
_ACTION_PHASE_SEMANTICS = {
    "instant": "本章发生该瞬时事件，不扩写后续结果",
    "start": "本章只启动行动，不得写成完成、到达或取得最终结果",
    "progress": "本章只推进过程，不得写成完成或取得最终结果",
    "complete": "本章完整完成事件，但不得追加合同外后果",
}


def prose_visible_canon(hard: dict) -> dict:
    """Project hard constraints to current, prose-useful facts without gate answers."""
    canon = hard.get("compiled_canon") or {}
    subjects = (hard.get("current_state") or {}).get("subjects") or {}
    return {
        "story_invariants": copy.deepcopy(hard.get("story_invariants") or {}),
        "compiled_canon": {
            "entities": copy.deepcopy(canon.get("entities") or []),
            "world_rules": copy.deepcopy(canon.get("world_rules") or []),
        },
        "current_state": {
            "subjects": {
                subject_id: _prose_subject(value)
                for subject_id, value in subjects.items()
                if isinstance(value, dict)
            }
        },
    }


def current_chapter_prose_context(
    context: dict,
    brief: dict,
    chapter_plan: dict,
    *,
    boundary_version: int = 0,
) -> dict:
    hard = context.get("hard_constraints") or {}
    canon = hard.get("compiled_canon") or {}
    current_state = hard.get("current_state") or {}
    executions = {
        item.get("event_id"): item
        for item in chapter_plan.get("execution_contracts") or []
        if isinstance(item, dict)
    }
    event_ids = list(chapter_plan.get("required_event_ids") or [])
    events = [
        {
            "event_id": event_id,
            "event": text,
            "execution": {
                key: copy.deepcopy(value)
                for key, value in (executions.get(event_id) or {}).items()
                if key in _PROSE_EXECUTION_FIELDS
            },
        }
        for event_id, text in zip(
            event_ids, chapter_plan.get("key_events") or [], strict=True
        )
    ]
    scene_participants = _scene_participants(
        canon, set(chapter_plan.get("character_focus") or [])
    )
    for item in events:
        item["scene_participants"] = [
            copy.deepcopy(participant)
            for participant in scene_participants
            if participant["label"] in item["event"]
        ]
    allowed = {
        value
        for beat in brief.get("beats") or []
        for value in beat.get("allowed_entity_ids") or []
    }
    allowed.update(
        value for item in executions.values() for value in item.get("actor_ids") or []
    )
    focus = set(chapter_plan.get("character_focus") or [])
    motivations = {
        item.get("character_id"): item.get("motivation")
        for item in brief.get("character_motivations") or []
        if isinstance(item, dict)
    }
    characters = []
    for entity in canon.get("entities") or []:
        if entity.get("kind") != "character":
            continue
        if entity.get("id") not in allowed and entity.get("name") not in focus:
            continue
        subject = (current_state.get("subjects") or {}).get(entity["id"]) or {}
        characters.append(
            {
                "id": entity["id"],
                "name": entity.get("name"),
                "aliases": list(entity.get("aliases") or []),
                "attributes": copy.deepcopy(entity.get("attributes") or {}),
                "current_state": _prose_subject(subject),
                "motivation": motivations.get(entity["id"]),
            }
        )
    result = {
        "events": events,
        "characters": characters,
        "scene_participants": scene_participants,
    }
    if boundary_version:
        result["typed_execution_boundary"] = _typed_execution_boundary(
            context, executions, boundary_version
        )
    return result


def _typed_execution_boundary(
    context: dict, executions: dict[str, dict], version: int
) -> dict:
    if version != PROSE_EXECUTION_BOUNDARY_VERSION:
        raise ValueError(f"不支持的正文执行边界版本: {version}")
    delta = (context.get("brief_input") or {}).get("expected_delta") or {}
    locations = copy.deepcopy(delta.get("location_transitions") or [])
    actor_ids = {
        str(value)
        for item in executions.values()
        for value in item.get("actor_ids") or []
        if str(value or "").strip()
    }
    moved = {str(item.get("subject_id")) for item in locations}
    return {
        "schema": "story_novel_prose_execution_boundary.v1",
        "effects_are_exhaustive": True,
        "free_text_conflict_rule": "typed_effects_and_action_phase_win",
        "action_phase_semantics": copy.deepcopy(_ACTION_PHASE_SEMANTICS),
        "state_transitions": copy.deepcopy(delta.get("state_transitions") or []),
        "entity_introductions": copy.deepcopy(delta.get("entity_introductions") or []),
        "location_transitions": locations,
        "knowledge_grants": copy.deepcopy(delta.get("knowledge_grants") or []),
        "milestones_consumed": list(delta.get("milestones_consumed") or []),
        "opened_thread_ids": list(delta.get("opened_thread_ids") or []),
        "resolved_thread_ids": list(delta.get("resolved_thread_ids") or []),
        "unchanged_location_subject_ids": sorted(actor_ids - moved),
    }


def _scene_participants(canon: dict, focus: set[str]) -> list[dict]:
    """Keep outline-authorized generic actors without inventing Canon state."""
    known = {
        str(value).strip()
        for entity in canon.get("entities") or []
        if entity.get("kind") == "character"
        for value in [
            entity.get("id"),
            entity.get("name"),
            *(entity.get("aliases") or []),
        ]
        if str(value or "").strip()
    }
    return [
        {
            "label": value,
            "scope": "current_chapter_only",
            "persistent_state": False,
        }
        for value in sorted(focus)
        if value and value not in known
    ]


def _prose_subject(value: dict) -> dict:
    return {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key not in {"knowledge"}
    }
