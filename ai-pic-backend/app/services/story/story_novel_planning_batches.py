"""Bounded chapter-contract batches for providers with finite output limits."""

from __future__ import annotations

import copy

from .story_novel_plan_validator import _validate_chapter, _validation_context

PLAN_CHAPTER_BATCH_SIZE = 8
PLAN_BATCH_COMPLEXITY_BUDGET = 48
PLAN_BATCH_MIN_SIZE = 3


def chapter_batches(
    expected_positions: list[int],
    frozen_spec: dict | None = None,
    canon: dict | None = None,
) -> list[list[int]]:
    if not expected_positions:
        return [[]]
    scores = _chapter_complexity(frozen_spec, canon)
    batches, current, cost = [], [], 0
    for position in expected_positions:
        next_cost = scores.get(position, 5)
        if current and (
            len(current) >= PLAN_CHAPTER_BATCH_SIZE
            or (
                len(current) >= PLAN_BATCH_MIN_SIZE
                and cost + next_cost > PLAN_BATCH_COMPLEXITY_BUDGET
            )
        ):
            batches.append(current)
            current, cost = [], 0
        current.append(position)
        cost += next_cost
    if current:
        batches.append(current)
    return batches


def batch_contract(contract: dict, positions: list[int]) -> dict:
    if not positions:
        return contract
    result = copy.deepcopy(contract)
    seed = result.get("story_seed")
    outline = seed.get("structured_outline") if isinstance(seed, dict) else None
    if isinstance(outline, dict):
        full_rows = list(outline.get("chapters") or [])
        outline["chapters"] = _position_rows(outline.get("chapters"), positions)
    else:
        full_rows = []
    result["chapter_batch"] = {
        "positions": positions,
        "first_position": positions[0],
        "last_position": positions[-1],
        "next_boundary_anchor": _next_boundary_anchor(full_rows, positions[-1]),
    }
    return result


def batch_frozen_spec(frozen_spec: dict | None, positions: list[int]):
    if not frozen_spec or not positions:
        return frozen_spec
    return {
        **frozen_spec,
        "chapters": _position_rows(frozen_spec.get("chapters"), positions),
    }


def batch_thread_payoffs(thread_payoffs: list[dict] | None, positions: list[int]):
    if thread_payoffs is None or not positions:
        return thread_payoffs
    allowed = set(positions)
    return [
        item
        for item in thread_payoffs
        if int(item.get("payoff_position") or 0) in allowed
    ]


def validated_prefix_context(canon: dict, chapters: list[dict]) -> dict:
    context = _validation_context(canon)
    for chapter in chapters:
        _validate_chapter(chapter, context)
    if chapters:
        through = int(chapters[-1]["position"])
        missing = [
            item["id"]
            for item in canon.get("milestones") or []
            if item.get("planned_position")
            and int(item["planned_position"]) <= through
            and item["id"] not in context["seen_milestones"]
        ]
        if missing:
            raise ValueError(f"计划前缀遗漏到期里程碑: {missing}")
    return {
        "validated_through_position": (
            int(chapters[-1]["position"]) if chapters else 0
        ),
        "state": context["state"],
        "seen_event_ids": sorted(context["seen_events"]),
        "consumed_milestone_ids": sorted(context["seen_milestones"]),
        "open_thread_ids": sorted(context["open_threads"]),
    }


def reusable_plan_draft(
    current: dict,
    canon: dict,
    expected_positions: list[int],
) -> list[dict]:
    rows = current.get("chapter_plan_draft")
    if not isinstance(rows, list) or current.get(
        "chapter_plan_draft_canon_hash"
    ) != canon.get("canon_hash"):
        return []
    positions = [int(item.get("position") or 0) for item in rows]
    if positions != expected_positions[: len(positions)]:
        return []
    try:
        validated_prefix_context(canon, rows)
    except (KeyError, TypeError, ValueError):
        return []
    return copy.deepcopy(rows)


def checkpoint_plan_batch(service, revision, task, canon, chapters) -> None:
    revision.generation_plan = {
        **dict(revision.generation_plan or {}),
        "chapter_plan_draft": copy.deepcopy(chapters),
        "chapter_plan_draft_canon_hash": canon["canon_hash"],
    }
    task.description = f"章节合同已验证 {len(chapters)} 章，继续规划…"
    service.db.commit()


def _position_rows(rows, positions: list[int]) -> list[dict]:
    allowed = set(positions)
    return [
        copy.deepcopy(item)
        for item in rows or []
        if int(item.get("position") or 0) in allowed
    ]


def _chapter_complexity(frozen_spec, canon) -> dict[int, int]:
    rows = (frozen_spec or {}).get("chapters") or []
    milestone_counts: dict[int, int] = {}
    timeline_counts: dict[int, int] = {}
    for item in (canon or {}).get("milestones") or []:
        position = int(item.get("planned_position") or 0)
        milestone_counts[position] = milestone_counts.get(position, 0) + 1
    for item in (canon or {}).get("timeline") or []:
        position = int(item.get("source_chapter_position") or 0)
        timeline_counts[position] = timeline_counts.get(position, 0) + 1
    return {
        int(row["position"]): (
            3
            + len(row.get("key_events") or [])
            + min(2, len(row.get("character_focus") or []))
            + len(row.get("open_threads") or [])
            + milestone_counts.get(int(row["position"]), 0)
            + timeline_counts.get(int(row["position"]), 0)
        )
        for row in rows
    }


def _next_boundary_anchor(rows: list[dict], last_position: int) -> dict | None:
    row = next(
        (item for item in rows if int(item.get("position") or 0) > last_position),
        None,
    )
    if not row:
        return None
    return {
        "position": int(row["position"]),
        "title": row.get("title"),
        "goal": row.get("goal"),
        "first_key_event": (row.get("key_events") or [None])[0],
    }
