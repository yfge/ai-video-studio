"""One-shot repair prompt for executable long-form chapter contracts."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_initial_state import canonical_initial_subjects
from .story_novel_location_rules import (
    ABSENT_OBJECT_STATUS_LITERALS,
    TERMINAL_OBJECT_STATUS_LITERALS,
)
from .story_novel_plan_refs import known_canon_ids
from .story_novel_prompt_renderer import render_novel_prompt


def plan_repair_prompt(
    prompt: str,
    text: str,
    error: str | None,
    expected_positions: list[int],
    *,
    canon: dict | None = None,
    frozen_spec: dict | None = None,
    thread_payoffs: list[dict] | None = None,
) -> str:
    context = _repair_context(
        text, error, canon or {}, frozen_spec or {}, thread_payoffs
    )
    absence_literals = "、".join(
        f'"{value}"' for value in ABSENT_OBJECT_STATUS_LITERALS
    )
    terminal_literals = "、".join(
        f'"{value}"' for value in TERMINAL_OBJECT_STATUS_LITERALS
    )
    return render_novel_prompt(
        "story_novel_plan_full_repair_v3",
        original_prompt=prompt,
        previous_output=text,
        batch_start=expected_positions[0] if expected_positions else None,
        batch_end=expected_positions[-1] if expected_positions else None,
        absence_literals=absence_literals,
        terminal_literals=terminal_literals,
        repair_context_json=canonical_json(context),
        validation_error=error or "章节规划无效",
    )


def _repair_context(
    text: str,
    error: str | None,
    canon: dict,
    frozen_spec: dict,
    thread_payoffs: list[dict] | None,
) -> dict:
    payload = extract_json_block(text) or {}
    initial_state = canonical_initial_subjects(canon)
    object_ids = {
        item["id"]
        for item in canon.get("entities") or []
        if item.get("id") and item.get("kind") == "object"
    }
    unpositioned_once = {
        item["id"]
        for item in canon.get("milestones") or []
        if item.get("id")
        and not item.get("repeatable")
        and "planned_position" in item
        and item.get("planned_position") is None
    }
    source = list(frozen_spec.get("chapters") or payload.get("chapters") or [])
    consumed_ids = {
        milestone_id
        for item in payload.get("chapters") or []
        for milestone_id in item.get("milestones_consumed") or []
    }
    failing = [
        item
        for item in canon.get("milestones") or []
        if item.get("id")
        and str(item["id"]) in str(error or "")
        and (
            item.get("repeatable")
            or item.get("planned_position") is not None
            or "planned_position" not in item
        )
    ]
    openings = [
        {
            "position": int(item["position"]),
            "thread_ids": list(item.get("open_threads") or []),
        }
        for item in source
    ]
    capacity = [
        {
            "position": int(item["position"]),
            "max_payoffs": 3,
            "key_events": list(item.get("key_events") or []),
        }
        for item in source
    ]
    terminal = capacity[-1] if capacity else None
    return {
        "failing_milestones": failing,
        "consumed_milestone_contracts": [
            item
            for item in canon.get("milestones") or []
            if item.get("id") in consumed_ids
            and (
                item.get("repeatable")
                or item.get("planned_position") is not None
                or "planned_position" not in item
            )
        ],
        "milestone_outcome_contracts": [
            {
                "id": item["id"],
                "planned_position": item.get("planned_position"),
                "outcomes": item.get("outcomes") or [],
            }
            for item in canon.get("milestones") or []
            if item.get("id")
            and not item.get("repeatable")
            and (
                item.get("planned_position") is not None
                or "planned_position" not in item
            )
        ],
        "valid_canon_ids": sorted(known_canon_ids(canon) - unpositioned_once),
        "timeline_contracts": [
            {
                "position": int(item.get("source_chapter_position") or 0),
                "timeline_id": item["id"],
                "source_key_event": item.get("source_key_event"),
            }
            for item in canon.get("timeline") or []
            if item.get("immutable") and item.get("id")
        ],
        "authoritative_initial_state": initial_state,
        "object_location_contract": {
            "absence_status_literals": list(ABSENT_OBJECT_STATUS_LITERALS),
        },
        "state_value_contract": {
            "undefined_field_from_value": None,
            "defined_empty_array_from_value": [],
            "copy_authoritative_values_without_coercion": True,
        },
        "derived_state_contract": {
            "possessions": "derived_from_object_owner_id_never_transition_directly"
        },
        "unlocated_object_initial_states": [
            {
                "subject_id": subject_id,
                "status": initial_state[subject_id].get("status"),
                "status_is_defined": "status" in initial_state[subject_id],
                "owner_id": initial_state[subject_id].get("owner_id"),
                "owner_id_is_defined": "owner_id" in initial_state[subject_id],
                "location": initial_state[subject_id].get("location"),
                "location_is_defined": "location" in initial_state[subject_id],
            }
            for subject_id in sorted(object_ids)
            if subject_id in initial_state
            and initial_state[subject_id].get("location") is None
        ],
        "authoritative_key_events": [
            {
                "position": int(item["position"]),
                "key_events": list(item.get("key_events") or []),
            }
            for item in source
        ],
        "authoritative_thread_payoffs": thread_payoffs,
        "thread_openings": openings,
        "thread_count": sum(len(item["thread_ids"]) for item in openings),
        "payoff_capacity": capacity,
        "terminal_payoff_capacity": terminal,
    }
