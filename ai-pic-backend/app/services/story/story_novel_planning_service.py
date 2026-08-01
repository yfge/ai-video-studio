"""Outline-driven chapter planning for prose novel revisions."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException

from .story_novel_incremental_planning import prepare_incremental_plan
from .story_novel_plan_checkpoint import (
    begin_planning,
    frozen_generation_spec,
    reusable_generation_plan,
)
from .story_novel_plan_versions import is_v3_plan, is_v4_plan
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
        "characters": snapshot.get("characters") or [],
        "character_relationships": snapshot.get("character_relationships"),
        "world_building": snapshot.get("world_building"),
        "setting_time": snapshot.get("setting_time"),
        "setting_location": snapshot.get("setting_location"),
    }


def canon_planning_contract(snapshot: dict) -> dict:
    """Keep long-form Canon input bounded while retaining planned world growth."""
    contract = planning_contract(snapshot)
    seed = dict(contract.get("story_seed") or {})
    outline = dict(seed.get("structured_outline") or {})
    if int(outline.get("planning_structure_version") or 0) == 1:
        seed["structured_outline"] = {
            key: outline.get(key)
            for key in (
                "status",
                "version",
                "requested_chapter_count",
                "planning_model",
                "planning_structure_version",
                "core_character_routes",
                "scope_taxonomy",
                "initial_scope_nodes",
                "initial_scope_edges",
                "progression_arcs",
            )
        }
    return {**contract, "story_seed": seed}


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
    if (
        current.get("status") == "ready"
        and current.get("phase") == "ready"
        and any(str(row.content_text or "").strip() for row in revision.chapters or [])
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "当前 ready 计划的 hash 或门禁版本异常；已有正文未改写，"
                "请创建新小说版本后显式重新规划"
            ),
        )
    resumed = begin_planning(service, revision, task, current, frozen_spec)
    snapshot = revision.story_snapshot or {}
    expected_positions = explicit_outline_positions(snapshot)
    contract = planning_contract(snapshot)
    canon, timeline_filter = await compile_canon(
        service,
        revision,
        task,
        generate_text,
        canon_planning_contract(snapshot),
        current.get("canon") if resumed else None,
    )
    checkpoint_canon(service, revision, task, canon, timeline_filter)
    if frozen_spec is not None and (is_v3_plan(frozen_spec) or is_v4_plan(frozen_spec)):
        return await prepare_incremental_plan(
            service, revision, task, generate_text, frozen_spec, canon
        )
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
