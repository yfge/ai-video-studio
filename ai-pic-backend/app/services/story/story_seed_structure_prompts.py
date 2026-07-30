"""Prompt rendering for bounded multi-arc StorySeed structuring."""

from typing import Any

from .story_novel_domain import json_prompt_payload
from .story_novel_prompt_renderer import render_novel_prompt


def structured_progression_prompt(
    *, story_seed: dict[str, Any], chapter_ranges: list[dict]
) -> str:
    return render_novel_prompt(
        "story_novel_structure_arcs_v3",
        story_seed_json=json_prompt_payload(story_seed),
        chapter_ranges_json=json_prompt_payload(chapter_ranges),
        requested_chapter_count=sum(
            int(item["end_position"]) - int(item["start_position"]) + 1
            for item in chapter_ranges
        ),
    )


def structured_arc_chapters_prompt(
    *,
    story_seed: dict[str, Any],
    progression_plan: dict[str, Any],
    arc: dict[str, Any],
    positions: list[int],
    is_final: bool,
) -> str:
    directives = [
        item
        for row in progression_plan.get("progression_arcs") or []
        for item in row.get("threads") or []
        if item.get("open_position") in positions
        or item.get("payoff_position") in positions
    ]
    return render_novel_prompt(
        "story_novel_structure_arc_chapters_v3",
        story_seed_json=json_prompt_payload(story_seed),
        current_arc_json=json_prompt_payload(arc),
        positions_json=json_prompt_payload(positions),
        thread_directives_json=json_prompt_payload(directives),
        ending_requirement=(
            "本批含终章，最后一章必须明确覆盖 ending_direction。"
            if is_final
            else "本批不含终章，不得提前完成 ending_direction。"
        ),
    )


def structured_arc_repair_prompt(
    original_prompt: str, previous_output: str, validation_error: str
) -> str:
    return render_novel_prompt(
        "story_novel_structure_arc_repair_v3",
        original_prompt=original_prompt,
        validation_error=validation_error,
        previous_output=previous_output[:24000],
    )
