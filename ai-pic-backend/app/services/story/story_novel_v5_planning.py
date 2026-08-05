"""Provider orchestration for automatic V5 consistency compilation."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block
from fastapi import HTTPException

from .story_novel_plan_hash import generation_plan_hash
from .story_novel_v5_batched_contracts import BATCHED_COMPILE_THRESHOLD
from .story_novel_v5_batched_planning import ensure_batched_v5_plan
from .story_novel_v5_plan import freeze_v5_plan, valid_v5_plan
from .story_novel_v5_prompts import (
    compile_prompt,
    compile_repair_prompt,
    prompt_policy,
)


async def ensure_v5_generation_plan(service, revision, task, generate_text):
    current = dict(revision.generation_plan or {})
    if valid_v5_plan(current, revision.story_snapshot or {}):
        return current
    if any(str(row.content_text or "").strip() for row in revision.chapters or []):
        raise HTTPException(
            status_code=409,
            detail="V5 冻结 Schema/hash 无效且已有正文，拒绝原地重编译",
        )
    if current.get("schema_compile_status") == "failed":
        raise HTTPException(
            status_code=422, detail=current.get("schema_compile_diagnostics")
        )
    if len(current.get("chapters") or []) > BATCHED_COMPILE_THRESHOLD:
        return await ensure_batched_v5_plan(
            service, revision, task, generate_text, current
        )
    return await _ensure_single_plan(service, revision, task, generate_text, current)


async def _ensure_single_plan(service, revision, task, generate_text, current):
    contract = _compile_contract(revision, current)
    if current.get("schema_compile_status") == "repairing":
        attempts = list(current.get("schema_compile_attempts") or [])
        diagnostics = list(current.get("schema_compile_diagnostics") or [])
        previous = dict(current.get("schema_compile_candidate") or {})
        if (
            len(attempts) != 1
            or not diagnostics
            or "schema_compile_candidate" not in current
        ):
            raise HTTPException(
                status_code=409, detail="V5 Schema 修复 checkpoint 不完整"
            )
    else:
        task.description = "正在编译本 Story 的一致性模型…"
        _checkpoint(service, revision, current, "compiling", [], [])
        first = await generate_text(
            revision,
            compile_prompt(contract),
            stage="consistency_schema.compile",
            max_tokens=20_000,
        )
        attempts = [_attempt(first)]
        previous = extract_json_block(str(first)) or {}
        payload, diagnostics = _parse_and_freeze(current, revision, first, attempts)
        if payload is not None:
            return _save_ready(service, revision, task, payload)
        _checkpoint(
            service,
            revision,
            current,
            "repairing",
            diagnostics,
            attempts,
            candidate=previous,
        )
    task.description = "一致性模型未通过，正在执行唯一一次结构/语义修复…"
    repair = await generate_text(
        revision,
        compile_repair_prompt(contract, previous, diagnostics),
        stage="consistency_schema.repair",
        max_tokens=20_000,
        temperature=0.1,
    )
    attempts.append(_attempt(repair))
    payload, diagnostics = _parse_and_freeze(current, revision, repair, attempts)
    if payload is not None:
        return _save_ready(service, revision, task, payload)
    _checkpoint(
        service,
        revision,
        current,
        "failed",
        diagnostics,
        attempts,
        candidate=extract_json_block(str(repair)) or {},
    )
    raise HTTPException(
        status_code=422,
        detail={"code": "V5_SCHEMA_COMPILE_FAILED", "diagnostics": diagnostics},
    )


def _compile_contract(revision, plan):
    snapshot = revision.story_snapshot or {}
    return {
        "story_seed": snapshot.get("story_seed") or {},
        "story_seed_version": plan.get("story_seed_version"),
        "outline_hash": plan.get("outline_hash"),
        "story": {
            key: snapshot.get(key)
            for key in (
                "title",
                "genre",
                "theme",
                "target_audience",
                "premise",
                "synopsis",
                "main_conflict",
                "resolution",
            )
        },
        "characters": snapshot.get("characters") or [],
        "chapter_contracts": plan.get("chapters") or [],
    }


def _parse_and_freeze(base, revision, text, attempts):
    try:
        parsed = extract_json_block(str(text))
        if not isinstance(parsed, dict):
            raise ValueError("response does not contain one JSON object")
        candidate = freeze_v5_plan(
            {
                **base,
                "prompt_templates": prompt_policy(),
                "schema_compile_revision_business_id": revision.business_id,
            },
            parsed,
            revision.story_snapshot or {},
            attempts,
        )
        return candidate, []
    except (TypeError, ValueError) as exc:
        return None, [{"code": "compile_validation_failed", "message": str(exc)}]


def _checkpoint(
    service, revision, base, status, diagnostics, attempts, *, candidate=None
):
    plan = {
        **base,
        "status": "failed" if status == "failed" else "planning",
        "phase": "consistency_schema",
        "schema_compile_status": status,
        "schema_compile_diagnostics": diagnostics,
        "schema_compile_attempts": attempts,
    }
    if candidate is not None:
        plan["schema_compile_candidate"] = candidate
    plan.pop("plan_hash", None)
    revision.generation_plan = plan
    service.db.commit()


def _save_ready(service, revision, task, plan):
    if plan["plan_hash"] != generation_plan_hash(plan):
        raise RuntimeError("v5 plan hash changed during freeze")
    revision.generation_plan = plan
    task.description = "一致性模型已冻结，准备生成正文…"
    service.db.commit()
    return plan


def _attempt(text):
    return dict(getattr(text, "invocation_evidence", {}) or {})
