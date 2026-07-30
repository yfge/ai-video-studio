"""Build the non-truncatable state contract for one novel chapter."""

from __future__ import annotations

import json
from typing import Any

from .story_novel_canon_service import content_hash
from .story_novel_constraint_visibility import visible_content_constraints
from .story_novel_state_visibility import (
    milestone_effect_refs,
    state_entity_refs,
    visible_state_fields,
    visible_subject,
)
from .story_novel_timeline_contract import (
    prompt_visible_chapter_contract,
    visible_timeline_refs,
)
from .story_novel_world_expansion import (
    canon_with_plan_expansion,
    state_with_pending_expansion,
)

SAFE_ENTITY_ATTRIBUTES = set("age occupation type gender pronouns family_role".split())


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
    effective_canon = canon_with_plan_expansion(canon, [chapter_plan], state_before)
    prompt_state = state_with_pending_expansion(
        state_before, chapter_plan.get("entity_introductions") or []
    )
    visible_plan = prompt_visible_chapter_contract(effective_canon, chapter_plan)
    current_refs = _visible_refs(effective_canon, [chapter_plan])
    revealed_refs = {
        ref for chapter in chapter_history for ref in _chapter_refs(chapter) if ref
    }
    refs = visible_timeline_refs(
        effective_canon,
        milestone_effect_refs(
            effective_canon,
            state_entity_refs(
                effective_canon,
                current_refs,
                prompt_state,
                revealed_refs=revealed_refs | current_refs,
            ),
            prompt_state,
        ),
        position,
    )
    relevant = _relevant_canon(effective_canon, visible_plan, [chapter_plan], refs)
    visible_state = _visible_state(prompt_state, effective_canon, [chapter_plan], refs)
    return {
        "story_invariants": _story_invariants(snapshot, effective_canon, refs),
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
    focus = {
        str(value).strip()
        for chapter in chapters
        for value in chapter.get("character_focus") or []
        if str(value).strip()
    }
    for item in canon.get("entities") or []:
        names = [item.get("name"), *(item.get("aliases") or [])]
        if any(
            name
            and (
                str(name) in surface
                or (
                    item.get("kind") == "character"
                    and any(value in str(name) or str(name) in value for value in focus)
                )
            )
            for name in names
        ):
            refs.add(str(item["id"]))
    return refs


def _visible_state(
    state_before: dict, canon: dict, chapters: list[dict], refs: set[str]
) -> dict:
    allowed = visible_state_fields(canon, chapters, refs)
    return {
        **{
            key: value
            for key, value in state_before.items()
            if key not in {"subjects", "revision_local_entities"}
        },
        "subjects": {
            subject_id: visible_subject(value, allowed.get(subject_id, set()), refs)
            for subject_id, value in (state_before.get("subjects") or {}).items()
            if subject_id in refs
        },
    }


def _chapter_refs(chapter: dict) -> set[str]:
    refs = set(chapter.get("canon_refs") or [])
    refs.update(
        item.get("id")
        for item in chapter.get("entity_introductions") or []
        if item.get("id")
    )
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
        if item.get("name"):
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
    allowed = visible_state_fields(canon, chapters, refs)
    return {
        subject_id: visible_subject(value, allowed.get(subject_id, set()), refs)
        for subject_id, value in (canon.get("initial_state") or {}).items()
        if subject_id in refs
    }


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
