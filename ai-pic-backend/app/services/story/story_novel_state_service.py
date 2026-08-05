"""State replay, hashing, application, and metrics for long-form novels."""

from __future__ import annotations

import copy
from typing import Any

from .story_novel_canon_service import content_hash
from .story_novel_initial_state import (
    apply_subject_movement,
    apply_subject_transition,
    canonical_initial_subjects,
)
from .story_novel_scope_graph import initial_scope_graph
from .story_novel_world_expansion import apply_entity_introductions

HARD_METRIC_CODES = {
    "canon_violation": "canon_violation_count",
    "state_reversion": "state_reversion_count",
    "duplicate_milestone": "duplicate_milestone_count",
    "illegal_knowledge": "illegal_knowledge_count",
    "unexplained_location": "unexplained_location_transition_count",
}
REQUIRED_HARD_METRICS = frozenset(HARD_METRIC_CODES.values()) | {
    "hard_constraint_truncation_count",
    "overdue_open_thread_count",
}


def initial_story_state(canon: dict) -> dict:
    result = {
        "subjects": canonical_initial_subjects(canon),
        "occurred_event_ids": [],
        "completed_milestone_ids": [],
        "threads": {},
    }
    graph = initial_scope_graph(canon)
    if graph:
        result["scope_graph"] = graph
    return result


def state_hash(state: dict) -> str:
    return content_hash(state)


def replay_checkpoint_state(state_before: dict, entry: dict) -> dict | None:
    """Return the replayed state only when every stored state proof matches."""
    delta = entry.get("state_delta")
    stored_after = entry.get("state_after")
    if (
        not isinstance(delta, dict)
        or not isinstance(stored_after, dict)
        or entry.get("state_before_hash") != state_hash(state_before)
    ):
        return None
    replayed = apply_state_delta(state_before, delta)
    if stored_after != replayed or entry.get("state_after_hash") != state_hash(
        replayed
    ):
        return None
    return replayed


def state_before_position(revision, position: int) -> dict:
    plan = dict(revision.generation_plan or {})
    canon = dict(plan.get("canon") or {})
    state = initial_story_state(canon)
    rows = (revision.continuity_ledger or {}).get("chapters") or {}
    for prior_position in range(1, position):
        key = str(prior_position)
        entry = rows.get(key)
        if (
            not entry
            or entry.get("status") != "ready"
            or entry.get("canon_hash") != canon.get("canon_hash")
            or not entry.get("state_delta")
        ):
            raise ValueError(f"第 {key} 章状态前缀不完整")
        before_hash = state_hash(state)
        after = apply_state_delta(state, entry["state_delta"])
        if (
            (entry.get("state_validation") or {}).get("status") != "passed"
            or entry.get("state_before_hash") != before_hash
            or entry.get("state_after_hash") != state_hash(after)
        ):
            raise ValueError(f"第 {key} 章状态 hash 前缀无效")
        state = after
    return state


def apply_state_delta(state_before: dict, delta: dict) -> dict:
    state = copy.deepcopy(state_before)
    apply_entity_introductions(state, delta.get("entity_introductions") or [])
    subjects = state.setdefault("subjects", {})
    for transition in delta.get("state_transitions") or []:
        apply_subject_transition(
            subjects,
            transition["subject_id"],
            transition["field"],
            transition["to_value"],
        )
    for movement in delta.get("location_transitions") or []:
        apply_subject_movement(
            subjects, movement["subject_id"], movement["to_location_id"]
        )
    for grant in delta.get("knowledge_grants") or []:
        knowledge = subjects.setdefault(grant["character_id"], {}).setdefault(
            "knowledge", []
        )
        if grant["fact_id"] not in knowledge:
            knowledge.append(grant["fact_id"])
    _extend_unique(
        state.setdefault("occurred_event_ids", []), delta.get("occurred_event_ids")
    )
    _extend_unique(
        state.setdefault("completed_milestone_ids", []),
        delta.get("milestones_consumed"),
    )
    threads = state.setdefault("threads", {})
    for thread_id in delta.get("opened_thread_ids") or []:
        threads[thread_id] = "open"
    for thread_id in delta.get("resolved_thread_ids") or []:
        threads[thread_id] = "resolved"
    return state


def quality_metrics(revision) -> dict:
    rows = (revision.continuity_ledger or {}).get("chapters") or {}
    metrics = {name: 0 for name in HARD_METRIC_CODES.values()}
    repairs = 0
    for entry in rows.values():
        repairs += int(entry.get("body_repair_count") or 0)
        for item in (entry.get("state_validation") or {}).get("violations") or []:
            metric = HARD_METRIC_CODES.get(item.get("code"))
            if metric:
                metrics[metric] += 1
    metrics["hard_constraint_truncation_count"] = sum(
        1
        for entry in rows.values()
        for item in (entry.get("context_evidence") or {}).get("truncations") or []
        if item.get("section") == "hard_constraints"
    )
    final_state = (revision.continuity_ledger or {}).get("current_state") or {}
    due = {
        thread_id
        for chapter in (revision.generation_plan or {}).get("chapters") or []
        for thread_id in chapter.get("payoffs_due") or []
    }
    metrics["overdue_open_thread_count"] = sum(
        1
        for key, status in (final_state.get("threads") or {}).items()
        if status == "open" and key in due
    )
    chapter_count = max(1, int(revision.chapter_count or len(rows) or 1))
    return {**metrics, "chapter_repair_rate": round(repairs / chapter_count, 4)}


def get_state_value(value: dict, path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _extend_unique(target: list, values) -> None:
    for value in values or []:
        if value not in target:
            target.append(value)
