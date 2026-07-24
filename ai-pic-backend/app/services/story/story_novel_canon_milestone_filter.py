"""Drop model milestone outcomes already established by earlier source chapters."""

from __future__ import annotations

import re

from .story_novel_location_rules import TERMINAL_OBJECT_STATUS_LITERALS

CANON_MODEL_FILTER_VERSION = 3


def filter_model_milestone_outcomes(
    payload: dict, planning_contract: dict
) -> tuple[dict, list[dict]]:
    seed = planning_contract.get("story_seed") or {}
    chapters = (seed.get("structured_outline") or {}).get("chapters") or []
    entities = {item.get("id"): item for item in payload.get("entities") or []}
    if not chapters or not entities:
        return payload, []
    diagnostics: list[dict] = []
    milestones = []
    for raw in payload.get("milestones") or []:
        item = dict(raw)
        kept = []
        for outcome in item.get("outcomes") or []:
            diagnostic = _location_outcome_diagnostic(outcome, item, entities, chapters)
            if diagnostic is None:
                kept.append(outcome)
                continue
            diagnostics.append(
                {
                    "id": str(item.get("id") or "<missing-id>"),
                    "section": "milestone",
                    **diagnostic,
                    "subject_id": str(outcome.get("subject_id") or ""),
                    "location_id": str(outcome.get("value") or ""),
                }
            )
        item["outcomes"] = kept
        for subject_id in _complete_terminal_owner_clear(item, entities):
            diagnostics.append(
                {
                    "id": str(item.get("id") or "<missing-id>"),
                    "section": "milestone",
                    "reason": "terminal_owner_clear_completed",
                    "subject_id": subject_id,
                }
            )
        if kept:
            milestones.append(item)
        else:
            diagnostics.append(
                {
                    "id": str(item.get("id") or "<missing-id>"),
                    "section": "milestone",
                    "reason": "empty_after_location_filter",
                }
            )
    return {**payload, "milestones": milestones}, diagnostics


def _complete_terminal_owner_clear(item: dict, entities: dict[str, dict]) -> list[str]:
    if item.get("repeatable") is not False or item.get("planned_position") is None:
        return []
    outcomes = item["outcomes"]
    owner_subjects = {
        outcome.get("subject_id")
        for outcome in outcomes
        if outcome.get("field") == "owner_id"
    }
    terminal_statuses = set(TERMINAL_OBJECT_STATUS_LITERALS)
    terminal_subjects = {
        outcome.get("subject_id")
        for outcome in outcomes
        if outcome.get("field") == "status"
        and outcome.get("operator") == "eq"
        and str(outcome.get("value") or "").strip().lower() in terminal_statuses
        and (entities.get(outcome.get("subject_id")) or {}).get("kind") == "object"
    }
    completed = sorted(terminal_subjects - owner_subjects)
    outcomes.extend(
        {
            "subject_id": subject_id,
            "field": "owner_id",
            "operator": "eq",
            "value": None,
        }
        for subject_id in completed
    )
    return completed


def _location_outcome_diagnostic(outcome, milestone, entities, chapters):
    subject = entities.get(outcome.get("subject_id")) or {}
    location = entities.get(outcome.get("value")) or {}
    if (
        outcome.get("field") != "location"
        or outcome.get("operator") != "eq"
        or subject.get("kind") != "object"
        or location.get("kind") != "location"
    ):
        return None
    planned = int(milestone.get("planned_position") or 0)
    subject_terms = _entity_terms(subject)
    location_terms = _entity_terms(location)
    sourced_at_milestone = False
    earlier_source = None
    for chapter in chapters:
        position = int(chapter.get("position") or 0)
        if not position or position > planned:
            continue
        text = _normalized_text(
            " ".join(
                [
                    str(chapter.get("title") or ""),
                    str(chapter.get("goal") or ""),
                    *[str(value) for value in chapter.get("key_events") or []],
                    str(chapter.get("end_state") or ""),
                ]
            )
        )
        if any(term in text for term in subject_terms) and any(
            term in text for term in location_terms
        ):
            if position == planned:
                sourced_at_milestone = True
            elif earlier_source is None:
                earlier_source = position
    if not sourced_at_milestone:
        return {
            "reason": "location_not_sourced_at_milestone",
            "planned_chapter_position": planned,
        }
    if earlier_source is not None:
        return {
            "reason": "location_already_sourced_earlier",
            "source_chapter_position": earlier_source,
        }
    return None


def _entity_terms(entity: dict) -> list[str]:
    return [
        normalized
        for value in [entity.get("name"), *(entity.get("aliases") or [])]
        if (normalized := _normalized_text(str(value)))
    ]


def _normalized_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value).lower()
