"""Durable v4 ledger checkpoints and resume proofs for v3 chapters."""

from __future__ import annotations

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_context_utils import value_hash
from .story_novel_domain import sha256_text
from .story_novel_memory_context import (
    capture_chapter_source_hashes,
    invalidate_chapter_source,
)
from .story_novel_state_service import state_hash
from .story_novel_v3_audit_budget import audit_contract_hash, lock_checkpoint_entry
from .story_novel_v3_audit_checkpoint import prepare_checkpoint_audit


def checkpoint_brief(service, revision, position, entry, context, brief, metrics):
    from .story_novel_chapter_service import save_ledger_entry

    entry.update(
        {
            "status": "chapter_planning",
            "stage": "chapter_planning",
            "chapter_brief": brief,
            "brief_input": context["brief_input"],
            "brief_hash": brief["brief_hash"],
            "brief_input_hash": context["evidence"]["context_hash"],
            "chapter_contract_hash": context["evidence"]["chapter_contract_hash"],
            "canon_hash": context["evidence"]["canon_hash"],
            "context_hash": context["evidence"]["context_hash"],
            "context_evidence": context["evidence"],
            "state_before_hash": context["evidence"]["state_before_hash"],
            "stage_metrics": {
                **dict(entry.get("stage_metrics") or {}),
                "chapter_planning": metrics,
            },
        }
    )
    save_ledger_entry(revision, position, entry)
    service.db.commit()
    return entry


def checkpoint_prose(
    service,
    revision,
    position,
    chapter_plan,
    entry,
    brief,
    prose_input,
    expected_delta,
    prose_result,
    metrics,
    *,
    metric_stage="prose",
    repair_count=0,
    repair_resume=None,
):
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    existing = next(
        (item for item in revision.chapters if item.position == position), None
    )
    old_source = (
        capture_chapter_source_hashes([existing])[existing.business_id]
        if existing
        else None
    )
    chapter = service.checkpoint_chapter(
        revision,
        position=position,
        title=chapter_plan["title"],
        content_text=prose_result["content_text"],
        summary=brief["summary"],
        cliffhanger=brief.get("cliffhanger"),
        commit=False,
    )
    if old_source and old_source != novel_chapter_source_hash(chapter):
        invalidate_chapter_source(
            service.db,
            revision,
            chapter,
            old_source,
            force=True,
            reason_code="v3_source_hash_changed",
        )
    body_audit_hash = audit_contract_hash(chapter.content_hash, expected_delta, entry)
    stage_metrics = dict(entry.get("stage_metrics") or {})
    if repair_resume:
        stage_metrics["audit"] = repair_resume["audit_metrics"]
    else:
        stage_metrics = {
            key: value
            for key, value in stage_metrics.items()
            if key not in {"audit", "local_repair"}
        }
    stage_metrics[metric_stage] = metrics
    entry.update(
        {
            "status": "audit",
            "stage": "audit",
            "chapter_business_id": chapter.business_id,
            "body_hash": chapter.content_hash,
            "audit_contract_hash": body_audit_hash,
            "audit_budget_hash": (repair_resume or {}).get("budget_hash")
            or body_audit_hash,
            "audit_reservations": (
                list(entry.get("audit_reservations") or []) if repair_resume else []
            ),
            "source_hash": novel_chapter_source_hash(chapter),
            "char_count": prose_result["char_count"],
            "blocks": prose_result["blocks"],
            "prose_context_hash": value_hash(prose_input),
            "expected_delta": expected_delta,
            "extraction_status": "pending",
            "body_repair_count": repair_count,
            "stage_metrics": stage_metrics,
        }
    )
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    chapter.review_status = "review_required"
    service.db.commit()
    return chapter, entry


def checkpoint_body(
    service,
    revision,
    position,
    chapter_plan,
    entry,
    brief,
    prose_input,
    expected_delta,
    prose_result,
    audit_result,
    metrics,
    *,
    repair_count,
    commit=True,
):
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )
    from .story_novel_plot_contract import validated_plot_delta
    from .story_novel_v3_generation import merge_stage_metrics

    revision = lock_checkpoint_entry(service, revision, position, entry)
    merged_metrics = dict(entry.get("stage_metrics") or {})
    for stage, metric in (metrics or {}).items():
        merged_metrics[stage] = merge_stage_metrics(merged_metrics.get(stage), metric)
    candidate_body_hash = sha256_text(prose_result["content_text"].strip())
    candidate_audit_hash, budget_hash, merged_metrics = prepare_checkpoint_audit(
        service.db,
        revision.business_id,
        position,
        entry,
        candidate_body_hash,
        expected_delta,
        merged_metrics,
    )
    existing = next(
        (item for item in revision.chapters if item.position == position), None
    )
    old_source = (
        capture_chapter_source_hashes([existing])[existing.business_id]
        if existing
        else None
    )
    chapter = service.checkpoint_chapter(
        revision,
        position=position,
        title=chapter_plan["title"],
        content_text=prose_result["content_text"],
        summary=brief["summary"],
        cliffhanger=brief.get("cliffhanger"),
        commit=False,
    )
    if old_source and old_source != novel_chapter_source_hash(chapter):
        invalidate_chapter_source(
            service.db,
            revision,
            chapter,
            old_source,
            force=True,
            reason_code="v3_source_hash_changed",
        )
    passed = audit_result["passed"]
    evidence_pending = (
        not passed and audit_result.get("failure_kind") == "evidence_only"
    )
    state_after = audit_result.get("state_after") if passed else None
    entry.update(
        {
            "status": (
                "memory_ready"
                if passed
                else "audit" if evidence_pending else "gate_failed"
            ),
            "stage": "memory_ready" if passed else "audit",
            "chapter_business_id": chapter.business_id,
            "body_hash": chapter.content_hash,
            "audit_contract_hash": audit_contract_hash(
                chapter.content_hash, expected_delta, entry
            ),
            "audit_budget_hash": budget_hash,
            "source_hash": novel_chapter_source_hash(chapter),
            "char_count": prose_result["char_count"],
            "blocks": prose_result["blocks"],
            "prose_context_hash": value_hash(prose_input),
            "expected_delta": expected_delta,
            "state_delta": audit_result.get("state_delta") if passed else None,
            "state_validation": audit_result["state_validation"],
            "state_after": state_after,
            "state_after_hash": state_hash(state_after) if state_after else None,
            "proof_spans": audit_result.get("proof_spans") or [],
            "sentence_index_hash": audit_result.get("sentence_index_hash"),
            "future_audit": audit_result.get("future_audit") or {},
            "body_repair_count": repair_count,
            "extraction_status": "pending" if passed or evidence_pending else "blocked",
            "audit_failure_kind": None if passed else audit_result.get("failure_kind"),
            "failed_block_ids": audit_result.get("failed_block_ids") or [],
            "plot_delta": (
                validated_plot_delta(chapter_plan, audit_result["state_delta"])
                if passed
                else None
            ),
            "plot_delta_source": "expected_delta" if passed else None,
            "plot_delta_version": 2 if passed else None,
            "stage_metrics": merged_metrics,
        }
    )
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    chapter.review_status = "ready" if passed else "review_required"
    if not passed and not evidence_pending:
        ledger = dict(revision.continuity_ledger or {})
        ledger.update(state_status="failed", stale_from_position=position)
        revision.continuity_ledger = ledger
        revision.continuity_status = "review_required"
    (service.db.commit if commit else service.db.flush)()
    return chapter, entry
