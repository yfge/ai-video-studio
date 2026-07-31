"""Compact, source-grounded context for whole-novel continuity review."""

from __future__ import annotations

import copy
import json

from .story_novel_context_utils import frozen_story_contract, value_hash

GLOBAL_PAYLOAD_CHAR_BUDGET = 500_000
_STATE_FIELDS = (
    "occurred_event_ids",
    "state_transitions",
    "location_transitions",
    "knowledge_grants",
    "milestones_consumed",
    "opened_thread_ids",
    "resolved_thread_ids",
    "entity_introductions",
)


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
    rows = [_chapter_row(row, ledger_rows) for row in chapters]
    facts = _group_candidates(events, _event_row, "世界事件")
    character_memories = _group_candidates(memories, _memory_row, "人物记忆")
    payload = {
        "schema": "story_novel_continuity_global_context.v1",
        "story_contract": frozen_story_contract(revision.story_snapshot or {}),
        "plan_binding": _plan_binding(plan),
        "progression_arcs": _progression_arcs(revision.story_snapshot or {}),
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


def _plan_binding(plan: dict) -> dict:
    return {
        key: copy.deepcopy(plan.get(key))
        for key in (
            "schema",
            "version",
            "plan_hash",
            "canon_hash",
            "outline_hash",
            "chapter_count",
            "target_chars",
            "model_policy",
            "planning_structure_version",
            "future_guard_hash",
        )
        if plan.get(key) is not None
    }


def _progression_arcs(snapshot: dict) -> list[dict]:
    outline = (snapshot.get("story_seed") or {}).get("structured_outline") or {}
    return copy.deepcopy(outline.get("progression_arcs") or [])


def _chapter_row(chapter, ledger_rows: dict) -> dict:
    entry = ledger_rows.get(str(chapter.position)) or {}
    proofs = entry.get("proof_spans") or []
    proof_refs, evidence = _proof_digest(proofs)
    return {
        "business_id": chapter.business_id,
        "position": chapter.position,
        "title": str(chapter.title or ""),
        "summary": str(chapter.summary or ""),
        "cliffhanger": str(chapter.cliffhanger or ""),
        "content_hash": chapter.content_hash,
        "body_hash": entry.get("body_hash"),
        "source_hash": entry.get("source_hash"),
        "context_hash": entry.get("context_hash"),
        "canon_hash": entry.get("canon_hash"),
        "state_before_hash": entry.get("state_before_hash"),
        "state_after_hash": entry.get("state_after_hash"),
        "sentence_index_hash": entry.get("sentence_index_hash"),
        "plot_delta": _compact_plot_delta(entry.get("plot_delta") or {}),
        "state_delta": _compact_state_delta(entry.get("state_delta") or {}),
        "proof_refs": proof_refs,
        "sentence_index": evidence,
        "proof_manifest": {
            "proof_count": len(proofs),
            "source_sentence_ref_count": sum(
                len(item.get("sentence_ids") or []) for item in proofs
            ),
            "global_sentence_ref_count": sum(len(item) for item in proof_refs.values()),
            "selection_policy": "event_first_last_other_last",
        },
        "future_audit": copy.deepcopy(entry.get("future_audit") or {}),
    }


def _compact_plot_delta(value: dict) -> dict:
    return {
        key: copy.deepcopy(value.get(key))
        for key in (
            "key_events",
            "unresolved_threads",
            "resolved_threads",
        )
        if value.get(key)
    }


def _compact_state_delta(value: dict) -> dict:
    return {
        key: copy.deepcopy(value.get(key)) for key in _STATE_FIELDS if value.get(key)
    }


def _proof_digest(proofs: list[dict]) -> tuple[dict[str, list[str]], list[dict]]:
    refs = {}
    sentences: dict[str, str] = {}
    for proof in proofs:
        contract_id = str(proof.get("contract_id") or "")
        source_ids = [str(value) for value in proof.get("sentence_ids") or []]
        ids = _global_proof_ids(contract_id, source_ids)
        refs[contract_id] = ids
        for span in proof.get("spans") or []:
            sentence_id = str(span.get("sentence_id") or "")
            if sentence_id and sentence_id in ids:
                sentences.setdefault(sentence_id, str(span.get("text") or ""))
    return refs, [
        {"sentence_id": sentence_id, "text": text}
        for sentence_id, text in sentences.items()
    ]


def _global_proof_ids(contract_id: str, sentence_ids: list[str]) -> list[str]:
    if not sentence_ids:
        return []
    if contract_id.startswith("event:") and len(sentence_ids) > 1:
        return [sentence_ids[0], sentence_ids[-1]]
    return [sentence_ids[-1]]


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
