"""Human-confirmed Canon edits and deterministic successor invalidation."""

from __future__ import annotations

from fastapi import HTTPException

from .story_novel_canon_diff import changed_canon_refs, earliest_affected_position
from .story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    validate_generation_plan,
)
from .story_novel_length_service import generation_plan_hash
from .story_novel_memory_context import mark_revision_ledger_stale
from .story_novel_plan_checkpoint import validated_canon_checkpoint


def update_revision_canon(service, revision, request):
    plan = dict(revision.generation_plan or {})
    ready = plan.get("status") == "ready"
    failed_checkpoint = (
        plan.get("status") == "failed"
        and plan.get("phase") == "chapters"
        and validated_canon_checkpoint(plan) is not None
    )
    planning_checkpoint = (
        plan.get("status") == "planning"
        and plan.get("phase") == "chapters"
        and validated_canon_checkpoint(plan) is not None
    )
    if plan.get("schema") != "story_novel_generation_plan.v2" or not (
        ready or failed_checkpoint or planning_checkpoint
    ):
        raise HTTPException(status_code=409, detail="当前修订版没有可编辑 Canon")
    if int(plan.get("version") or 0) != request.expected_plan_version:
        raise HTTPException(status_code=409, detail="章节计划已被其他窗口更新")
    before = dict(plan.get("canon") or {})
    if before.get("canon_hash") != request.expected_canon_hash:
        raise HTTPException(status_code=409, detail="Canon 已被其他窗口更新")
    try:
        required_gate = (
            CANON_GATE_VERSION
            if int(plan.get("canon_gate_version") or 0) == CANON_GATE_VERSION
            else 0
        )
        after = normalize_canon(
            request.canon.model_dump(), required_gate_version=required_gate
        )
        if ready:
            validate_generation_plan(after, plan.get("chapters") or [])
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    changed = changed_canon_refs(before, after)
    stale_from = (
        earliest_affected_position(plan.get("chapters") or [], changed)
        if changed
        else None
    )
    plan.update(
        version=int(plan["version"]) + 1,
        canon=after,
        canon_hash=after["canon_hash"],
    )
    if failed_checkpoint:
        plan["error"] = None
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    if stale_from is not None:
        mark_revision_ledger_stale(revision, from_position=stale_from)
        ledger = dict(revision.continuity_ledger or {})
        ledger["stale_from_position"] = stale_from
        revision.continuity_ledger = ledger
        service._invalidate_from(revision, stale_from)
        report = dict(revision.continuity_report or {})
        if report:
            report.update(stale=True, stale_canon_hash=request.expected_canon_hash)
            revision.continuity_report = report
    service.db.commit()
    return revision, after["canon_hash"], stale_from
