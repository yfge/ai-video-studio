"""Deterministic checks plus proof-only audit for one assembled v3 body."""

from .story_novel_future_guard_index import future_claim_cards
from .story_novel_sentence_spans import sentence_spans
from .story_novel_v3_audit import evaluate_proof_audit
from .story_novel_v3_audit_semantics import (
    current_state_contract,
    future_state_boundaries,
)
from .story_novel_v3_gate import (
    combine_violations,
    failed_blocks_for_prose,
    prose_violations,
)
from .story_novel_v3_generation import audit_chapter, merge_stage_metrics
from .story_novel_v3_proof_validation import merge_proof_audits
from .story_novel_v3_repair_guidance import deterministic_repair_issue
from .story_novel_v3_runtime import update_progress
from .story_novel_world_expansion import canon_with_plan_expansion


async def evaluate_body(
    service,
    revision,
    task,
    chapter_plan,
    brief,
    context,
    prose,
    expected_delta,
    generate_text,
    *,
    allow_evidence_retry,
    audit_stage,
    audit_call_budget,
    reserve_call,
    frozen_plan=None,
    before_call=None,
):
    plan = frozen_plan or revision.generation_plan or {}
    position = int(chapter_plan["position"])
    deterministic = prose_violations(revision, chapter_plan, prose, brief)
    update_progress(service, task, position, revision, "audit")
    index = sentence_spans(prose["content_text"])
    audit, metrics = await _audit_once(
        revision,
        position,
        chapter_plan,
        brief,
        context,
        prose,
        expected_delta,
        index,
        generate_text,
        stage=audit_stage,
        max_calls=audit_call_budget,
        reserve_call=reserve_call,
        frozen_plan=plan,
        before_call=before_call,
    )
    evaluated = _evaluate(
        audit, plan, chapter_plan, context, prose, brief, expected_delta
    )
    evaluated = combine_violations(evaluated, deterministic)
    _attach_deterministic_blocks(evaluated, deterministic, prose, brief)
    remaining = max(0, audit_call_budget - int(metrics.get("calls") or 0))
    if _should_retry(evaluated, deterministic, allow_evidence_retry and remaining > 0):
        retry, retry_metrics = await _audit_once(
            revision,
            position,
            chapter_plan,
            brief,
            context,
            prose,
            expected_delta,
            index,
            generate_text,
            stage=f"{audit_stage}.evidence_retry",
            max_calls=remaining,
            reserve_call=reserve_call,
            repair_focus=[
                item["message"] for item in evaluated["state_validation"]["violations"]
            ],
            frozen_plan=plan,
            before_call=before_call,
        )
        merged = merge_proof_audits(audit, retry)
        evaluated = _evaluate(
            merged, plan, chapter_plan, context, prose, brief, expected_delta
        )
        metrics = merge_stage_metrics(metrics, retry_metrics)
    return {"prose": prose, "audit": evaluated, "audit_metrics": metrics}


async def _audit_once(
    revision,
    position,
    chapter_plan,
    brief,
    context,
    prose,
    expected_delta,
    index,
    generate_text,
    stage,
    max_calls,
    reserve_call,
    repair_focus=None,
    frozen_plan=None,
    before_call=None,
):
    plan = frozen_plan or revision.generation_plan or {}
    effective_canon = canon_with_plan_expansion(
        plan.get("canon") or {}, [chapter_plan], context["state_before"]
    )
    return await audit_chapter(
        revision,
        position,
        content_text=prose["content_text"],
        sentence_index=index,
        expected_delta=expected_delta,
        canon=effective_canon,
        chapter_plan=chapter_plan,
        future_claim_cards=future_claim_cards(
            plan["future_guard_index"],
            position,
            prose["content_text"],
            visible_entity_ids=chapter_plan.get("canon_refs") or [],
        ),
        visible_world_rules=(
            context["hard_constraints"].get("compiled_canon") or {}
        ).get("world_rules")
        or [],
        generate_text=generate_text,
        stage=stage,
        max_calls=max_calls,
        reserve_call=reserve_call,
        repair_focus=repair_focus,
        brief=brief,
        established_background=_established_background(context),
        current_state_contract=current_state_contract(
            effective_canon,
            chapter_plan,
            expected_delta,
            context["state_before"],
            prose["content_text"],
        ),
        future_state_boundaries=future_state_boundaries(
            plan,
            chapter_plan,
            expected_delta,
            context["state_before"],
        ),
        before_call=before_call,
    )


def _established_background(context: dict) -> list[dict]:
    result = []
    brief_input = context.get("brief_input", {})
    position = int((brief_input.get("chapter_contract") or {}).get("position") or 0)
    for key, entry in (brief_input.get("prior_ledger") or {}).items():
        valid = (
            int(key) < position
            and entry.get("status") == "ready"
            and entry.get("plot_delta_source") == "expected_delta"
            and entry.get("plot_delta_version") == 2
            and (entry.get("state_validation") or {}).get("status") == "passed"
            and entry.get("body_hash")
            and entry.get("source_hash")
        )
        if not valid:
            continue
        result.extend(
            {
                "chapter_position": int(key),
                "key_event": str(item),
                "source_hash": entry["source_hash"],
            }
            for item in (entry.get("plot_delta") or {}).get("key_events") or []
            if str(item).strip()
        )
    return list(
        {
            (item["chapter_position"], item["key_event"]): item for item in result
        }.values()
    )


def _evaluate(audit, plan, chapter_plan, context, prose, brief, expected_delta):
    return evaluate_proof_audit(
        audit=audit,
        expected_delta=expected_delta,
        canon=plan.get("canon") or {},
        chapter_plan=chapter_plan,
        state_before=context["state_before"],
        content_text=prose["content_text"],
        brief=brief,
        block_manifest=prose["blocks"],
    )


def _attach_deterministic_blocks(evaluated, violations, prose, brief) -> None:
    if not violations:
        return
    if not evaluated.get("state_contract_failed"):
        evaluated["repairable"] = True
        evaluated["failure_kind"] = "content"
    evaluated["repair_issues"].extend(
        deterministic_repair_issue(item) for item in violations
    )
    evaluated["failed_block_ids"] = sorted(
        set(evaluated["failed_block_ids"])
        | set(failed_blocks_for_prose(violations, prose["block_contents"], brief))
    )


def _should_retry(evaluated, deterministic, allowed) -> bool:
    return bool(
        allowed
        and not deterministic
        and not evaluated["passed"]
        and evaluated.get("failure_kind") == "evidence_only"
    )
