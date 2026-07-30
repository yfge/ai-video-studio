"""Targeted one-shot repair for invalid thread payoff rows."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_plan_quality import MAX_PAYOFFS_PER_CHAPTER
from .story_novel_prompt_renderer import render_novel_prompt


def extracted_schedule_rows(text: str) -> list[dict]:
    payload = extract_json_block(text)
    if not isinstance(payload, dict):
        return []
    rows = payload.get("thread_payoffs")
    return rows if isinstance(rows, list) else []


def repair_conflict_ids(rows: list[dict], contract: list[dict]) -> list[str]:
    opened = {
        thread_id: chapter["position"]
        for chapter in contract
        for thread_id in chapter["open_threads"]
    }
    events = {chapter["position"]: chapter["key_events"] for chapter in contract}
    conflicts: set[str] = set()
    seen: set[str] = set()
    candidates: list[tuple[str, int, str]] = []
    malformed = False
    for row in rows:
        if not isinstance(row, dict):
            malformed = True
            continue
        thread_id = row.get("thread_id")
        if thread_id not in opened:
            continue
        if thread_id in seen:
            conflicts.add(thread_id)
        seen.add(thread_id)
        payoff = row.get("payoff_position")
        if type(payoff) is not int or payoff not in events:
            conflicts.add(thread_id)
            continue
        if payoff <= opened[thread_id]:
            conflicts.add(thread_id)
        evidence = row.get("evidence_key_event")
        if evidence not in events[payoff]:
            conflicts.add(thread_id)
        candidates.append((thread_id, payoff, evidence))
    conflicts.update(set(opened) - seen)
    threads_by_position: dict[int, list[str]] = {}
    for thread_id, payoff, evidence in candidates:
        if thread_id in conflicts:
            continue
        threads_by_position.setdefault(payoff, []).append(thread_id)
    for thread_ids in threads_by_position.values():
        conflicts.update(thread_ids[MAX_PAYOFFS_PER_CHAPTER:])
    if malformed:
        conflicts.update(opened)
    return [thread_id for thread_id in opened if thread_id in conflicts]


def thread_schedule_repair_prompt(
    error: str | None,
    conflict_ids: list[str],
    contract: list[dict],
    original_rows: list[dict],
) -> str:
    context = _repair_context(conflict_ids, contract, original_rows)
    template = {
        "thread_payoff_repairs": [
            {
                "thread_id": thread_id,
                "payoff_position": 0,
                "evidence_key_event": "目标章 key_events 原文",
            }
            for thread_id in conflict_ids
        ]
    }
    return render_novel_prompt(
        "story_novel_thread_schedule_repair_v3",
        max_payoffs_per_chapter=MAX_PAYOFFS_PER_CHAPTER,
        repair_template_json=canonical_json(template),
        repair_context_json=canonical_json(context),
        validation_error=error or "伏笔回收调度无效",
    )


def _repair_context(
    conflict_ids: list[str], contract: list[dict], original_rows: list[dict]
) -> dict:
    opened = {
        thread_id: chapter["position"]
        for chapter in contract
        for thread_id in chapter["open_threads"]
    }
    conflicts = set(conflict_ids)
    previous = {
        row.get("thread_id"): row
        for row in original_rows
        if isinstance(row, dict) and row.get("thread_id") in conflicts
    }
    occupied: dict[int, int] = {}
    for row in original_rows:
        if (
            not isinstance(row, dict)
            or row.get("thread_id") not in opened
            or row.get("thread_id") in conflicts
        ):
            continue
        payoff = row.get("payoff_position")
        if type(payoff) is int:
            occupied[payoff] = occupied.get(payoff, 0) + 1
    chapters = [
        {
            "position": chapter["position"],
            "title": chapter.get("title") or "",
            "available_slots": (
                MAX_PAYOFFS_PER_CHAPTER - occupied.get(chapter["position"], 0)
            ),
            "key_events": chapter["key_events"],
        }
        for chapter in contract
        if MAX_PAYOFFS_PER_CHAPTER - occupied.get(chapter["position"], 0) > 0
    ]
    return {
        "authoritative_conflict_thread_ids": conflict_ids,
        "conflicts": [
            {
                "thread_id": thread_id,
                "open_position": opened[thread_id],
                "previous_assignment": previous.get(thread_id),
            }
            for thread_id in conflict_ids
        ],
        "candidate_chapters": chapters,
    }


def merge_schedule_repairs(
    original_rows: list[dict],
    repair_text: str,
    contract: list[dict],
    conflict_ids: list[str],
) -> list[dict]:
    payload = extract_json_block(repair_text)
    repairs = (
        payload.get("thread_payoff_repairs") if isinstance(payload, dict) else None
    )
    if not isinstance(repairs, list):
        raise ValueError("伏笔调度修复必须返回 thread_payoff_repairs 数组")
    repair_map = {
        row.get("thread_id"): row
        for row in repairs
        if isinstance(row, dict) and row.get("thread_id")
    }
    if len(repair_map) != len(repairs) or set(repair_map) != set(conflict_ids):
        raise ValueError("伏笔调度修复必须逐项且仅覆盖全部冲突 thread_id")
    opened = [
        thread_id
        for chapter in contract
        for thread_id in chapter.get("open_threads") or []
    ]
    original_map = {
        row.get("thread_id"): row
        for row in original_rows
        if isinstance(row, dict)
        and row.get("thread_id") in opened
        and row.get("thread_id") not in conflict_ids
    }
    return [
        repair_map.get(thread_id) or original_map[thread_id] for thread_id in opened
    ]
