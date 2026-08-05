"""Durable v2 chapter checkpoints and authoritative state promotion."""

from __future__ import annotations

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_chapter_gate import chapter_length_range
from .story_novel_memory_context import (
    capture_chapter_source_hashes,
    invalidate_chapter_source,
)
from .story_novel_state_service import (
    replay_checkpoint_state,
    state_before_position,
    state_hash,
)


def checkpoint_gated_result(
    service,
    revision,
    position: int,
    result: dict,
    gated: dict,
    evidence: dict,
    existing,
):
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    old_source = (
        capture_chapter_source_hashes([existing])[existing.business_id]
        if existing
        else None
    )
    chapter = service.checkpoint_chapter(
        revision,
        position=position,
        title=result["title"],
        content_text=result["content_text"],
        summary=result["summary"],
        cliffhanger=result.get("cliffhanger"),
    )
    if old_source:
        pending = gated.get("state_extraction_evidence_only") is True
        invalidate_chapter_source(
            service.db,
            revision,
            chapter,
            old_source,
            force=not gated["passed"],
            reason_code=(
                "chapter_state_pending"
                if pending
                else (
                    "chapter_gate_failed"
                    if not gated["passed"]
                    else "source_hash_changed"
                )
            ),
        )
    entry = _ledger_entry(chapter, result, gated, evidence)
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    return chapter, entry


def _ledger_entry(chapter, result: dict, gated: dict, evidence: dict) -> dict:
    passed = gated["passed"]
    pending = gated.get("state_extraction_evidence_only") is True
    state_after = gated.get("state_after") if passed else None
    entry = {
        "status": (
            "body_ready" if passed else ("state_pending" if pending else "gate_failed")
        ),
        "chapter_business_id": chapter.business_id,
        "body_hash": chapter.content_hash,
        "source_hash": novel_chapter_source_hash(chapter),
        "char_count": gated["actual_chars"],
        "canon_hash": evidence["canon_hash"],
        "context_hash": evidence["context_hash"],
        "context_evidence": evidence,
        "state_before_hash": evidence["state_before_hash"],
        "state_after_hash": state_hash(state_after) if state_after else None,
        "state_after": state_after,
        "state_delta": gated.get("state_delta") if passed else None,
        "state_validation": gated["state_validation"],
        "plot_delta": gated.get("validated_plot_delta") if passed else None,
        "plot_delta_source": "typed_state" if passed else None,
        "plot_delta_version": 1 if passed else None,
        "body_repair_count": gated["body_repair_count"],
        "state_extraction_repair_count": gated["state_extraction_repair_count"],
        "extraction_status": "pending" if passed else "blocked",
    }
    if pending:
        entry["state_pending_reason"] = "source_evidence"
    if not passed and not pending:
        entry["gate_evidence"] = {
            "candidate_state_after_hash": (
                state_hash(gated["state_after"]) if gated.get("state_after") else None
            ),
            "candidate_state_delta": gated.get("state_delta"),
            "candidate_plot_delta": result["plot_delta"],
        }
    return entry


def pause_state_pending(
    service,
    revision,
    chapter,
    position: int,
    entry: dict,
    violations: list[dict],
    *,
    repair_count: int = 0,
) -> None:
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    entry.update(
        {
            "status": "state_pending",
            "state_pending_reason": "source_evidence",
            "state_delta": None,
            "state_after": None,
            "state_after_hash": None,
            "state_validation": {"status": "failed", "violations": violations},
            "plot_delta": None,
            "plot_delta_source": None,
            "plot_delta_version": None,
            "extraction_status": "blocked",
            "event_ids": [],
            "memory_ids": [],
            "state_extraction_repair_count": int(
                entry.get("state_extraction_repair_count") or 0
            )
            + repair_count,
        }
    )
    entry.pop("gate_evidence", None)
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    chapter.review_status = "review_required"
    ledger = dict(revision.continuity_ledger or {})
    ledger.update(state_status="failed", recovery_from_position=position)
    revision.continuity_ledger = ledger
    revision.continuity_status = "review_required"
    service.db.commit()
    message = "; ".join(item["message"] for item in violations[:3])
    raise HTTPException(
        status_code=500,
        detail=(
            f"第 {position} 章正文已保存，状态提取待恢复：{message}。"
            "继续任务只会重试状态提取，不会重写正文"
        ),
    )


def fail_gate(service, revision, chapter, position: int, plan: dict, gated: dict):
    chapter.review_status = "review_required"
    ledger = dict(revision.continuity_ledger or {})
    ledger.update(state_status="failed", stale_from_position=position)
    revision.continuity_ledger = ledger
    revision.continuity_status = "review_required"
    service.db.commit()
    minimum, _target, maximum = chapter_length_range(plan)
    message = "; ".join(
        item["message"] for item in gated["state_validation"]["violations"][:3]
    )
    raise HTTPException(
        status_code=500,
        detail=(
            f"第 {position} 章 Canon/状态门禁失败："
            f"计划范围 {minimum}–{maximum}，"
            f"实际 {gated['actual_chars']} 个非空白字符；{message}。"
            "已完成章节已保留，可从本章恢复"
        ),
    )


def finalize_state(service, revision, position: int, entry: dict) -> None:
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    state_after = replay_checkpoint_state(
        state_before_position(revision, position),
        entry,
    )
    if state_after is None:
        raise HTTPException(status_code=500, detail=f"第 {position} 章状态 hash 无效")
    entry["status"] = "ready"
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    ledger = dict(revision.continuity_ledger or {})
    recovery = int(ledger.get("recovery_from_position") or 0)
    ledger.update(
        current_state=state_after,
        state_status="failed" if recovery > position else "generating",
    )
    if recovery == position:
        ledger.pop("recovery_from_position", None)
    revision.continuity_ledger = ledger
    service.db.commit()
