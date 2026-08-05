"""Compile the only state delta an audited v3 chapter may apply."""

from __future__ import annotations

import copy

from .story_novel_context_utils import value_hash

EXPECTED_DELTA_SCHEMA = "story_novel_expected_delta.v1"


def compile_expected_delta(chapter_plan: dict, state_before: dict) -> dict:
    """Compile plan-owned effects without accepting model-authored state."""
    if not isinstance(chapter_plan, dict) or not isinstance(state_before, dict):
        raise ValueError("chapter_plan 和 state_before 必须是对象")
    events = _unique_strings(chapter_plan.get("required_event_ids"), "事件")
    state = _dict_rows(chapter_plan.get("state_transitions"), "状态变化")
    locations = _dict_rows(chapter_plan.get("location_transitions"), "地点变化")
    knowledge = _dict_rows(chapter_plan.get("knowledge_grants"), "知识授予")
    milestones = _unique_strings(chapter_plan.get("milestones_consumed"), "里程碑")
    opened = _unique_strings(chapter_plan.get("open_threads"), "新伏笔")
    resolved = _unique_strings(chapter_plan.get("payoffs_due"), "回收伏笔")
    introductions = _dict_rows(chapter_plan.get("entity_introductions"), "世界实体引入")
    if set(opened).intersection(resolved):
        raise ValueError("同一章节不能同时打开和回收同一伏笔")

    delta = {
        "schema": EXPECTED_DELTA_SCHEMA,
        "state_before_hash": value_hash(state_before),
        "occurred_event_ids": events,
        "state_transitions": state,
        "location_transitions": locations,
        "knowledge_grants": knowledge,
        "milestones_consumed": milestones,
        "opened_thread_ids": opened,
        "resolved_thread_ids": resolved,
        "entity_introductions": introductions,
    }
    delta["proof_contracts"] = _proof_contracts(delta)
    delta["delta_hash"] = value_hash(delta)
    return delta


def _proof_contracts(delta: dict) -> list[dict]:
    contracts = [
        {"contract_id": f"event:{value}", "kind": "event", "value": value}
        for value in delta["occurred_event_ids"]
    ]
    contracts.extend(
        {
            "contract_id": f"entity:{item['id']}",
            "kind": "entity_introduction",
            "value": copy.deepcopy(item),
        }
        for item in delta.get("entity_introductions") or []
    )
    for field, prefix, kind in (
        ("state_transitions", "state", "state_transition"),
        ("location_transitions", "location", "location_transition"),
        ("knowledge_grants", "knowledge", "knowledge_grant"),
    ):
        contracts.extend(
            {
                "contract_id": f"{prefix}:{index}",
                "kind": kind,
                "value": copy.deepcopy(value),
            }
            for index, value in enumerate(delta[field], start=1)
        )
    # Milestones and thread lifecycle are deterministic effects of required
    # events. Requiring a second, independent sentence proof makes the body
    # restate the same outcome without increasing state safety.
    ids = [item["contract_id"] for item in contracts]
    if len(ids) != len(set(ids)):
        raise ValueError("proof contract ID 重复")
    return contracts


def _dict_rows(value, label: str) -> list[dict]:
    rows = list(value or [])
    if any(not isinstance(item, dict) for item in rows):
        raise ValueError(f"{label}必须是对象数组")
    return copy.deepcopy(rows)


def _unique_strings(value, label: str) -> list[str]:
    rows = list(value or [])
    if any(not isinstance(item, str) or not item.strip() for item in rows):
        raise ValueError(f"{label}必须使用非空字符串 ID")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{label} ID 重复")
    return rows
