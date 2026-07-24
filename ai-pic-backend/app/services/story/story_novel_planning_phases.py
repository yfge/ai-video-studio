from __future__ import annotations

from typing import Awaitable, Callable

from app.schemas.story_novel_longform import StoryNovelGenerationPlan
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException
from pydantic import ValidationError

from .story_novel_ai_prompts import canon_prompt, planning_prompt
from .story_novel_canon_repair import canon_repair_prompt as _canon_repair_prompt
from .story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    parse_model_canon,
    validate_generation_plan,
)
from .story_novel_length_service import generation_plan_hash
from .story_novel_outline_merge import merge_frozen_chapters
from .story_novel_plan_normalizer import normalize_redundant_location_state
from .story_novel_plan_repair import plan_repair_prompt as _plan_repair_prompt
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
    prompt = planning_prompt(
        planning_contract=contract,
        canon=canon,
        thread_payoffs=thread_payoffs,
    )
    max_tokens = max(16000, len(expected_positions or []) * 1400)
    text = await generate_text(revision, prompt, max_tokens=max_tokens)
    ensure_task_not_cancelled(service.db, task)
    parsed, error = _parse_plan(
        text, expected_positions, canon, frozen_spec, thread_payoffs
    )
    if not parsed:
        repair = _plan_repair_prompt(
            prompt,
            text,
            error,
            expected_positions,
            canon=canon,
            frozen_spec=frozen_spec,
            thread_payoffs=thread_payoffs,
        )
        text = await generate_text(revision, repair, max_tokens=max_tokens)
        ensure_task_not_cancelled(service.db, task)
        parsed, error = _parse_plan(
            text, expected_positions, canon, frozen_spec, thread_payoffs
        )
    if not parsed:
        fail_plan(service, revision, "chapters", error)
    return parsed["chapters"]


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
        "canon_timeline_filter": (revision.generation_plan or {}).get(
            "canon_timeline_filter"
        ),
        "chapter_count": len(chapters),
        "target_chars": sum(int(item["target_chars"]) for item in chapters),
        "chapters": chapters,
    }
    plan["plan_hash"] = generation_plan_hash(plan)
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


def _parse_plan(
    text, expected_positions, canon, frozen_spec, thread_payoffs=None
) -> tuple[dict | None, str | None]:
    payload = extract_json_block(text)
    try:
        if not payload:
            raise ValueError("missing JSON object")
        parsed = StoryNovelGenerationPlan.model_validate(payload)
        positions = [item.position for item in parsed.chapters]
        if expected_positions and positions != expected_positions:
            raise ValueError(
                "explicit outline chapter coverage mismatch: "
                f"expected 1-{expected_positions[-1]}, got {len(positions)} chapters"
            )
        machine_rows = normalize_redundant_location_state(
            canon, parsed.model_dump()["chapters"]
        )
        rows = merge_frozen_chapters(
            machine_rows,
            frozen_spec,
            canon,
            thread_payoffs,
        )
        if not frozen_spec:
            validate_generation_plan(canon, rows)
        return {"chapters": rows}, None
    except (ValidationError, ValueError) as exc:
        return None, str(exc)
