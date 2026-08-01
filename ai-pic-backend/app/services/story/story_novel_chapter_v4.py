"""Frozen-snapshot v4 chapter planning, prose, audit, and memory pipeline."""

from __future__ import annotations

from fastapi import HTTPException

from .story_novel_block_contract import assemble_prose_blocks
from .story_novel_chapter_service import chapter_entry
from .story_novel_domain import active_chapters
from .story_novel_planner_snapshot import planner_snapshot_sources_current
from .story_novel_prose_length_control import (
    PROMPT_CONTRACT_VERSION,
    build_length_control,
    controlled_prompt_input,
    record_length_observation,
)
from .story_novel_prose_length_history import prior_revision_length_samples
from .story_novel_prose_length_policy import POLICY_SCHEMA, activate_length_control
from .story_novel_v3_audit_pipeline import evaluate_and_repair
from .story_novel_v3_candidates import materialize_v3_candidates
from .story_novel_v3_checkpoint import checkpoint_body, checkpoint_prose
from .story_novel_v3_resume import reusable_body, reusable_verified_body
from .story_novel_v3_runtime import candidate_checkpoint_ready, update_progress
from .story_novel_v4_arc_planning import ensure_current_arc
from .story_novel_v4_call_snapshot import freeze_v4_call_input
from .story_novel_v4_generation import generate_prose_blocks_v4
from .story_novel_v4_plan_reset import mark_snapshot_stale
from .story_novel_v4_planning import (
    context_from_checkpoint,
    prepare_v4_chapter,
    reusable_v4_package,
)
from .story_novel_v4_prose_input import build_v4_prose_input
from .story_novel_v4_snapshot_guard import lock_chapter_execution_source


async def generate_or_resume_v4(
    service, revision, task, chapter_plan: dict, generate_text, *, force=False
):
    position = int(chapter_plan["position"])
    existing = next(
        (item for item in active_chapters(revision) if item.position == position), None
    )
    entry = chapter_entry(revision, position)
    entry = await ensure_current_arc(service, revision, position, entry, generate_text)
    plan = dict(revision.generation_plan or {})
    chapter_plan = next(
        item for item in plan.get("chapters") or [] if int(item["position"]) == position
    )
    if chapter_plan.get("contract_status") == "pending":
        update_progress(service, task, position, revision, "chapter_planning")
        (
            chapter_plan,
            brief,
            context,
            entry,
            snapshot,
            intent,
        ) = await prepare_v4_chapter(
            service, revision, position, chapter_plan, entry, generate_text
        )
    else:
        package = reusable_v4_package(entry, position)
        if package is None:
            raise HTTPException(
                status_code=409,
                detail=f"第 {position} 章冻结规划快照无效；拒绝重组上下文",
            )
        snapshot, intent, brief = package
        if not planner_snapshot_sources_current(service, revision, snapshot):
            mark_snapshot_stale(
                service,
                revision,
                position,
                "planner snapshot source manifest changed",
            )
            raise HTTPException(
                status_code=409,
                detail=f"第 {position} 章规划来源已变化；快照已 stale，拒绝静默重组",
            )
        context = context_from_checkpoint(entry, chapter_plan)
    if not force and reusable_verified_body(entry, existing, context, brief):
        if candidate_checkpoint_ready(service, revision, existing, entry):
            return existing
        update_progress(service, task, position, revision, "memory_ready")
        materialize_v3_candidates(service, revision, existing, task, entry)
        return existing
    prose_input = build_v4_prose_input(snapshot, intent, chapter_plan, brief)
    expected_delta = entry["expected_delta"]
    prose_result, entry = await _prose_for(
        service,
        revision,
        task,
        chapter_plan,
        entry,
        brief,
        context,
        prose_input,
        expected_delta,
        existing,
        generate_text,
        force,
    )
    frozen_plan = {
        **snapshot["audit_context"],
        "chapters": [chapter_plan],
    }
    selected, stage_metrics, repair_count = await evaluate_and_repair(
        service,
        revision,
        task,
        chapter_plan,
        brief,
        context,
        prose_input,
        expected_delta,
        prose_result,
        generate_text,
        entry=entry,
        frozen_plan=frozen_plan,
        before_call=_call_freezer(service, revision, position, entry),
    )
    revision = lock_chapter_execution_source(service, revision, entry)
    return _finish(
        service,
        revision,
        task,
        chapter_plan,
        entry,
        brief,
        prose_input,
        expected_delta,
        selected,
        stage_metrics,
        repair_count,
    )


async def _prose_for(
    service,
    revision,
    task,
    chapter_plan,
    entry,
    brief,
    context,
    prose_input,
    expected_delta,
    existing,
    generate_text,
    force,
):
    position = int(chapter_plan["position"])
    blocks = None if force else reusable_body(entry, existing, context, brief)
    if blocks is not None:
        return {"block_contents": blocks, **assemble_prose_blocks(blocks)}, entry
    update_progress(service, task, position, revision, "prose")
    policy = (revision.continuity_ledger or {}).get("prose_length_control")
    baseline = (
        []
        if policy
        else prior_revision_length_samples(
            service.db,
            revision,
            POLICY_SCHEMA,
            PROMPT_CONTRACT_VERSION,
        )
    )
    activate_length_control(revision, position, baseline_samples=baseline)
    length_control = build_length_control(service.db, revision, position, prose_input)
    prompt_input = controlled_prompt_input(prose_input, length_control)
    prose, metrics = await generate_prose_blocks_v4(
        revision,
        position,
        prompt_input,
        len(brief["beats"]),
        generate_text,
        before_call=_call_freezer(service, revision, position, entry),
    )
    revision = lock_chapter_execution_source(service, revision, entry)
    metrics = record_length_observation(metrics, length_control, prose, prompt_input)
    _chapter, entry = checkpoint_prose(
        service,
        revision,
        position,
        chapter_plan,
        entry,
        brief,
        prose_input,
        expected_delta,
        prose,
        metrics,
    )
    return prose, entry


def _finish(
    service,
    revision,
    task,
    chapter_plan,
    entry,
    brief,
    prose_input,
    expected_delta,
    selected,
    stage_metrics,
    repair_count,
):
    position = int(chapter_plan["position"])
    chapter, entry = checkpoint_body(
        service,
        revision,
        position,
        chapter_plan,
        entry,
        brief,
        prose_input,
        expected_delta,
        selected["prose"],
        selected["audit"],
        stage_metrics,
        repair_count=repair_count,
        commit=not selected["audit"]["passed"],
    )
    if not selected["audit"]["passed"]:
        messages = "; ".join(
            item["message"]
            for item in selected["audit"]["state_validation"]["violations"][:3]
        )
        raise HTTPException(
            status_code=500, detail=f"第 {position} 章 v4 门禁失败：{messages}"
        )
    update_progress(service, task, position, revision, "memory_ready", commit=False)
    materialize_v3_candidates(service, revision, chapter, task, entry)
    return chapter


def _call_freezer(service, revision, position, entry):
    return lambda stage, prompt: freeze_v4_call_input(
        service,
        revision,
        position,
        entry,
        stage,
        prompt,
        reuse_existing_input=True,
    )
