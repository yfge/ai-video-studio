"""Build the non-truncatable state contract for one novel chapter."""

from __future__ import annotations

import json
from typing import Any

from .story_novel_canon_service import content_hash
from .story_novel_constraint_visibility import visible_content_constraints
from .story_novel_timeline_contract import (
    prompt_visible_chapter_contract,
    visible_timeline_refs,
)

SAFE_ENTITY_ATTRIBUTES = {"age", "occupation", "type"}


def build_hard_constraints(
    *,
    snapshot: dict,
    canon: dict,
    chapter_plan: dict,
    chapter_history: list[dict],
    approved_story_canon: dict,
    state_before: dict,
) -> dict:
    position = int(chapter_plan["position"])
    visible_plan = prompt_visible_chapter_contract(canon, chapter_plan)
    refs = visible_timeline_refs(canon, _visible_refs(canon, chapter_history), position)
    relevant = _relevant_canon(canon, visible_plan, chapter_history, refs)
    visible_state = _visible_state(state_before, canon, chapter_history, refs)
    return {
        "story_invariants": _story_invariants(snapshot, canon, refs),
        "chapter_contract": visible_plan,
        "compiled_canon": relevant,
        "approved_story_canon": approved_story_canon,
        "current_state": visible_state,
        "must_not_repeat": {
            "event_ids": state_before.get("occurred_event_ids") or [],
            "milestone_ids": state_before.get("completed_milestone_ids") or [],
        },
        "knowledge_boundaries": {
            subject_id: value.get("knowledge") or []
            for subject_id, value in (visible_state.get("subjects") or {}).items()
            if isinstance(value, dict)
        },
        "payoffs_due": visible_plan.get("payoffs_due") or [],
    }


def _relevant_canon(
    canon: dict, chapter_plan: dict, chapters: list[dict], refs: set[str]
) -> dict:
    return {
        "timeline": _matching(canon.get("timeline"), refs),
        "entities": _visible_entities(canon.get("entities"), refs, chapters),
        "world_rules": list(canon.get("world_rules") or []),
        "milestones": _matching(
            canon.get("milestones"),
            set(chapter_plan.get("milestones_consumed") or []),
        ),
        "character_arcs_to_current_chapter": _visible_character_arcs(
            canon.get("character_arcs"),
            refs,
            int(chapter_plan["position"]),
        ),
        "initial_state": _explicit_initial_state(canon, chapters, refs),
        "canon_hash": canon.get("canon_hash"),
    }


def _story_invariants(snapshot: dict, canon: dict, refs: set[str]) -> dict:
    """Only static metadata is safe without chapter visibility IDs."""
    constraints, excluded = visible_content_constraints(snapshot, canon, refs)
    return {
        "title": snapshot.get("title"),
        "genre": snapshot.get("genre"),
        "target_audience": snapshot.get("target_audience"),
        "story_format": snapshot.get("story_format"),
        "story_seed": {
            "content_constraints": constraints,
            "constraint_scope": "current_visible_only",
            "future_constraint_count_excluded": excluded,
        },
    }


def hard_constraints_hash(value: dict[str, Any]) -> str:
    return content_hash(value)


def _visible_refs(canon: dict, chapters: list[dict]) -> set[str]:
    refs = {ref for chapter in chapters for ref in _chapter_refs(chapter) if ref}
    surface = json.dumps(chapters, ensure_ascii=False, default=str)
    for item in canon.get("entities") or []:
        names = [item.get("name"), *(item.get("aliases") or [])]
        if any(str(name) in surface for name in names if name):
            refs.add(str(item["id"]))
    return refs


def _visible_state(
    state_before: dict, canon: dict, chapters: list[dict], refs: set[str]
) -> dict:
    allowed = _visible_state_fields(chapters, refs)
    return {
        **state_before,
        "subjects": {
            subject_id: {
                key: value
                for key, value in value.items()
                if key in allowed.get(subject_id, set())
            }
            for subject_id, value in (state_before.get("subjects") or {}).items()
            if subject_id in refs
        },
    }


def _chapter_refs(chapter: dict) -> set[str]:
    refs = set(chapter.get("canon_refs") or [])
    for field in ("preconditions", "state_transitions", "location_transitions"):
        refs.update(
            item.get("subject_id")
            for item in chapter.get(field) or []
            if item.get("subject_id")
        )
    refs.update(
        item.get("character_id")
        for item in chapter.get("knowledge_grants") or []
        if item.get("character_id")
    )
    for movement in chapter.get("location_transitions") or []:
        refs.update([movement.get("from_location_id"), movement.get("to_location_id")])
    refs.update(chapter.get("milestones_consumed") or [])
    return refs


def _matching(items, refs: set[str]) -> list[dict]:
    return [item for item in items or [] if item.get("id") in refs]


def _visible_entities(items, refs: set[str], chapters: list[dict]) -> list[dict]:
    surface = json.dumps(chapters, ensure_ascii=False, default=str)
    result = []
    for item in items or []:
        if item.get("id") not in refs:
            continue
        projected = {"id": item["id"], "kind": item["kind"]}
        if item.get("name") and (
            item.get("kind") == "location" or str(item["name"]) in surface
        ):
            projected["name"] = item["name"]
        aliases = [
            alias for alias in item.get("aliases") or [] if str(alias) in surface
        ]
        if aliases:
            projected["aliases"] = aliases
        attributes = {
            key: value
            for key, value in (item.get("attributes") or {}).items()
            if key in SAFE_ENTITY_ATTRIBUTES
        }
        if attributes:
            projected["attributes"] = attributes
        result.append(projected)
    return result


def _explicit_initial_state(canon: dict, chapters: list[dict], refs: set[str]) -> dict:
    allowed = _visible_state_fields(chapters, refs)
    return {
        subject_id: {
            key: field_value
            for key, field_value in value.items()
            if key in allowed.get(subject_id, set())
        }
        for subject_id, value in (canon.get("initial_state") or {}).items()
        if subject_id in refs
    }


def _visible_state_fields(
    chapters: list[dict], visible_refs: set[str]
) -> dict[str, set[str]]:
    fields: dict[str, set[str]] = {}
    for subject_id in visible_refs:
        fields.setdefault(subject_id, set()).add("location")
    for chapter in chapters:
        for item in chapter.get("preconditions") or []:
            fields.setdefault(item["subject_id"], set()).add(
                str(item["field"]).split(".", 1)[0]
            )
        for item in chapter.get("state_transitions") or []:
            fields.setdefault(item["subject_id"], set()).add(
                str(item["field"]).split(".", 1)[0]
            )
        for item in chapter.get("location_transitions") or []:
            fields.setdefault(item["subject_id"], set()).add("location")
        for item in chapter.get("knowledge_grants") or []:
            fields.setdefault(item["character_id"], set()).add("knowledge")
    return fields


def _visible_character_arcs(items, refs: set[str], position: int) -> list[dict]:
    return [
        {
            "character_id": item["character_id"],
            "checkpoints": [
                checkpoint
                for checkpoint in item.get("checkpoints") or []
                if int(checkpoint["position"]) <= position
            ],
        }
        for item in items or []
        if item.get("character_id") in refs
    ]
