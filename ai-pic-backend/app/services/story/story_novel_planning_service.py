"""Outline-driven chapter planning for prose novel revisions."""

from __future__ import annotations

from typing import Awaitable, Callable

from .story_novel_plan_checkpoint import (
    begin_planning,
    frozen_generation_spec,
    reusable_generation_plan,
)
from .story_novel_planning_phases import (
    checkpoint_canon,
    compile_canon,
    complete_plan,
    plan_chapters,
)
from .story_outline_positions import explicit_outline_positions

GenerateText = Callable[..., Awaitable[str]]


def planning_contract(snapshot: dict) -> dict:
    """Expose only the frozen seed, characters, and world constraints."""
    seed = dict(snapshot.get("story_seed") or {})
    if seed.get("schema") == "story_seed_v2" and seed.get("structured_outline"):
        seed.pop("outline", None)
        seed.pop("outline_text", None)
    return {
        "story_seed": seed,
        "main_characters": snapshot.get("main_characters"),
        "character_relationships": snapshot.get("character_relationships"),
        "world_building": snapshot.get("world_building"),
        "setting_time": snapshot.get("setting_time"),
        "setting_location": snapshot.get("setting_location"),
    }


async def ensure_generation_plan(
    service,
    revision,
    task,
    generate_text: GenerateText,
) -> dict:
    current = dict(revision.generation_plan or {})
    frozen_spec = frozen_generation_spec(current)
    if reusable_generation_plan(current, frozen_spec):
        return current
    resumed = begin_planning(service, revision, task, current, frozen_spec)
    snapshot = revision.story_snapshot or {}
    expected_positions = explicit_outline_positions(snapshot)
    contract = planning_contract(snapshot)
    canon, timeline_filter = await compile_canon(
        service,
        revision,
        task,
        generate_text,
        contract,
        current.get("canon") if resumed else None,
    )
    checkpoint_canon(service, revision, task, canon, timeline_filter)
    chapters = await plan_chapters(
        service,
        revision,
        task,
        generate_text,
        contract,
        canon,
        expected_positions,
        frozen_spec,
    )
    return complete_plan(service, revision, task, frozen_spec, canon, chapters)
