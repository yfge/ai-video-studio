"""Durable checkpoints for batched V5 consistency compilation."""

from fastapi import HTTPException

from .story_novel_plan_hash import generation_plan_hash


def checkpoint_foundation(service, revision, base, foundation, attempts):
    return checkpoint_batched(
        service,
        revision,
        {
            **base,
            **foundation,
            "consistency_schema_hash": foundation["consistency_schema"]["schema_hash"],
            "initial_snapshot_hash": foundation["initial_fact_graph"]["snapshot_hash"],
        },
        status="causal_compiling",
        diagnostics=[],
        attempts=attempts,
        partial={
            "schema": "story_novel_causal_event_graph.v1",
            "events": [],
            "obligations": [],
        },
        next_batch=0,
    )


def checkpoint_batched(
    service,
    revision,
    base,
    *,
    status,
    diagnostics,
    attempts,
    candidate=None,
    partial=None,
    next_batch=None,
    active_range=None,
    completed_range=None,
):
    completed = list(base.get("causal_compile_completed_ranges") or [])
    if completed_range and completed_range not in completed:
        completed.append(completed_range)
    plan = {
        **base,
        "status": "failed" if status == "failed" else "planning",
        "phase": "consistency_schema",
        "schema_compile_mode": "batched",
        "schema_compile_status": status,
        "schema_compile_diagnostics": diagnostics,
        "schema_compile_attempts": attempts,
        "causal_compile_completed_ranges": completed,
    }
    if candidate is None:
        plan.pop("schema_compile_candidate", None)
    else:
        plan["schema_compile_candidate"] = candidate
    if partial is not None:
        plan["causal_compile_partial_graph"] = partial
    if next_batch is not None:
        plan["causal_compile_next_batch"] = next_batch
    if active_range is None:
        plan.pop("causal_compile_active_range", None)
    else:
        plan["causal_compile_active_range"] = active_range
    plan.pop("plan_hash", None)
    revision.generation_plan = plan
    service.db.commit()
    return plan


def raise_batched_failure(
    service,
    revision,
    base,
    diagnostics,
    attempts,
    candidate,
    **checkpoint,
):
    checkpoint_batched(
        service,
        revision,
        base,
        status="failed",
        diagnostics=diagnostics,
        attempts=attempts,
        candidate=candidate,
        **checkpoint,
    )
    raise HTTPException(
        status_code=422,
        detail={"code": "V5_SCHEMA_COMPILE_FAILED", "diagnostics": diagnostics},
    )


def save_ready(service, revision, task, plan):
    if plan["plan_hash"] != generation_plan_hash(plan):
        raise RuntimeError("v5 plan hash changed during freeze")
    revision.generation_plan = plan
    task.description = "一致性模型已冻结，准备生成正文…"
    service.db.commit()
    return plan
