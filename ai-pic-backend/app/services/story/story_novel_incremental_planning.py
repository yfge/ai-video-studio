"""Finalize a V3 skeleton without pre-planning every chapter contract."""

from __future__ import annotations

from . import story_novel_planning_invocations as planning_invocations
from .story_novel_canon_milestone_filter import CANON_MODEL_FILTER_VERSION
from .story_novel_canon_service import CANON_GATE_VERSION
from .story_novel_incremental_plan import (
    build_chapter_skeletons,
    incremental_plan_fields,
)
from .story_novel_length_service import generation_plan_hash
from .story_novel_planning_failure import fail_plan
from .story_novel_task_guard import ensure_task_not_cancelled
from .story_novel_thread_schedule import compile_thread_payoffs
from .story_novel_thread_schedule_checkpoint import (
    checkpoint_thread_payoffs,
    reusable_thread_payoffs,
)


async def prepare_incremental_plan(
    service, revision, task, generate_text, frozen_spec: dict, canon: dict
) -> dict:
    ensure_task_not_cancelled(service.db, task)
    task.description = "Canon 编译完成，正在冻结轻量全书骨架…"
    service.db.commit()
    thread_payoffs = reusable_thread_payoffs(frozen_spec)
    if thread_payoffs is None:
        try:
            thread_payoffs = await compile_thread_payoffs(
                service.db, task, generate_text, revision, frozen_spec
            )
        except ValueError as exc:
            fail_plan(service, revision, "chapters", str(exc))
    if thread_payoffs is not None:
        checkpoint_thread_payoffs(service, revision, task, frozen_spec, thread_payoffs)
    chapters = build_chapter_skeletons(canon, frozen_spec, thread_payoffs)
    manifest = _base_manifest(revision.generation_plan or {})
    plan = {
        **frozen_spec,
        "status": "ready",
        "phase": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "canon_timeline_filter": (revision.generation_plan or {}).get(
            "canon_timeline_filter"
        ),
        "chapter_count": len(chapters),
        "target_chars": sum(int(item["target_chars"]) for item in chapters),
        "chapters": chapters,
        "thread_payoffs": list(thread_payoffs or []),
    }
    plan.update(
        incremental_plan_fields(
            canon,
            chapters,
            schema=frozen_spec.get("schema"),
            snapshot=revision.story_snapshot or {},
        )
    )
    planning_invocations.finalize(plan, canon, chapters, source_manifest=manifest)
    plan["plan_hash"] = generation_plan_hash(plan)
    for key in (
        "chapter_plan_draft",
        "chapter_plan_draft_canon_hash",
        "plan_semantic_audit_version",
        "error",
    ):
        plan.pop(key, None)
    revision.generation_plan = plan
    revision.chapter_count = len(chapters)
    revision.target_words = plan["target_chars"]
    task.description = f"轻量骨架已冻结，共 {len(chapters)} 章；开始逐章规划"
    ensure_task_not_cancelled(service.db, task)
    service.db.commit()
    return plan


def _base_manifest(plan: dict) -> dict:
    manifest = dict(plan.get("planning_invocations") or {})
    entries = [
        item
        for item in manifest.get("entries") or []
        if str(item.get("logical_stage") or "").startswith(("canon", "thread_schedule"))
    ]
    return {"schema": manifest.get("schema"), "entries": entries}
