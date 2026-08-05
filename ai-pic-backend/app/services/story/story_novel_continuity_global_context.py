"""Compact, source-grounded context for whole-novel continuity review."""

from __future__ import annotations

import copy
import json

from .story_novel_context_utils import frozen_story_contract, value_hash
from .story_novel_continuity_chapter_digest import (
    chapter_digest,
    plan_binding,
    progression_arcs,
)

GLOBAL_PAYLOAD_CHAR_BUDGET = 500_000


def build_global_context(
    revision,
    chapters: list,
    ledger_rows: dict,
    events: list,
    memories: list,
    window_reports: list,
    valid_contract_refs: list[str],
) -> dict:
    plan = revision.generation_plan or {}
    rows = [chapter_digest(row, ledger_rows) for row in chapters]
    facts = _group_candidates(events, _event_row, "世界事件")
    character_memories = _group_candidates(memories, _memory_row, "人物记忆")
    payload = {
        "schema": "story_novel_continuity_global_context.v1",
        "story_contract": frozen_story_contract(revision.story_snapshot or {}),
        "plan_binding": plan_binding(plan),
        "progression_arcs": progression_arcs(revision.story_snapshot or {}),
        "compiled_canon": copy.deepcopy(plan.get("canon") or {}),
        "chapters": rows,
        "facts": facts,
        "character_memories": character_memories,
        "rolling_state": copy.deepcopy(
            (revision.continuity_ledger or {}).get("current_state") or {}
        ),
        "window_findings": [_window_row(item) for item in window_reports],
        "valid_contract_refs": list(valid_contract_refs),
        "input_manifest": {
            "chapter_count": len(rows),
            "chapter_positions": [row["position"] for row in rows],
            "fact_count": len(events),
            "fact_ids_hash": value_hash(_candidate_ids(facts)),
            "memory_count": len(memories),
            "memory_ids_hash": value_hash(_candidate_ids(character_memories)),
            "window_count": len(window_reports),
            "sentence_index_count": sum(len(row["sentence_index"]) for row in rows),
            "raw_body_included": False,
            "raw_proof_records_included": False,
            "candidate_quote_text_included": False,
        },
    }
    size = global_context_chars(payload)
    payload["input_manifest"]["payload_chars"] = size
    size = global_context_chars(payload)
    payload["input_manifest"]["payload_chars"] = size
    if size > GLOBAL_PAYLOAD_CHAR_BUDGET:
        raise ValueError(
            "全局连续性输入超过 "
            f"{GLOBAL_PAYLOAD_CHAR_BUDGET} 字符预算（实际 {size}）；"
            "已保留全部章节和状态证据，拒绝静默裁剪"
        )
    return payload


def global_context_chars(payload: dict) -> int:
    return len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _event_row(item: dict) -> dict:
    return {
        key: copy.deepcopy(item.get(key))
        for key in (
            "source_hash",
            "event_type",
            "participant_character_ids",
            "presentation",
            "audience_disclosure",
            "typed_fact_id",
            "typed_source_event_id",
        )
        if item.get(key) is not None
    } | {"summary": str(item.get("summary") or "")}


def _memory_row(item: dict) -> dict:
    result = {
        key: copy.deepcopy(item.get(key))
        for key in (
            "character_business_id",
            "memory_type",
            "source_hash",
            "effective_from_anchor_business_id",
            "typed_fact_id",
            "typed_source_event_id",
            "revision_local",
        )
        if item.get(key) is not None
    }
    for key in ("content", "belief", "growth_delta"):
        if item.get(key) is not None:
            result[key] = copy.deepcopy(item.get(key))
    return result


def _group_candidates(
    items: list[dict], row_builder, label: str
) -> dict[str, dict[str, dict]]:
    result: dict[str, dict[str, dict]] = {}
    seen = set()
    for item in items:
        chapter_id = str(item.get("source_chapter_business_id") or "")
        candidate_id = str(item.get("business_id") or "")
        if not candidate_id or not chapter_id or not item.get("source_hash"):
            raise ValueError(f"{label}缺少 ID、来源章或 source hash")
        if candidate_id in seen:
            raise ValueError(f"{label}候选 ID 重复: {candidate_id}")
        seen.add(candidate_id)
        result.setdefault(chapter_id, {})[candidate_id] = row_builder(item)
    if len(seen) != len(items):
        raise ValueError(f"{label}分组覆盖不完整")
    return result


def _candidate_ids(groups: dict[str, dict[str, dict]]) -> list[str]:
    return sorted(candidate_id for rows in groups.values() for candidate_id in rows)


def _window_row(item: dict) -> dict:
    return {
        "batch_index": item.get("batch_index"),
        "chapter_refs": copy.deepcopy(item.get("chapter_refs") or []),
        "summary": str(item.get("summary") or ""),
        "issues": copy.deepcopy(item.get("issues") or []),
    }
