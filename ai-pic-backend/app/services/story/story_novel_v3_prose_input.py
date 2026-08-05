"""Build the future-isolated prose payload for one v3 chapter."""

from .story_novel_prose_context import (
    current_chapter_prose_context,
    prose_visible_canon,
)


def build_v3_prose_input(context: dict, brief: dict, chapter_plan: dict) -> dict:
    brief_input = context["brief_input"]
    snapshot = (brief_input.get("hard_constraints") or {}).get("story_invariants", {})
    boundary_version = int(brief_input.get("prose_execution_boundary_version") or 0)
    result = {
        "chapter_brief": brief,
        "current_chapter_context": current_chapter_prose_context(
            context,
            brief,
            chapter_plan,
            boundary_version=boundary_version,
        ),
        "visible_canon": prose_visible_canon(context["hard_constraints"]),
        "chapter_length": {
            key: int(chapter_plan[key])
            for key in ("min_chars", "target_chars", "max_chars")
        },
        "writing_style": {
            key: snapshot.get(key)
            for key in ("genre", "target_audience", "story_format")
        },
        "prompt_evidence": {
            "raw_world_event_count": 0,
            "raw_character_memory_count": 0,
            "future_chapter_count": 0,
        },
    }
    return result
