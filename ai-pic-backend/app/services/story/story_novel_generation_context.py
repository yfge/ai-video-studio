"""Bounded, reproducible context packs for sequential novel chapters."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from .story_novel_candidate_context import (
    ready_prior_chapters,
    revision_local_candidates,
)
from .story_novel_context_utils import (
    CONTEXT_CHAR_BUDGET,
    add_bounded,
    frozen_story_contract,
    json_text,
    prompt_chapter_contract,
    prompt_safe_prior_ledger,
    recent_chapter_rows,
    rolling_state,
    stable_canon,
    value_hash,
)
from .story_novel_hard_context import build_hard_constraints, hard_constraints_hash
from .story_novel_memory_context import chapter_memory_context
from .story_novel_state_service import state_before_position, state_hash


def _validated_prefix(revision, position: int) -> tuple[list, dict]:
    ledger = dict(revision.continuity_ledger or {})
    ledger_rows = ledger.get("chapters") or {}
    try:
        previous = ready_prior_chapters(revision, position, strict=True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return previous, {
        key: value
        for key, value in ledger_rows.items()
        if int(key) < position and value.get("status") == "ready"
    }


def _hard_context(service, revision, position: int, chapter_plan: dict, plan: dict):
    approved_canon = stable_canon(
        chapter_memory_context(service.db, revision, position) or {}
    )
    if plan.get("schema") != "story_novel_generation_plan.v2":
        return {}, approved_canon, None, None
    try:
        state_before = state_before_position(revision, position)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    contract = prompt_chapter_contract(chapter_plan)
    hard = build_hard_constraints(
        snapshot=revision.story_snapshot or {},
        canon=plan.get("canon") or {},
        chapter_plan=contract,
        chapter_history=[
            prompt_chapter_contract(item)
            for item in plan.get("chapters") or []
            if int(item["position"]) <= position
        ],
        approved_story_canon=approved_canon,
        state_before=state_before,
    )
    if len(json_text({"hard_constraints": hard})) > CONTEXT_CHAR_BUDGET:
        raise HTTPException(
            status_code=500,
            detail=f"第 {position} 章不可截断 Canon 超过 32K 上下文预算",
        )
    return (
        {"hard_constraints": hard},
        approved_canon,
        state_before,
        hard_constraints_hash(hard),
    )


def _soft_sections(
    revision,
    previous: list,
    prior_ledger: dict,
    approved_canon: dict,
    chapter_plan: dict,
    state_before: dict | None,
    events: list[dict],
    memories: list[dict],
) -> list[tuple[str, Any]]:
    safe_prior_ledger = prompt_safe_prior_ledger(prior_ledger)
    sections = [
        ("story_contract", frozen_story_contract(revision.story_snapshot or {})),
        (
            "revision_local_canon",
            {"events": events, "character_memories": memories},
        ),
        (
            "rolling_plot_ledger",
            {
                "current_state": rolling_state(safe_prior_ledger),
                "prior_chapters": safe_prior_ledger,
            },
        ),
        (
            "recent_chapters",
            recent_chapter_rows(previous),
        ),
        (
            "previous_chapter_tail",
            previous[-1].content_text[-2400:] if previous else "",
        ),
    ]
    if state_before is None:
        sections[1:1] = [
            ("chapter_plan", prompt_chapter_contract(chapter_plan)),
            ("approved_story_canon", approved_canon),
        ]
    return sections


def _context_evidence(
    pack: dict,
    plan: dict,
    position: int,
    chapter_plan: dict,
    previous: list,
    events: list[dict],
    memories: list[dict],
    state_before: dict | None,
    hard_hash: str | None,
    truncations: list[dict],
) -> dict:
    local_canon = pack.get("revision_local_canon") or {}
    included_events = (
        local_canon.get("events") or [] if isinstance(local_canon, dict) else []
    )
    included_memories = (
        local_canon.get("character_memories") or []
        if isinstance(local_canon, dict)
        else []
    )
    return {
        "context_hash": value_hash(pack),
        "context_chars": len(json_text(pack)),
        "canon_hash": plan.get("canon_hash"),
        "hard_constraints_hash": hard_hash,
        "chapter_contract_hash": value_hash(prompt_chapter_contract(chapter_plan)),
        "outline_scope": "current_chapter_contract_only",
        "future_chapter_count_excluded": sum(
            int(item["position"]) > position for item in plan.get("chapters") or []
        ),
        "state_before_hash": state_hash(state_before) if state_before else None,
        "chapter_ids": [item.business_id for item in previous],
        "chapter_hashes": [item.content_hash for item in previous],
        "event_ids": [item["business_id"] for item in included_events],
        "event_hashes": [item["source_hash"] for item in included_events],
        "memory_ids": [item["business_id"] for item in included_memories],
        "memory_hashes": [item["source_hash"] for item in included_memories],
        "truncations": truncations,
    }


def build_chapter_context(service, revision, position: int, chapter_plan: dict) -> dict:
    """Build a <=32K character context and auditable evidence manifest."""
    plan = dict(revision.generation_plan or {})
    previous, prior_ledger = _validated_prefix(revision, position)
    pack, approved, state_before, hard_hash = _hard_context(
        service, revision, position, chapter_plan, plan
    )
    events, memories = revision_local_candidates(
        service.db, revision, position, prior_chapters=previous
    )
    sections = _soft_sections(
        revision,
        previous,
        prior_ledger,
        approved,
        chapter_plan,
        state_before,
        events,
        memories,
    )
    truncations: list[dict] = []
    for key, value in sections:
        add_bounded(pack, key, value, truncations)
    return {
        "context": pack,
        "state_before": state_before,
        "evidence": _context_evidence(
            pack,
            plan,
            position,
            chapter_plan,
            previous,
            events,
            memories,
            state_before,
            hard_hash,
            truncations,
        ),
    }
