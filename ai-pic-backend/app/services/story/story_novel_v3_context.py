"""Future-isolated planning and prose inputs for generation-plan v3."""

from __future__ import annotations

from fastapi import HTTPException

from .story_novel_brief_policy import LEGACY_BRIEF_POLICY_VERSION
from .story_novel_candidate_context import (
    ready_prior_chapters,
    revision_local_candidates,
)
from .story_novel_chapter_brief_contract import compile_chapter_brief_input
from .story_novel_context_utils import (
    CONTEXT_CHAR_BUDGET,
    json_text,
    prompt_chapter_contract,
    prompt_safe_prior_ledger,
    recent_chapter_rows,
    stable_canon,
    value_hash,
)
from .story_novel_hard_context import build_hard_constraints, hard_constraints_hash
from .story_novel_memory_context import chapter_memory_context
from .story_novel_planning_evidence import rank_planning_evidence
from .story_novel_state_service import state_before_position, state_hash
from .story_novel_v3_prose_input import build_v3_prose_input as build_v3_prose_input


def build_v3_planning_context(
    service_or_db,
    revision,
    position: int,
    chapter_plan: dict,
    *,
    persist_memory_snapshots: bool = True,
):
    db = getattr(service_or_db, "db", service_or_db)
    plan = dict(revision.generation_plan or {})
    try:
        previous = ready_prior_chapters(revision, position, strict=True)
        state_before = state_before_position(revision, position)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    approved = stable_canon(
        chapter_memory_context(
            db,
            revision,
            position,
            persist_snapshots=persist_memory_snapshots,
        )
        or {}
    )
    contract = prompt_chapter_contract(chapter_plan)
    history = [contract]
    hard = build_hard_constraints(
        snapshot=revision.story_snapshot or {},
        canon=plan.get("canon") or {},
        chapter_plan=contract,
        chapter_history=history,
        approved_story_canon=approved,
        state_before=state_before,
    )
    base = {"hard_constraints": hard}
    if len(json_text(base)) > CONTEXT_CHAR_BUDGET:
        raise HTTPException(
            status_code=500,
            detail=f"第 {position} 章不可截断 Canon 超过 32K 上下文预算",
        )
    events, memories = revision_local_candidates(
        db, revision, position, prior_chapters=previous
    )
    events = rank_planning_evidence(
        events,
        kind="world_event",
        chapter_contract=contract,
        canon=plan.get("canon") or {},
        prior_chapters=previous,
    )
    memories = rank_planning_evidence(
        memories,
        kind="character_memory",
        chapter_contract=contract,
        canon=plan.get("canon") or {},
        prior_chapters=previous,
    )
    truncations: list[dict] = []
    _add_rows(base, "recent_chapters", recent_chapter_rows(previous), truncations)
    tail = previous[-1].content_text[-2400:] if previous else ""
    _add_tail(base, tail, truncations)
    prior_ledger = prompt_safe_prior_ledger(
        {
            key: value
            for key, value in (
                (revision.continuity_ledger or {}).get("chapters") or {}
            ).items()
            if int(key) < position and value.get("status") == "ready"
        }
    )
    _add_ledger(base, prior_ledger, truncations)
    _add_rows(base, "world_events", events, truncations)
    _add_rows(base, "character_memories", memories, truncations)
    allowed_ids = [
        item["id"] for item in (hard.get("compiled_canon") or {}).get("entities") or []
    ]
    brief_input = compile_chapter_brief_input(
        chapter_contract=contract,
        state_before=state_before,
        world_events=base.get("world_events") or [],
        character_memories=base.get("character_memories") or [],
        allowed_entity_ids=allowed_ids,
        brief_policy_version=plan.get("brief_policy_version")
        or LEGACY_BRIEF_POLICY_VERSION,
    )
    if plan.get("prose_execution_boundary_version"):
        brief_input["prose_execution_boundary_version"] = int(
            plan["prose_execution_boundary_version"]
        )
    brief_input.update(
        hard_constraints=hard,
        recent_chapters=base["recent_chapters"],
        previous_chapter_tail=base["previous_chapter_tail"],
        prior_ledger=base["prior_ledger"],
    )
    evidence = {
        "context_hash": value_hash(brief_input),
        "context_chars": len(json_text(brief_input)),
        "canon_hash": plan.get("canon_hash"),
        "hard_constraints_hash": hard_constraints_hash(hard),
        "chapter_contract_hash": value_hash(contract),
        "state_before_hash": state_hash(state_before),
        "chapter_ids": [item.business_id for item in previous],
        "chapter_hashes": [item.content_hash for item in previous],
        "event_ids": [item["business_id"] for item in base.get("world_events") or []],
        "event_hashes": [
            item["source_hash"] for item in base.get("world_events") or []
        ],
        "memory_ids": [
            item["business_id"] for item in base.get("character_memories") or []
        ],
        "memory_hashes": [
            item["source_hash"] for item in base.get("character_memories") or []
        ],
        "future_chapter_count_excluded": sum(
            int(item["position"]) > position for item in plan.get("chapters") or []
        ),
        "truncations": truncations,
    }
    return {
        "brief_input": brief_input,
        "state_before": state_before,
        "hard_constraints": hard,
        "evidence": evidence,
    }


def _add_rows(pack: dict, key: str, rows, truncations: list[dict]) -> None:
    source = list(rows or [])
    kept = []
    for item in source:
        if len(json_text({**pack, key: [*kept, item]})) > CONTEXT_CHAR_BUDGET:
            break
        kept.append(item)
    pack[key] = kept
    if len(kept) != len(source):
        truncations.append(
            {"section": key, "original_items": len(source), "kept_items": len(kept)}
        )


def _add_ledger(pack: dict, rows: dict, truncations: list[dict]) -> None:
    kept = {}
    ordered = sorted(rows, key=int, reverse=True)
    for key in ordered:
        candidate = {**kept, key: rows[key]}
        if len(json_text({**pack, "prior_ledger": candidate})) > CONTEXT_CHAR_BUDGET:
            break
        kept[key] = rows[key]
    pack["prior_ledger"] = dict(sorted(kept.items(), key=lambda item: int(item[0])))
    if len(kept) != len(rows):
        truncations.append(
            {
                "section": "prior_ledger",
                "original_items": len(rows),
                "kept_items": len(kept),
            }
        )


def _add_tail(pack: dict, tail: str, truncations: list[dict]) -> None:
    low, high, kept = 0, len(tail), ""
    while low <= high:
        middle = (low + high) // 2
        candidate = tail[-middle:] if middle else ""
        if (
            len(json_text({**pack, "previous_chapter_tail": candidate}))
            <= CONTEXT_CHAR_BUDGET
        ):
            kept = candidate
            low = middle + 1
        else:
            high = middle - 1
    pack["previous_chapter_tail"] = kept
    if len(kept) != len(tail):
        truncations.append(
            {
                "section": "previous_chapter_tail",
                "original_chars": len(tail),
                "kept_chars": len(kept),
            }
        )
