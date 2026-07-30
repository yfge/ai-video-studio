"""Prompt for Canon-backed long-form chapter contract planning."""

from __future__ import annotations

from typing import Any

from .story_novel_domain import json_prompt_payload
from .story_novel_location_rules import (
    ABSENT_OBJECT_STATUS_LITERALS,
    TERMINAL_OBJECT_STATUS_LITERALS,
)
from .story_novel_prompt_renderer import render_novel_prompt


def planning_prompt(
    *,
    planning_contract: dict[str, Any],
    canon: dict,
    thread_payoffs: list[dict] | None = None,
    batch_positions: list[int] | None = None,
    prefix_context: dict | None = None,
) -> str:
    absence_literals = "、".join(
        f'"{value}"' for value in ABSENT_OBJECT_STATUS_LITERALS
    )
    terminal_literals = "、".join(
        f'"{value}"' for value in TERMINAL_OBJECT_STATUS_LITERALS
    )
    schedule = (
        "未提供冻结伏笔调度，按章节合同自行规划。"
        if thread_payoffs is None
        else "以下机器校验后的 thread_payoffs 是唯一权威，逐章 payoffs_due 必须按 "
        "payoff_position 精确复制 thread_id，不得遗漏、重排或另行推断："
        f"{json_prompt_payload(thread_payoffs)}"
    )
    return render_novel_prompt(
        "story_novel_plan_v3",
        planning_contract_json=json_prompt_payload(planning_contract),
        canon_json=json_prompt_payload(canon),
        thread_schedule=schedule,
        absence_literals=absence_literals,
        terminal_literals=terminal_literals,
        batch_positions_json=(
            json_prompt_payload(batch_positions) if batch_positions else ""
        ),
        batch_start=batch_positions[0] if batch_positions else None,
        batch_end=batch_positions[-1] if batch_positions else None,
        prefix_context_json=(
            json_prompt_payload(prefix_context) if prefix_context is not None else ""
        ),
    )
