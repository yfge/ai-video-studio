"""Frozen series/arc roadmap fields for generation-plan v4."""

from __future__ import annotations

import copy

from .story_novel_context_utils import value_hash
from .story_novel_plan_versions import V4_SCHEMA

ARC_SCHEMA = "story_novel_arc_plan.v1"
ROADMAP_SCHEMA = "story_novel_series_roadmap.v1"
SERIES_BIBLE_SCHEMA = "story_novel_series_bible.v1"


def v4_plan_fields(snapshot: dict, canon: dict, chapters: list[dict]) -> dict:
    outline = _structured_outline(snapshot)
    arcs = _arc_rows(outline, chapters)
    bible = _series_bible(snapshot, outline, canon, chapters, arcs)
    roadmap = _series_roadmap(outline, chapters, arcs)
    current = {}
    arc_plans = {}
    result = {
        "series_bible": bible,
        "series_bible_hash": value_hash(bible),
        "series_roadmap": roadmap,
        "series_roadmap_hash": value_hash(roadmap),
        "current_arc_plan": current,
        "current_arc_plan_hash": value_hash(current),
        "arc_plans": arc_plans,
        "arc_plans_hash": value_hash(arc_plans),
        "frozen_through_position": 0,
        "scope_graph": {
            "taxonomy": copy.deepcopy(outline.get("scope_taxonomy") or []),
            "nodes": copy.deepcopy(outline.get("initial_scope_nodes") or []),
            "edges": copy.deepcopy(outline.get("initial_scope_edges") or []),
        },
        "planner_snapshot_schema": "story_novel_planner_snapshot.v1",
        "chapter_intent_schema": "story_novel_chapter_intent.v1",
        "chapter_contract_schema": "story_novel_chapter_contract.v2",
        "audit_proof_schema": "story_novel_audit_proof.v2",
    }
    result["scope_graph_hash"] = value_hash(result["scope_graph"])
    return result


def valid_v4_plan_fields(plan: dict) -> bool:
    if plan.get("schema") != V4_SCHEMA:
        return True
    try:
        chapters = list(plan["chapters"])
        roadmap = dict(plan["series_roadmap"])
        positions = [int(item["position"]) for item in roadmap["chapters"]]
        arcs = list(roadmap["arcs"])
        covered = [
            position
            for arc in arcs
            for position in range(
                int(arc["start_position"]), int(arc["end_position"]) + 1
            )
        ]
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        positions == list(range(1, len(chapters) + 1))
        and covered == positions
        and plan.get("series_bible_hash") == value_hash(plan.get("series_bible"))
        and plan.get("series_roadmap_hash") == value_hash(roadmap)
        and plan.get("current_arc_plan_hash")
        == value_hash(plan.get("current_arc_plan"))
        and _current_arc_is_frozen(plan)
        and plan.get("arc_plans_hash") == value_hash(plan.get("arc_plans") or {})
        and plan.get("scope_graph_hash") == value_hash(plan.get("scope_graph"))
        and plan.get("planner_snapshot_schema") == "story_novel_planner_snapshot.v1"
        and plan.get("chapter_intent_schema") == "story_novel_chapter_intent.v1"
        and plan.get("chapter_contract_schema") == "story_novel_chapter_contract.v2"
        and plan.get("audit_proof_schema") == "story_novel_audit_proof.v2"
    )


def arc_for_position(plan: dict, position: int) -> dict:
    current = plan.get("current_arc_plan") or {}
    if (
        int(current.get("start_position") or 0)
        <= position
        <= int(current.get("end_position") or -1)
    ):
        return copy.deepcopy(current)
    return next(
        (
            copy.deepcopy(item)
            for item in (plan.get("series_roadmap") or {}).get("arcs") or []
            if int(item["start_position"]) <= position <= int(item["end_position"])
        ),
        {},
    )


def all_arc_plans_frozen(plan: dict) -> bool:
    expected = {
        item["arc_id"] for item in (plan.get("series_roadmap") or {}).get("arcs") or []
    }
    return bool(expected and set(plan.get("arc_plans") or {}) == expected)


def _current_arc_is_frozen(plan: dict) -> bool:
    current = plan.get("current_arc_plan") or {}
    if not current:
        return not (plan.get("arc_plans") or {})
    return (plan.get("arc_plans") or {}).get(current.get("arc_id")) == current


def _structured_outline(snapshot: dict) -> dict:
    return copy.deepcopy(
        ((snapshot.get("story_seed") or {}).get("structured_outline") or {})
    )


def _arc_rows(outline: dict, chapters: list[dict]) -> list[dict]:
    source = list(outline.get("progression_arcs") or [])
    if not source:
        source = [
            {
                "arc_id": "arc-1",
                "title": "全书",
                "start_position": 1,
                "end_position": len(chapters),
                "narrative_goal": "完成已确认大纲",
            }
        ]
    return [
        {
            "schema": ARC_SCHEMA,
            "arc_id": item["arc_id"],
            "title": item["title"],
            "start_position": int(item["start_position"]),
            "end_position": int(item["end_position"]),
            "narrative_goal": item.get("narrative_goal") or "推进当前阶段冲突",
            "growth": copy.deepcopy(item.get("growth") or {}),
            "threads": copy.deepcopy(item.get("threads") or []),
            "character_slots": copy.deepcopy(item.get("character_slots") or []),
            "scope_slots": copy.deepcopy(item.get("scope_slots") or []),
        }
        for item in source
    ]


def _series_bible(snapshot, outline, canon, chapters, arcs) -> dict:
    seed = snapshot.get("story_seed") or {}
    entities = list(canon.get("entities") or [])
    ending = seed.get("ending_direction") or snapshot.get("resolution")
    promises = list(seed.get("core_promises") or [])
    for value in (seed.get("central_conflict"), ending):
        if value and value not in promises:
            promises.append(value)
    return {
        "schema": SERIES_BIBLE_SCHEMA,
        "title": snapshot.get("title") or seed.get("title"),
        "genre": snapshot.get("genre"),
        "target_audience": snapshot.get("target_audience")
        or seed.get("target_audience"),
        "story_format": snapshot.get("story_format"),
        "narrative_style": snapshot.get("theme"),
        "content_boundaries": copy.deepcopy(seed.get("content_constraints") or []),
        "initial_world_constraints": copy.deepcopy(seed.get("world_constraints") or []),
        "world_building": snapshot.get("world_building"),
        "chapter_count": len(chapters),
        "arc_boundaries": [
            [item["start_position"], item["end_position"]] for item in arcs
        ],
        "core_character_routes": copy.deepcopy(
            outline.get("core_character_routes") or []
        ),
        "initial_characters": [
            copy.deepcopy(item) for item in entities if item.get("kind") == "character"
        ],
        "initial_organizations": [
            copy.deepcopy(item)
            for item in entities
            if item.get("kind") == "organization"
        ],
        "key_objects": [
            copy.deepcopy(item) for item in entities if item.get("kind") == "object"
        ],
        "scope_taxonomy": copy.deepcopy(outline.get("scope_taxonomy") or []),
        "initial_scope_nodes": copy.deepcopy(outline.get("initial_scope_nodes") or []),
        "initial_scope_edges": copy.deepcopy(outline.get("initial_scope_edges") or []),
        "world_rules": copy.deepcopy(canon.get("world_rules") or []),
        "growth_curves": [
            {"arc_id": item["arc_id"], **copy.deepcopy(item.get("growth") or {})}
            for item in arcs
        ],
        "ending_direction": ending,
        "core_promises": promises,
    }


def _series_roadmap(outline, chapters, arcs) -> dict:
    return {
        "schema": ROADMAP_SCHEMA,
        "arcs": copy.deepcopy(arcs),
        "chapters": [
            {"position": int(item["position"]), "arc_id": _arc_id(arcs, item)}
            for item in chapters
        ],
        "future_commitments": [
            {
                "arc_id": item["arc_id"],
                "narrative_goal": item["narrative_goal"],
                "growth": copy.deepcopy(item.get("growth") or {}),
                "character_slot_ids": [
                    slot["slot_id"] for slot in item.get("character_slots") or []
                ],
                "scope_slot_ids": [
                    slot["slot_id"] for slot in item.get("scope_slots") or []
                ],
            }
            for item in arcs
        ],
    }


def _arc_id(arcs: list[dict], chapter: dict) -> str:
    position = int(chapter["position"])
    return next(
        item["arc_id"]
        for item in arcs
        if int(item["start_position"]) <= position <= int(item["end_position"])
    )
