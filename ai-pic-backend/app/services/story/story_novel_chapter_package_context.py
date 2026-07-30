"""Build a future-isolated input for one just-in-time chapter package."""

from __future__ import annotations

import copy

from .story_novel_context_utils import value_hash
from .story_novel_incremental_plan import chapter_skeleton
from .story_novel_v3_context import build_v3_planning_context

SCHEMA = "story_novel_chapter_package_input.v3"


def build_package_input(service, revision, position: int, skeleton: dict) -> dict:
    context = build_v3_planning_context(service, revision, position, skeleton)
    brief_input = context["brief_input"]
    hard = context["hard_constraints"]
    result = {
        "schema": SCHEMA,
        "position": position,
        "current_chapter_skeleton": chapter_skeleton(skeleton),
        "story_invariants": copy.deepcopy(hard.get("story_invariants") or {}),
        "novel_delivery": copy.deepcopy(
            ((getattr(revision, "generation_plan", None) or {}).get("length_profile"))
            or {}
        ),
        "current_progression_arc": _current_progression_arc(revision, position),
        "state_before": _planning_state(context, skeleton),
        "state_before_hash": brief_input["state_before_hash"],
        "current_visible_canon": hard.get("compiled_canon") or {},
        "approved_story_canon": hard.get("approved_story_canon") or {},
        "must_not_repeat": hard.get("must_not_repeat") or {},
        "prior_world_events": brief_input["planning_evidence"]["world_events"],
        "prior_character_memories": brief_input["planning_evidence"][
            "character_memories"
        ],
        "recent_chapters": brief_input.get("recent_chapters") or [],
        "previous_chapter_tail": brief_input.get("previous_chapter_tail") or "",
        "allowed_entity_ids": brief_input.get("allowed_entity_ids") or [],
        "expected_beat_count": brief_input["expected_beat_count"],
        "future_chapter_count_excluded": context["evidence"][
            "future_chapter_count_excluded"
        ],
    }
    result["package_input_hash"] = value_hash(result)
    return result


def _planning_state(context: dict, skeleton: dict) -> dict:
    """Keep complete past state for current refs without exposing unrelated entities."""
    brief_input = context["brief_input"]
    source = context.get("state_before") or brief_input.get("state_before") or {}
    refs = set(skeleton.get("canon_refs") or [])
    refs.update(brief_input.get("allowed_entity_ids") or [])
    return {
        **{
            key: copy.deepcopy(value)
            for key, value in source.items()
            if key != "subjects"
        },
        "subjects": {
            key: copy.deepcopy(value)
            for key, value in (source.get("subjects") or {}).items()
            if key in refs
        },
    }


def _current_progression_arc(revision, position: int) -> dict:
    snapshot = getattr(revision, "story_snapshot", None) or {}
    outline = (snapshot.get("story_seed") or {}).get("structured_outline") or {}
    if int(outline.get("planning_structure_version") or 0) != 1:
        return {}
    arc = next(
        (
            item
            for item in outline.get("progression_arcs") or []
            if int(item.get("start_position") or 0)
            <= position
            <= int(item.get("end_position") or 0)
        ),
        None,
    )
    if not arc:
        return {}
    return {
        key: copy.deepcopy(arc.get(key))
        for key in (
            "arc_id",
            "title",
            "start_position",
            "end_position",
            "narrative_goal",
            "growth",
        )
    }
