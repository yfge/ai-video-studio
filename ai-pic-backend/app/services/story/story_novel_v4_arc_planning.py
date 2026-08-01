"""Refine and freeze only the current arc from its real opening state."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

from fastapi import HTTPException

from . import story_novel_planning_invocations as planning_invocations
from .story_novel_arc_slot_contract import parse_arc_package
from .story_novel_context_utils import value_hash
from .story_novel_future_guard_index import compile_future_guard_index
from .story_novel_incremental_plan import chapter_skeleton, skeleton_hash
from .story_novel_length_service import generation_plan_hash
from .story_novel_planner_snapshot import build_planner_snapshot
from .story_novel_prompt_renderer import render_novel_prompt
from .story_novel_v3_generation import _generate_with_format_repair
from .story_novel_v4_arc_retry import (
    archive_failed_arc_calls,
    archive_stale_arc_snapshot,
)
from .story_novel_v4_call_snapshot import freeze_v4_call_input
from .story_novel_v4_plan import arc_for_position
from .story_novel_v4_plan_reset import mark_snapshot_stale
from .story_novel_v4_scope_context import scope_world_context
from .story_novel_v4_snapshot_guard import lock_current_snapshot_source
from .story_novel_world_reveal import compile_world_reveal_index


async def ensure_current_arc(
    service, revision, position: int, entry: dict, generate_text
) -> dict:
    plan = dict(revision.generation_plan or {})
    target = _roadmap_arc(plan, position)
    current = plan.get("current_arc_plan") or {}
    if current.get("arc_id") == target.get("arc_id"):
        return entry
    if position != int(target.get("start_position") or 0):
        raise ValueError("只能在分卷起点冻结新的 Arc Plan")
    source_rows = _arc_rows(plan, target)
    snapshot = entry.get("arc_planner_snapshot")
    source_change = _arc_snapshot_source_change(snapshot, plan)
    if source_change and archive_stale_arc_snapshot(
        entry, target["arc_id"], source_change
    ):
        _save_entry(service, revision, position, entry)
        snapshot = None
    if snapshot:
        if not _valid_arc_snapshot(snapshot, target):
            mark_snapshot_stale(
                service, revision, position, "arc snapshot hash invalid"
            )
            raise HTTPException(status_code=409, detail="Arc Plan 冻结快照无效")
        revision = lock_current_snapshot_source(service, revision, snapshot)
        if archive_failed_arc_calls(entry, target["arc_id"]):
            _save_entry(service, revision, position, entry)
    else:
        base = build_planner_snapshot(service, revision, position, source_rows[0])
        snapshot = _arc_snapshot(plan, target, source_rows, base)
        entry.update(
            arc_planner_snapshot=snapshot,
            arc_planner_snapshot_hash=snapshot["snapshot_hash"],
            source_manifest=snapshot["source_manifest"],
            state_before_hash=snapshot["state_before_hash"],
            canon_hash=plan.get("canon_hash"),
            chapter_contract_hash=value_hash(chapter_skeleton(source_rows[0])),
        )
        _save_entry(service, revision, position, entry)
    prompt = render_novel_prompt(
        "story_novel_arc_plan_v4",
        arc_planner_input_json=json.dumps(
            snapshot["model_input"], ensure_ascii=False, sort_keys=True
        ),
    )
    package, metrics = await _generate_with_format_repair(
        revision,
        prompt,
        lambda text: parse_arc_package(
            text,
            source_rows,
            target,
            scope_world_context(plan, snapshot),
        ),
        generate_text,
        stage=f"arc_planning.{target['arc_id']}",
        max_tokens=12_000,
        format_repair_max_tokens=8_000,
        before_call=lambda stage, text: freeze_v4_call_input(
            service, revision, position, entry, stage, text
        ),
    )
    revision = lock_current_snapshot_source(service, revision, snapshot)
    _checkpoint_arc(revision, target, package, metrics)
    stage_metrics = dict(entry.get("stage_metrics") or {})
    stage_metrics["arc_planning"] = metrics
    entry["stage_metrics"] = stage_metrics
    _save_entry(service, revision, position, entry)
    return entry


def _valid_arc_snapshot(snapshot, target) -> bool:
    stored = snapshot.get("snapshot_hash") if isinstance(snapshot, dict) else None
    payload = dict(snapshot or {})
    payload.pop("snapshot_hash", None)
    return bool(
        stored
        and stored == value_hash(payload)
        and snapshot.get("schema") == "story_novel_arc_planner_snapshot.v1"
        and snapshot.get("arc_id") == target.get("arc_id")
        and snapshot.get("model_input_hash") == value_hash(snapshot.get("model_input"))
    )


def _arc_snapshot(plan, target, rows, base):
    model_input = {
        "schema": "story_novel_arc_planner_input.v1",
        "current_arc": copy.deepcopy(target),
        "scope_taxonomy": copy.deepcopy(
            (plan.get("scope_graph") or {}).get("taxonomy") or []
        ),
        "chapter_skeletons": [chapter_skeleton(item) for item in rows],
        "series_promises": copy.deepcopy(
            (plan.get("series_bible") or {}).get("core_promises") or []
        ),
        "visible_characters_and_world": copy.deepcopy(
            base["model_input"].get("visible_characters_and_world") or []
        ),
        "planning_evidence": copy.deepcopy(
            base["model_input"].get("planning_evidence") or []
        ),
        "recent_chapters": copy.deepcopy(
            base["model_input"].get("recent_chapters") or []
        ),
        "previous_chapter_tail": base["model_input"].get("previous_chapter_tail"),
    }
    snapshot = {
        "schema": "story_novel_arc_planner_snapshot.v1",
        "position": int(target["start_position"]),
        "arc_id": target["arc_id"],
        "generation_plan_hash": plan.get("plan_hash"),
        "canon_hash": plan.get("canon_hash"),
        "source_manifest": copy.deepcopy(base["source_manifest"]),
        "state_before_hash": base["state_before_hash"],
        "scope_context": scope_world_context(plan, base),
        "handle_bindings": copy.deepcopy(base.get("handle_bindings") or {}),
        "model_input": model_input,
        "model_input_hash": value_hash(model_input),
    }
    snapshot["snapshot_hash"] = value_hash(snapshot)
    return snapshot


def _arc_snapshot_source_change(snapshot: dict | None, plan: dict) -> str | None:
    if not isinstance(snapshot, dict):
        return None
    if snapshot.get("generation_plan_hash") != plan.get("plan_hash"):
        return "generation_plan_hash_changed_before_resume"
    if snapshot.get("canon_hash") != plan.get("canon_hash"):
        return "canon_hash_changed_before_resume"
    return None


def _checkpoint_arc(revision, target, package, metrics):
    plan = dict(revision.generation_plan or {})
    chapters = package["chapters"]
    rows = [dict(item) for item in plan.get("chapters") or []]
    by_position = {item["position"]: item for item in chapters}
    for index, row in enumerate(rows):
        refined = by_position.get(int(row["position"]))
        if refined:
            rows[index] = {**row, **refined}
    current = {**copy.deepcopy(target), **copy.deepcopy(package)}
    arc_plans = dict(plan.get("arc_plans") or {})
    arc_plans[target["arc_id"]] = current
    plan.update(
        chapters=rows,
        current_arc_plan=current,
        current_arc_plan_hash=value_hash(current),
        arc_plans=arc_plans,
        arc_plans_hash=value_hash(arc_plans),
        frozen_through_position=int(target["end_position"]),
        chapter_skeleton_hash=skeleton_hash(rows),
    )
    future = compile_future_guard_index(
        rows,
        milestones=(plan.get("canon") or {}).get("milestones") or [],
        entities=(plan.get("canon") or {}).get("entities") or [],
    )
    reveal = compile_world_reveal_index(plan.get("canon") or {}, rows)
    plan.update(
        future_guard_index=future,
        future_guard_hash=future["index_hash"],
        world_reveal_index=reveal,
        world_reveal_hash=reveal["index_hash"],
    )
    attempt = (metrics.get("attempts") or [])[-1]
    carrier = SimpleNamespace(generation_plan=plan)
    planning_invocations.record_attempt(
        carrier,
        f"arc_plan.{target['arc_id']}",
        attempt,
        positions=[item["position"] for item in chapters],
        result_hash=value_hash(current),
    )
    plan = dict(carrier.generation_plan)
    planning_invocations.finalize(plan, plan["canon"], rows)
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan


def _roadmap_arc(plan, position):
    return next(
        copy.deepcopy(item)
        for item in (plan.get("series_roadmap") or {}).get("arcs") or []
        if int(item["start_position"]) <= position <= int(item["end_position"])
    )


def _arc_rows(plan, arc):
    return [
        dict(item)
        for item in plan.get("chapters") or []
        if int(arc["start_position"])
        <= int(item["position"])
        <= int(arc["end_position"])
    ]


def _save_entry(service, revision, position, entry):
    from .story_novel_chapter_service import save_ledger_entry

    save_ledger_entry(revision, position, entry)
    service.db.commit()
