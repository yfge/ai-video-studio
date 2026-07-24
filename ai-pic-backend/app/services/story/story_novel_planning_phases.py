from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException

from .story_novel_ai_prompts import canon_prompt, planning_prompt
from .story_novel_canon_milestone_filter import CANON_MODEL_FILTER_VERSION
from .story_novel_canon_repair import canon_repair_prompt as _canon_repair_prompt
from .story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    parse_model_canon,
)
from .story_novel_length_service import generation_plan_hash
from .story_novel_plan_parser import parse_plan
from .story_novel_plan_repair import plan_repair_prompt as _plan_repair_prompt
from .story_novel_plan_semantic_audit import (
    PLAN_SEMANTIC_AUDIT_VERSION,
    audit_and_patch_plan_batch,
    requires_plan_semantic_audit,
)
from .story_novel_planning_batches import (
    batch_contract,
    batch_frozen_spec,
    batch_thread_payoffs,
    chapter_batches,
    checkpoint_plan_batch,
    planning_batch_prompt,
    reusable_plan_draft,
)
from .story_novel_task_guard import ensure_task_not_cancelled
from .story_novel_thread_schedule import compile_thread_payoffs
from .story_novel_thread_schedule_checkpoint import (
    checkpoint_thread_payoffs,
    reusable_thread_payoffs,
)


async def compile_canon(
    service,
    revision,
    task,
    generate_text: Callable[..., Awaitable[str]],
    contract: dict,
    resumed_canon: dict | None,
) -> tuple[dict, list[dict] | None]:
    if resumed_canon:
        canon = normalize_canon(resumed_canon, required_gate_version=CANON_GATE_VERSION)
        return canon, None
    prompt = canon_prompt(planning_contract=contract)
    text = await generate_text(revision, prompt, max_tokens=16000)
    ensure_task_not_cancelled(service.db, task)
    canon, error, timeline_filter = parse_model_canon(text, contract)
    if not canon:
        repair = _canon_repair_prompt(prompt, text, error)
        text = await generate_text(revision, repair, max_tokens=16000)
        ensure_task_not_cancelled(service.db, task)
        canon, error, timeline_filter = parse_model_canon(text, contract)
    if not canon:
        fail_plan(service, revision, "canon", error)
    return canon, timeline_filter


def checkpoint_canon(
    service, revision, task, canon: dict, timeline_filter: list[dict] | None = None
) -> None:
    updates = {
        **dict(revision.generation_plan or {}),
        "phase": "chapters",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
    }
    if timeline_filter is not None:
        updates["canon_timeline_filter"] = {
            "dropped": timeline_filter or [],
            "kept_count": len(canon.get("timeline") or []),
        }
    revision.generation_plan = updates
    task.description = "Canon 编译完成，正在规划章节合同…"
    service.db.commit()


async def plan_chapters(
    service,
    revision,
    task,
    generate_text: Callable[..., Awaitable[str]],
    contract: dict,
    canon: dict,
    expected_positions: list[int],
    frozen_spec: dict | None,
) -> list[dict]:
    if frozen_spec is not None:
        ensure_task_not_cancelled(service.db, task)
        task.description = "Canon 编译完成，正在规划伏笔回收…"
        service.db.commit()
    thread_payoffs = reusable_thread_payoffs(frozen_spec)
    if thread_payoffs is None:
        try:
            thread_payoffs = await compile_thread_payoffs(
                service.db, task, generate_text, revision, frozen_spec
            )
        except ValueError as exc:
            fail_plan(service, revision, "chapters", str(exc))
    if thread_payoffs is not None and frozen_spec is not None:
        ensure_task_not_cancelled(service.db, task)
        checkpoint_thread_payoffs(service, revision, task, frozen_spec, thread_payoffs)
    chapters = reusable_plan_draft(
        dict(revision.generation_plan or {}), canon, expected_positions
    )
    for positions in chapter_batches(expected_positions):
        if positions and positions[-1] <= len(chapters):
            continue
        batch_spec = batch_frozen_spec(frozen_spec, positions)
        batch_payoffs = batch_thread_payoffs(thread_payoffs, positions)
        prompt = planning_prompt(
            planning_contract=batch_contract(contract, positions),
            canon=canon,
            thread_payoffs=batch_payoffs,
        )
        prompt = planning_batch_prompt(prompt, positions, canon, chapters)
        max_tokens = max(16000, len(positions or expected_positions or []) * 1400)
        text = await generate_text(revision, prompt, max_tokens=max_tokens)
        ensure_task_not_cancelled(service.db, task)
        parsed, error = parse_plan(
            text,
            positions or expected_positions,
            canon,
            batch_spec,
            batch_payoffs,
            prior_chapters=chapters,
            require_complete=not positions or positions[-1] == expected_positions[-1],
        )
        if not parsed:
            repair = _plan_repair_prompt(
                prompt,
                text,
                error,
                positions or expected_positions,
                canon=canon,
                frozen_spec=batch_spec,
                thread_payoffs=batch_payoffs,
            )
            text = await generate_text(revision, repair, max_tokens=max_tokens)
            ensure_task_not_cancelled(service.db, task)
            parsed, error = parse_plan(
                text,
                positions or expected_positions,
                canon,
                batch_spec,
                batch_payoffs,
                prior_chapters=chapters,
                require_complete=not positions
                or positions[-1] == expected_positions[-1],
            )
        if not parsed:
            fail_plan(service, revision, "chapters", error)
        rows = parsed["chapters"]
        if requires_plan_semantic_audit(contract):
            try:
                rows = await audit_and_patch_plan_batch(
                    revision,
                    contract=batch_contract(contract, positions),
                    canon=canon,
                    prior_chapters=chapters,
                    batch_chapters=rows,
                    require_complete=(
                        not positions or positions[-1] == expected_positions[-1]
                    ),
                    generate_text=generate_text,
                )
            except ValueError as exc:
                fail_plan(service, revision, "chapters", str(exc))
            ensure_task_not_cancelled(service.db, task)
        chapters.extend(rows)
        checkpoint_plan_batch(service, revision, task, canon, chapters)
    return chapters


def complete_plan(service, revision, task, frozen_spec, canon, chapters) -> dict:
    plan = {
        **(frozen_spec or {}),
        "schema": "story_novel_generation_plan.v2",
        "version": int((revision.generation_plan or {}).get("version") or 1),
        "status": "ready",
        "phase": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "plan_semantic_audit_version": (
            PLAN_SEMANTIC_AUDIT_VERSION
            if chapters and all(item.get("semantic_audit") for item in chapters)
            else None
        ),
        "canon_timeline_filter": (revision.generation_plan or {}).get(
            "canon_timeline_filter"
        ),
        "chapter_count": len(chapters),
        "target_chars": sum(int(item["target_chars"]) for item in chapters),
        "chapters": chapters,
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    plan.pop("chapter_plan_draft", None)
    plan.pop("chapter_plan_draft_canon_hash", None)
    revision.generation_plan = plan
    revision.chapter_count = len(chapters)
    revision.target_words = plan["target_chars"]
    task.description = f"规划完成，共 {len(chapters)} 章"
    ensure_task_not_cancelled(service.db, task)
    service.db.commit()
    return plan


def fail_plan(service, revision, phase: str, error: str | None) -> None:
    revision.generation_plan = {
        **dict(revision.generation_plan or {}),
        "status": "failed",
        "phase": phase,
        "error": error or "invalid generation plan",
    }
    service.db.commit()
    detail = "Canon 编译无效" if phase == "canon" else "章节规划无效"
    raise HTTPException(status_code=500, detail=f"{detail}，正文尚未生成")


def _parse_canon(
    text: str, planning_contract: dict | None = None
) -> tuple[dict | None, str | None]:
    return parse_model_canon(text, planning_contract)[:2]


_parse_canon_with_diagnostics = parse_model_canon
_parse_plan = parse_plan
