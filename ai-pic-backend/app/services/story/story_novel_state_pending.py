"""Fail-closed validation and extraction-only recovery for saved chapter bodies."""

from __future__ import annotations

from .story_novel_chapter_checkpoint import (
    fail_gate,
    finalize_state,
    pause_state_pending,
)
from .story_novel_chapter_gate import extract_and_validate_chapter_state
from .story_novel_context_utils import prompt_chapter_contract
from .story_novel_plot_contract import validated_plot_delta
from .story_novel_state_extraction import StateExtractionError
from .story_novel_state_service import state_hash


async def resume_pending_state(
    service,
    revision,
    task,
    position: int,
    chapter,
    entry: dict,
    context_pack: dict,
    plan: dict,
    generate_text,
):
    from .story_novel_chapter_service import ensure_chapter_extraction
    from .story_novel_task_guard import ensure_task_not_cancelled

    task.description = f"第 {position} 章正文已保存，正在恢复状态提取…"
    service.db.commit()
    try:
        delta, repairs, state_after, violations = (
            await extract_and_validate_chapter_state(
                revision,
                {"content_text": chapter.content_text},
                plan,
                context_pack,
                generate_text,
            )
        )
    except StateExtractionError as exc:
        ensure_task_not_cancelled(service.db, task)
        violations = [{"code": "canon_violation", "message": str(exc)}]
        if exc.evidence_only:
            pause_state_pending(
                service,
                revision,
                chapter,
                position,
                entry,
                violations,
                repair_count=exc.repair_count,
            )
        _fail_pending_state(
            service,
            revision,
            chapter,
            position,
            plan,
            entry,
            violations,
            repair_count=exc.repair_count,
        )
    except ValueError as exc:
        _fail_pending_state(
            service,
            revision,
            chapter,
            position,
            plan,
            entry,
            [{"code": "canon_violation", "message": str(exc)}],
        )
    ensure_task_not_cancelled(service.db, task)
    if violations:
        _fail_pending_state(
            service,
            revision,
            chapter,
            position,
            plan,
            entry,
            violations,
            repair_count=repairs,
        )
    entry = checkpoint_validated_state(
        service,
        revision,
        chapter,
        position,
        entry,
        state_delta=delta,
        state_after=state_after,
        plot_delta=validated_plot_delta(prompt_chapter_contract(plan), delta),
        repair_count=repairs,
    )
    task.description = f"第 {position} 章状态有效，正在校验事实与记忆…"
    service.db.commit()
    entry = await ensure_chapter_extraction(service, revision, chapter, task)
    finalize_state(service, revision, position, entry)
    return chapter


def checkpoint_validated_state(
    service,
    revision,
    chapter,
    position: int,
    entry: dict,
    *,
    state_delta: dict,
    state_after: dict,
    plot_delta: dict,
    repair_count: int,
) -> dict:
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    entry.update(
        {
            "status": "body_ready",
            "state_delta": state_delta,
            "state_after": state_after,
            "state_after_hash": state_hash(state_after),
            "state_validation": {"status": "passed", "violations": []},
            "plot_delta": plot_delta,
            "plot_delta_source": "typed_state",
            "plot_delta_version": 1,
            "extraction_status": "pending",
            "state_extraction_repair_count": int(
                entry.get("state_extraction_repair_count") or 0
            )
            + repair_count,
        }
    )
    entry.pop("state_pending_reason", None)
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    chapter.review_status = "ready"
    service.db.commit()
    return entry


def _fail_pending_state(
    service,
    revision,
    chapter,
    position: int,
    plan: dict,
    entry: dict,
    violations: list[dict],
    *,
    repair_count: int = 0,
) -> None:
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    validation = {"status": "failed", "violations": violations}
    entry.update(
        status="gate_failed",
        state_validation=validation,
        state_extraction_repair_count=int(
            entry.get("state_extraction_repair_count") or 0
        )
        + repair_count,
    )
    entry.pop("state_pending_reason", None)
    save_ledger_entry(revision, position, entry)
    sync_plan_chapter_runtime(revision, position, entry)
    ledger = dict(revision.continuity_ledger or {})
    ledger.pop("recovery_from_position", None)
    revision.continuity_ledger = ledger
    fail_gate(
        service,
        revision,
        chapter,
        position,
        plan,
        {"actual_chars": entry["char_count"], "state_validation": validation},
    )
