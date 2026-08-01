"""Approval gates for immutable-snapshot generation-plan v4."""

from __future__ import annotations

import copy
import hashlib
from types import SimpleNamespace

from app.repositories.llm_invocation_repository import LLMInvocationRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_expected_delta import compile_expected_delta
from .story_novel_planner_snapshot import valid_planner_snapshot
from .story_novel_planning_invocations import valid as valid_planning_invocations
from .story_novel_prose_length_control import valid_length_control
from .story_novel_prose_length_policy import valid_length_control_policy
from .story_novel_revision_local_memory import local_memory_rows_complete
from .story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
    state_hash,
)
from .story_novel_v3_approval import _valid_blocks, _valid_proofs
from .story_novel_v3_audit import audit_contracts
from .story_novel_v3_invocation_gate import persisted_invocation_issues
from .story_novel_v3_stage_evidence import valid_invocation, valid_stage_metrics
from .story_novel_v4_call_snapshot import valid_call_snapshot
from .story_novel_v4_plan import all_arc_plans_frozen, valid_v4_plan_fields
from .story_novel_v4_planning import context_from_checkpoint
from .story_novel_v4_prose_input import build_v4_prose_input
from .story_novel_v4_snapshot_guard import source_manifest_current


def require_v4_quality(db, revision, chapters, ledger_rows) -> None:
    plan = revision.generation_plan or {}
    if not valid_v4_plan_fields(plan) or not all_arc_plans_frozen(plan):
        raise HTTPException(
            status_code=409, detail="v4 分卷计划尚未全部冻结或 hash 无效"
        )
    if not valid_planning_invocations(plan):
        raise HTTPException(status_code=409, detail="v4 规划 invocation 证据不完整")
    if not valid_length_control_policy(db, revision):
        raise HTTPException(status_code=409, detail="v4 正文长度控制策略证据不完整")
    rows = {int(item["position"]): item for item in plan.get("chapters") or []}
    state = initial_story_state(plan.get("canon") or {})
    invalid = []
    for chapter in chapters:
        entry = ledger_rows.get(str(chapter.position)) or {}
        row = rows.get(chapter.position) or {}
        issues = _entry_issues(db, revision, chapter, row, entry, state)
        if issues:
            invalid.append({"position": chapter.position, "issues": issues})
        if entry.get("state_delta"):
            state = apply_state_delta(state, entry["state_delta"])
    if not _mandatory_slots_present(plan, state):
        invalid.append({"position": 0, "issues": ["mandatory entity slots"]})
    if invalid:
        raise HTTPException(status_code=409, detail=f"v4 冻结快照门禁不完整: {invalid}")
    _review_invocations(db, revision, ledger_rows, len(chapters))


def _entry_issues(db, revision, chapter, row, entry, state_before):
    plan = revision.generation_plan or {}
    issues = []
    snapshot = entry.get("planner_snapshot") or {}
    intent = entry.get("chapter_intent") or {}
    brief = entry.get("chapter_brief") or {}
    if not valid_planner_snapshot(snapshot):
        return ["planner snapshot hash"]
    if not source_manifest_current(
        SimpleNamespace(db=db),
        revision,
        chapter.position,
        snapshot.get("source_manifest") or {},
    ):
        issues.append("planner source manifest")
    expected = compile_expected_delta(row, state_before) if row else {}
    if entry.get("expected_delta") != expected:
        issues.append("expected delta")
    if (
        snapshot.get("canon_hash") != plan.get("canon_hash")
        or snapshot.get("state_before_hash") != state_hash(state_before)
        or intent.get("snapshot_hash") != snapshot.get("snapshot_hash")
        or entry.get("chapter_intent_hash") != intent.get("intent_hash")
        or brief.get("planner_snapshot_hash") != snapshot.get("snapshot_hash")
        or entry.get("brief_hash") != brief.get("brief_hash")
        or not _self_hash(brief, "brief_hash")
    ):
        issues.append("snapshot/intent/brief chain")
    try:
        context = context_from_checkpoint(entry, row)
        prose_input = build_v4_prose_input(snapshot, intent, row, brief)
    except (KeyError, TypeError, ValueError):
        return [*issues, "snapshot execution context"]
    if (
        entry.get("context_hash") != context["evidence"]["context_hash"]
        or entry.get("prose_context_hash") != value_hash(prose_input)
        or entry.get("chapter_contract_hash")
        != value_hash(prompt_chapter_contract(row))
    ):
        issues.append("context/prose hash")
    metric = (entry.get("stage_metrics") or {}).get("prose") or {}
    call_snapshots = entry.get("model_call_snapshots") or {}
    prefixes = ["chapter_planning.", "prose.", "audit."]
    if entry.get("body_repair_count"):
        prefixes.append("local_repair.")
    if (
        not call_snapshots
        or any(
            not any(stage.startswith(prefix) for stage in call_snapshots)
            for prefix in prefixes
        )
        or any(
            not valid_call_snapshot(snapshot) for snapshot in call_snapshots.values()
        )
    ):
        issues.append("model call snapshots")
    elif not _call_snapshots_bound_to_invocations(
        db, revision, call_snapshots, entry.get("stage_metrics") or {}
    ):
        issues.append("model call snapshot invocation binding")
    if any(
        value.get("execution_generation_plan_hash")
        != entry.get("execution_generation_plan_hash")
        for stage, value in call_snapshots.items()
        if stage.startswith(("prose.", "audit.", "local_repair."))
    ):
        issues.append("model call execution plan hash")
    if not valid_length_control(db, revision, chapter.position, prose_input, metric):
        issues.append("length invocation evidence")
    if (
        entry.get("body_hash") != chapter.content_hash
        or entry.get("source_hash") != novel_chapter_source_hash(chapter)
        or not _valid_blocks(chapter.content_text, brief, entry.get("blocks") or [])
    ):
        issues.append("body/block/source hash")
    proofs = entry.get("proof_spans") or []
    required = {
        item["contract_id"]
        for item in audit_contracts(expected, plan.get("canon") or {}, row)
    }
    if {item.get("contract_id") for item in proofs} != required or not _valid_proofs(
        chapter.content_text, proofs, entry
    ):
        issues.append("proof/sentence hash")
    audit = entry.get("future_audit") or {}
    if any(
        audit.get(key)
        for key in ("future_hits", "unexpected_claims", "world_rule_hits")
    ):
        issues.append("future/world audit")
    if not valid_stage_metrics(db, revision, chapter.position, entry):
        issues.append("model invocation evidence")
    if not local_memory_rows_complete(entry):
        issues.append("revision-local memory coverage")
    return issues


def _self_hash(value: dict, key: str) -> bool:
    candidate = copy.deepcopy(value)
    stored = candidate.pop(key, None)
    return bool(stored and stored == value_hash(candidate))


def _mandatory_slots_present(plan: dict, state: dict) -> bool:
    expected = {
        item["slot_id"]
        for arc in (plan.get("arc_plans") or {}).values()
        for key in ("instantiated_character_slots", "instantiated_scope_slots")
        for item in arc.get(key) or []
        if item.get("mandatory") and item.get("slot_id")
    }
    actual = {
        (item.get("attributes") or {}).get("slot_id")
        for item in (state.get("revision_local_entities") or {}).values()
    }
    return expected.issubset(actual)


def _call_snapshots_bound_to_invocations(
    db, revision, snapshots: dict, stage_metrics: dict
) -> bool:
    repo = LLMInvocationRepository(db)
    prefix = f"story_novel.{revision.business_id}."
    for stage, snapshot in snapshots.items():
        scene = f"{prefix}{stage}"
        metric = stage_metrics.get(stage.split(".", 1)[0]) or {}
        attempt = next(
            (
                item
                for item in metric.get("attempts") or []
                if item.get("call_scene") == scene
            ),
            None,
        )
        try:
            row = repo.get_by_id(int((attempt or {}).get("invocation_id")))
        except (TypeError, ValueError):
            row = None
        response = str(getattr(row, "response", "") or "")
        if not (
            row
            and attempt.get("status") == "succeeded"
            and row.call_scene == scene
            and row.status == "succeeded"
            and value_hash(str(row.original_prompt or row.prompt or ""))
            == snapshot.get("input_hash")
            and hashlib.sha256(response.strip().encode()).hexdigest()
            == attempt.get("response_hash")
            and hashlib.sha256(response.encode()).hexdigest()
            == attempt.get("raw_response_hash")
        ):
            return False
    return True


def _review_invocations(db, revision, ledger_rows, chapter_count):
    plan = revision.generation_plan or {}
    review = revision.continuity_report or {}
    invocations = review.get("review_invocations") or []
    model = review.get("reviewer_model") or (plan.get("model_policy") or {}).get(
        "audit_model"
    )
    expected = (chapter_count + 5) // 6 + 1
    if len(invocations) != expected or any(
        not valid_invocation(item, model, require_prompt_template=True)
        for item in invocations
    ):
        raise HTTPException(status_code=409, detail="v4 连续性审读调用证据不完整")
    issues = persisted_invocation_issues(db, revision, ledger_rows, review)
    if issues:
        raise HTTPException(
            status_code=409, detail=f"v4 invocation 证据不完整: {issues}"
        )
