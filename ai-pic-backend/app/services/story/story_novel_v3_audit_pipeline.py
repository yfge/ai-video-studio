"""Resume-safe substantive audit and local-repair orchestration."""

from app.repositories.llm_invocation_repository import LLMInvocationRepository
from fastapi import HTTPException

from .story_novel_invocation_evidence import GeneratedNovelText, invocation_row_evidence
from .story_novel_v3_audit_budget import (
    audit_budget_available,
    audit_contract_hash,
    audit_stage,
    persisted_audit_attempts,
    prune_abandoned_reservations,
    reserve_audit_attempt,
)
from .story_novel_v3_audit_contract import ensure_audit_contract
from .story_novel_v3_evaluation import evaluate_body
from .story_novel_v3_repair import repair_failed_body


async def evaluate_and_repair(
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
    *,
    entry,
    frozen_plan=None,
    before_call=None,
):
    position = int(chapter_plan["position"])
    audit_hash = audit_contract_hash(entry["body_hash"], expected_delta, entry)
    budget_hash = ensure_audit_contract(service, revision, entry, position, audit_hash)
    prune_abandoned_reservations(
        service,
        revision,
        entry,
        position,
        budget_hash,
        getattr(task, "id", None),
    )
    persisted = persisted_audit_attempts(
        service.db, revision.business_id, position, budget_hash
    )
    available = audit_budget_available(entry, budget_hash, persisted)
    budget_stage = audit_stage(position, budget_hash)
    logical_stage = f"{budget_stage}.body.{audit_hash}"
    replay = (
        reusable_audit_text(service.db, revision.business_id, logical_stage)
        if not available or entry.get("audit_failure_kind") != "evidence_only"
        else None
    )
    if not available and replay is None:
        raise HTTPException(
            status_code=409, detail="当前正文审计次数已耗尽，需显式重生成"
        )

    def reserve_call(stage):
        return reserve_audit_attempt(
            service,
            revision,
            entry,
            position,
            budget_hash,
            stage,
            task_id=getattr(task, "id", None),
        )

    if replay is None:
        audit_generate = generate_text
        first_budget = available
        repair_budget = available
        first_reserve = reserve_call
    else:

        async def audit_generate(*_args, **_kwargs):
            return replay

        first_budget = 1
        repair_budget = available + 1
        first_reserve = None
    first = await evaluate_body(
        service,
        revision,
        task,
        chapter_plan,
        brief,
        context,
        prose_result,
        expected_delta,
        audit_generate,
        allow_evidence_retry=replay is None and available >= 2,
        audit_stage=logical_stage,
        audit_call_budget=first_budget,
        reserve_call=first_reserve,
        frozen_plan=frozen_plan,
        before_call=before_call,
    )
    return await repair_failed_body(
        service,
        revision,
        task,
        chapter_plan,
        brief,
        context,
        prose_input,
        expected_delta,
        first,
        generate_text,
        audit_stage=budget_stage,
        audit_call_budget=repair_budget,
        reserve_call=reserve_call,
        entry=entry,
        allow_repair=not entry.get("body_repair_count"),
        frozen_plan=frozen_plan,
        before_call=before_call,
    )


def reusable_audit_text(db, revision_business_id: str, logical_stage: str):
    prefix = f"story_novel.{revision_business_id}.{logical_stage}"
    rows = LLMInvocationRepository(db).list_by_call_scene_prefix(prefix)
    for row in reversed(rows):
        metadata = dict(row.response_metadata or {})
        if (
            row.status == "succeeded"
            and metadata.get("product_status", "accepted") == "accepted"
            and metadata.get("finish_reason") == "stop"
            and str(row.response or "").strip()
        ):
            text = str(row.response).strip()
            return GeneratedNovelText(text, invocation_row_evidence(row))
    return None
