from __future__ import annotations

from fastapi import HTTPException

from .story_novel_block_contract import assemble_prose_blocks
from .story_novel_chapter_package import generate_and_checkpoint_package
from .story_novel_chapter_service import chapter_entry
from .story_novel_domain import active_chapters
from .story_novel_incremental_plan import is_incremental_plan
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
from .story_novel_v3_checkpoint import (
    checkpoint_body,
    checkpoint_brief,
    checkpoint_prose,
)
from .story_novel_v3_context import build_v3_planning_context, build_v3_prose_input
from .story_novel_v3_generation import generate_chapter_brief, generate_prose_blocks
from .story_novel_v3_resume import reusable_body, reusable_brief, reusable_verified_body
from .story_novel_v3_runtime import candidate_checkpoint_ready, update_progress


async def generate_or_resume_v3(
    service, revision, task, chapter_plan: dict, generate_text, *, force=False
):
    position = int(chapter_plan["position"])
    existing = next(
        (item for item in active_chapters(revision) if item.position == position), None
    )
    entry = chapter_entry(revision, position)
    plan = dict(revision.generation_plan or {})
    if is_incremental_plan(plan):
        chapter_plan = next(
            item
            for item in plan.get("chapters") or []
            if int(item["position"]) == position
        )
    if chapter_plan.get("contract_status") == "pending":
        update_progress(service, task, position, revision, "chapter_planning")
        chapter_plan, brief, context, entry = await generate_and_checkpoint_package(
            service, revision, position, chapter_plan, entry, generate_text
        )
    else:
        context = build_v3_planning_context(service, revision, position, chapter_plan)
        brief, entry = await _brief_for(
            service, revision, task, chapter_plan, context, entry, generate_text, force
        )
    if not force and reusable_verified_body(entry, existing, context, brief):
        if candidate_checkpoint_ready(service, revision, existing, entry):
            return existing
        update_progress(service, task, position, revision, "memory_ready")
        materialize_v3_candidates(service, revision, existing, task, entry)
        return existing
    prose_input = build_v3_prose_input(context, brief, chapter_plan)
    expected_delta = context["brief_input"]["expected_delta"]
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
    )
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


async def _brief_for(
    service, revision, task, chapter_plan, context, entry, generate_text, force
):
    position = int(chapter_plan["position"])
    brief = None if force else reusable_brief(entry, context, chapter_plan)
    if brief is not None:
        return brief, entry
    update_progress(service, task, position, revision, "chapter_planning")
    brief, metrics = await generate_chapter_brief(
        revision, position, context["brief_input"], generate_text
    )
    return brief, checkpoint_brief(
        service, revision, position, entry, context, brief, metrics
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
    prose, metrics = await generate_prose_blocks(
        revision,
        position,
        prompt_input,
        len(brief["beats"]),
        generate_text,
    )
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
    )
    if not selected["audit"]["passed"]:
        messages = "; ".join(
            item["message"]
            for item in selected["audit"]["state_validation"]["violations"][:3]
        )
        raise HTTPException(
            status_code=500, detail=f"第 {position} 章 v3 门禁失败：{messages}"
        )
    update_progress(service, task, position, revision, "memory_ready")
    materialize_v3_candidates(service, revision, chapter, task, entry)
    return chapter
