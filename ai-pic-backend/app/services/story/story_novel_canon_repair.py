"""Bounded provider repair prompt for an invalid compiled Canon."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_contains_outcome import merge_contains_outcome
from .story_novel_initial_state import (
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_prompt_renderer import render_novel_prompt


def canon_repair_prompt(prompt: str, text: str, error: str | None) -> str:
    payload = extract_json_block(text) or {}
    error_text = str(error or "")
    milestones = payload.get("milestones") or []
    invalid_contains_ids = _invalid_contains_milestone_ids(payload)
    failing = [
        item
        for item in milestones
        if item.get("id")
        and (str(item["id"]) in error_text or str(item["id"]) in invalid_contains_ids)
    ]
    initial_state_error = any(
        marker in error_text for marker in ("初始状态", "状态提前")
    )
    preserve_initial = None if initial_state_error else payload.get("initial_state")
    repair_context = {
        "failing_milestones": failing,
        "invalid_contains_milestone_ids": invalid_contains_ids,
        "delete_milestone_ids": _milestones_empty_after_dedup(milestones, error_text),
        "preserve_initial_state_exactly": preserve_initial,
        "existing_milestone_ids": [item["id"] for item in milestones if item.get("id")],
    }
    previous_canon = canonical_json(payload) if payload else text
    return render_novel_prompt(
        "story_novel_canon_repair_v3",
        original_prompt=prompt,
        error=str(error or ""),
        repair_context_json=canonical_json(repair_context),
        previous_canon=previous_canon,
    )


def _invalid_contains_milestone_ids(payload: dict) -> list[str]:
    subjects = canonical_initial_subjects(payload)
    invalid: list[str] = []
    milestones = sorted(
        payload.get("milestones") or [],
        key=lambda item: int(item.get("planned_position") or 0),
    )
    for milestone in milestones:
        for outcome in milestone.get("outcomes") or []:
            subject_id, field = outcome.get("subject_id"), outcome.get("field")
            value = outcome.get("value")
            if outcome.get("operator") == "contains":
                try:
                    value = merge_contains_outcome(
                        _field_value(subjects.get(subject_id) or {}, field),
                        field,
                        value,
                    )
                except ValueError:
                    invalid.append(str(milestone.get("id") or ""))
                    continue
            apply_subject_transition(subjects, subject_id, field, value)
    return list(dict.fromkeys(value for value in invalid if value))


def _field_value(subject: dict, field: str):
    value = subject
    for part in str(field or "").split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _milestones_empty_after_dedup(milestones: list[dict], error_text: str) -> list[str]:
    seen: set[str] = set()
    delete_ids: list[str] = []
    ordered = sorted(
        enumerate(milestones),
        key=lambda item: (
            item[1].get("planned_position") is None,
            item[1].get("planned_position") or 0,
            item[0],
        ),
    )
    for _index, milestone in ordered:
        milestone_id = str(milestone.get("id") or "")
        outcomes = milestone.get("outcomes") or []
        signatures = [canonical_json(item) for item in outcomes]
        if milestone_id in error_text and (
            not signatures or all(signature in seen for signature in signatures)
        ):
            delete_ids.append(milestone_id)
        seen.update(signatures)
    return delete_ids
