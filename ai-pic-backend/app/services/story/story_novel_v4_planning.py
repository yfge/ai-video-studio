"""Persist snapshot, call planner, then compile one v4 chapter contract."""

from __future__ import annotations

import copy
from types import SimpleNamespace

from . import story_novel_planning_invocations as planning_invocations
from .story_novel_chapter_contract_v4 import compile_intent_contract
from .story_novel_chapter_service import save_ledger_entry
from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_incremental_plan import chapter_skeleton, compiled_count
from .story_novel_length_service import generation_plan_hash
from .story_novel_planner_snapshot import build_planner_snapshot, valid_planner_snapshot
from .story_novel_v3_checkpoint import checkpoint_brief
from .story_novel_v4_call_snapshot import (
    archive_failed_chapter_planning_calls,
    freeze_v4_call_input,
)
from .story_novel_v4_generation import generate_chapter_intent
from .story_novel_v4_plan_reset import mark_snapshot_stale
from .story_novel_v4_snapshot_guard import lock_current_snapshot_source
from .story_novel_world_reveal import compile_world_reveal_index


async def prepare_v4_chapter(
    service, revision, position: int, skeleton: dict, entry: dict, generate_text
):
    plan = dict(revision.generation_plan or {})
    if position != compiled_count(plan) + 1:
        raise ValueError("v4 章节合同只能按连续章节顺序编译")
    snapshot = _stored_snapshot(entry, position, skeleton)
    if entry.get("planner_snapshot") and snapshot is None:
        mark_snapshot_stale(
            service, revision, position, "planner snapshot hash invalid"
        )
        raise ValueError("v4 planner snapshot 无效，拒绝静默重建")
    if snapshot is None:
        snapshot = build_planner_snapshot(service, revision, position, skeleton)
        entry = checkpoint_snapshot(service, revision, position, entry, snapshot)
    else:
        revision = lock_current_snapshot_source(service, revision, snapshot)
    if archive_failed_chapter_planning_calls(entry, position):
        save_ledger_entry(revision, position, entry)
        service.db.commit()
    intent, metrics = await generate_chapter_intent(
        revision,
        position,
        snapshot,
        generate_text,
        before_call=lambda stage, prompt: freeze_v4_call_input(
            service, revision, position, entry, stage, prompt
        ),
    )
    revision = lock_current_snapshot_source(service, revision, snapshot)
    contract, brief, expected_delta = compile_intent_contract(
        skeleton, intent, snapshot, plan.get("canon") or {}
    )
    context = _execution_context(snapshot, contract, expected_delta)
    _checkpoint_contract_plan(revision, position, contract, metrics)
    entry.update(
        planner_snapshot=snapshot,
        planner_snapshot_hash=snapshot["snapshot_hash"],
        execution_generation_plan_hash=(revision.generation_plan or {}).get(
            "plan_hash"
        ),
        chapter_intent=intent,
        chapter_intent_hash=intent["intent_hash"],
        expected_delta=expected_delta,
        proof_contract_schema="story_novel_audit_proof.v2",
    )
    entry = checkpoint_brief(
        service, revision, position, entry, context, brief, metrics
    )
    return contract, brief, context, entry, snapshot, intent


def checkpoint_snapshot(service, revision, position, entry, snapshot):
    entry.update(
        {
            "status": "chapter_planning",
            "stage": "planner_snapshot_ready",
            "planner_snapshot": snapshot,
            "planner_snapshot_hash": snapshot["snapshot_hash"],
            "context_hash": snapshot["snapshot_hash"],
            "canon_hash": snapshot["canon_hash"],
            "chapter_contract_hash": snapshot["chapter_contract_hash"],
            "state_before_hash": snapshot["state_before_hash"],
            "source_manifest": snapshot["source_manifest"],
        }
    )
    save_ledger_entry(revision, position, entry)
    service.db.commit()
    return entry


def reusable_v4_package(entry: dict, position: int):
    snapshot = entry.get("planner_snapshot")
    intent = entry.get("chapter_intent")
    brief = entry.get("chapter_brief")
    if (
        not valid_planner_snapshot(snapshot)
        or int(snapshot.get("position") or 0) != position
        or not isinstance(intent, dict)
        or intent.get("snapshot_hash") != snapshot["snapshot_hash"]
        or entry.get("chapter_intent_hash") != intent.get("intent_hash")
        or not isinstance(brief, dict)
        or brief.get("planner_snapshot_hash") != snapshot["snapshot_hash"]
    ):
        return None
    return snapshot, intent, brief


def context_from_checkpoint(entry: dict, contract: dict) -> dict:
    package = reusable_v4_package(entry, int(contract["position"]))
    if package is None:
        raise ValueError("v4 planner snapshot/intent checkpoint 无效")
    snapshot, _intent, _brief = package
    expected = entry.get("expected_delta")
    if not isinstance(expected, dict):
        raise ValueError("v4 expected delta checkpoint 缺失")
    return _execution_context(snapshot, contract, expected)


def _stored_snapshot(entry: dict, position: int, skeleton: dict):
    snapshot = entry.get("planner_snapshot")
    if not valid_planner_snapshot(snapshot):
        return None
    if int(snapshot.get("position") or 0) != position or snapshot.get(
        "chapter_contract_hash"
    ) != value_hash(chapter_skeleton(skeleton)):
        return None
    return snapshot


def _execution_context(snapshot: dict, contract: dict, expected_delta: dict) -> dict:
    context = copy.deepcopy(snapshot["execution_context"])
    frozen_contract = prompt_chapter_contract(contract)
    brief_input = context["brief_input"]
    brief_input.update(
        chapter_contract=copy.deepcopy(frozen_contract),
        chapter_contract_hash=value_hash(frozen_contract),
        expected_delta=copy.deepcopy(expected_delta),
        state_before_hash=snapshot["state_before_hash"],
        input_evidence_hash=value_hash(snapshot["source_manifest"]),
    )
    evidence = context["evidence"]
    evidence.update(
        chapter_contract_hash=value_hash(frozen_contract),
        context_hash=value_hash(brief_input),
        planner_snapshot_hash=snapshot["snapshot_hash"],
    )
    return context


def _checkpoint_contract_plan(revision, position, contract, metrics) -> None:
    plan = dict(revision.generation_plan or {})
    rows = [dict(item) for item in plan.get("chapters") or []]
    rows[position - 1] = contract
    reveal = compile_world_reveal_index(plan.get("canon") or {}, rows)
    plan.update(
        chapters=rows,
        compiled_chapter_count=position,
        world_reveal_index=reveal,
        world_reveal_hash=reveal["index_hash"],
    )
    final_attempt = (metrics.get("attempts") or [])[-1]
    candidate = SimpleNamespace(generation_plan=plan)
    planning_invocations.record_attempt(
        candidate,
        f"chapter_package.{position}",
        final_attempt,
        positions=[position],
        result_hash=value_hash([prompt_chapter_contract(contract)]),
    )
    plan = dict(candidate.generation_plan or {})
    planning_invocations.finalize(
        plan,
        plan.get("canon") or {},
        rows,
        source_manifest=plan.get("planning_invocations") or {},
    )
    if not planning_invocations.valid(plan):
        raise ValueError("v4 章前规划调用证据与冻结计划不一致")
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
