"""Bounded chapter-contract batches for providers with finite output limits."""

from __future__ import annotations

import copy

from .story_novel_domain import json_prompt_payload
from .story_novel_plan_validator import _validate_chapter, _validation_context

PLAN_CHAPTER_BATCH_SIZE = 8


def chapter_batches(expected_positions: list[int]) -> list[list[int]]:
    if not expected_positions:
        return [[]]
    return [
        expected_positions[index : index + PLAN_CHAPTER_BATCH_SIZE]
        for index in range(0, len(expected_positions), PLAN_CHAPTER_BATCH_SIZE)
    ]


def batch_contract(contract: dict, positions: list[int]) -> dict:
    if not positions:
        return contract
    result = copy.deepcopy(contract)
    seed = result.get("story_seed")
    outline = seed.get("structured_outline") if isinstance(seed, dict) else None
    if isinstance(outline, dict):
        outline["chapters"] = _position_rows(outline.get("chapters"), positions)
    result["chapter_batch"] = {
        "positions": positions,
        "first_position": positions[0],
        "last_position": positions[-1],
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


def planning_batch_prompt(
    prompt: str,
    positions: list[int],
    canon: dict,
    prior_chapters: list[dict],
) -> str:
    if not positions:
        return prompt
    prefix = validated_prefix_context(canon, prior_chapters)
    return (
        prompt
        + "\n\n本次是有界章节合同批次，只输出严格 JSON object，chapters 必须且只能"
        f"覆盖第 {positions[0]}–{positions[-1]} 章，精确 positions={positions}。"
        "不得复读已验证前缀，不得输出本批次之后的章节。"
        "\n以下 prefix_context 是此前批次经确定性验证后的唯一状态起点；"
        "所有 from_value、preconditions、事件 ID、里程碑和伏笔必须从这里连续推进："
        f"{json_prompt_payload(prefix)}"
    )


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
    return rows


def checkpoint_plan_batch(service, revision, task, canon, chapters) -> None:
    revision.generation_plan = {
        **dict(revision.generation_plan or {}),
        "chapter_plan_draft": chapters,
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
