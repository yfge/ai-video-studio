"""Bounded current-chapter-only repair for typed-state source evidence."""

from __future__ import annotations

import copy
import json

from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key
from app.services.narrative_memory.source_evidence import source_contains_evidence
from app.utils.json_utils import extract_json_block

from .story_novel_knowledge_prompt import knowledge_sentence_prefixes

STATE_EVIDENCE_REPAIR_MAX_TOKENS = 16000


async def repair_state_evidence(
    revision,
    *,
    chapter_plan: dict,
    content_text: str,
    current_timeline: list[dict],
    canon: dict | None = None,
    delta: dict,
    diagnostics: list[dict],
    error: str | None,
    generate_text,
) -> str:
    """Return the frozen delta with only its source-evidence maps replaced."""
    response = await generate_text(
        revision,
        _prompt(
            chapter_plan=chapter_plan,
            content_text=content_text,
            current_timeline=current_timeline,
            canon=canon or {},
            delta=delta,
            diagnostics=diagnostics,
            error=error,
        ),
        max_tokens=STATE_EVIDENCE_REPAIR_MAX_TOKENS,
        temperature=0.0,
    )
    patch = extract_json_block(response)
    _validate_patch(patch, delta, chapter_plan, current_timeline)
    _apply_diagnostic_fallbacks(patch, diagnostics, content_text)
    merged = copy.deepcopy(delta)
    merged["evidence"] = patch["evidence"]
    merged["knowledge_evidence"] = patch.get("knowledge_evidence", {})
    merged["timeline_evidence"] = patch["timeline_evidence"]
    return json.dumps(merged, ensure_ascii=False, separators=(",", ":"))


def _apply_diagnostic_fallbacks(
    patch: dict, diagnostics: list[dict], content_text: str
) -> None:
    """Replace a still-invalid model quote with source-derived exact fragments."""
    for diagnostic in diagnostics:
        field, item_id = diagnostic.get("field"), diagnostic.get("id")
        quotes = patch.get(field) if isinstance(field, str) else None
        if not isinstance(quotes, dict) or item_id not in quotes:
            continue
        if source_contains_evidence(content_text, str(quotes[item_id])):
            continue
        fragments = []
        for item in diagnostic.get("fragments") or []:
            offsets = item.get("exact_offsets") or []
            candidate = item.get("source_candidate") or {}
            text = item.get("text") if offsets else candidate.get("text")
            offset = min(offsets) if offsets else candidate.get("exact_offset")
            if text and isinstance(offset, int) and offset >= 0:
                fragments.append((offset, str(text)))
        fallback = "……".join(text for _offset, text in sorted(fragments))
        if source_contains_evidence(content_text, fallback):
            quotes[item_id] = fallback


def _validate_patch(
    patch: object,
    delta: dict,
    chapter_plan: dict,
    current_timeline: list[dict],
) -> None:
    if not isinstance(patch, dict):
        raise ValueError("状态证据返修必须返回 JSON object")
    expected_knowledge = {
        knowledge_evidence_key(item) for item in delta.get("knowledge_grants") or []
    }
    required_fields = {
        "evidence",
        "timeline_evidence",
    }
    if expected_knowledge:
        required_fields.add("knowledge_evidence")
    if set(patch) not in (required_fields, required_fields | {"knowledge_evidence"}):
        raise ValueError(
            "状态证据返修只能返回 evidence、knowledge_evidence 与 timeline_evidence"
        )
    event_ids = set(delta.get("occurred_event_ids") or []) | set(
        delta.get("premature_future_event_ids") or []
    )
    timeline_ids = {
        item.get("id")
        for item in current_timeline
        if item.get("immutable")
        and item.get("id") in chapter_plan.get("canon_refs", [])
    }
    for field, expected in (
        ("evidence", event_ids),
        ("knowledge_evidence", expected_knowledge),
        ("timeline_evidence", timeline_ids),
    ):
        value = patch.get(field, {})
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError(f"状态证据返修的 {field} ID 集合无效")
        if any(
            not isinstance(quote, str) or not quote.strip() for quote in value.values()
        ):
            raise ValueError(f"状态证据返修的 {field} 必须是非空逐字引用")


def _prompt(
    *,
    chapter_plan: dict,
    content_text: str,
    current_timeline: list[dict],
    canon: dict,
    delta: dict,
    diagnostics: list[dict],
    error: str | None,
) -> str:
    current = {
        key: chapter_plan.get(key)
        for key in (
            "position",
            "title",
            "key_events",
            "required_event_ids",
            "knowledge_grants",
            "canon_refs",
            "timeline_event_bindings",
        )
    }
    frozen = {
        key: delta.get(key)
        for key in (
            "occurred_event_ids",
            "premature_future_event_ids",
            "evidence",
            "knowledge_evidence",
            "timeline_evidence",
        )
    }
    payload = {
        "current_chapter_contract": current,
        "current_immutable_timeline": current_timeline,
        "content_text": content_text,
        "frozen_event_ids_and_quotes": frozen,
        "required_knowledge_evidence_keys": [
            knowledge_evidence_key(item) for item in delta.get("knowledge_grants") or []
        ],
        "required_knowledge_sentence_contracts": knowledge_sentence_prefixes(
            {"chapter_contract": chapter_plan, "compiled_canon": canon}
        ),
        "evidence_diagnostics": diagnostics,
        "validation_error": error,
    }
    return (
        "从实际小说正文提取的 typed state 已冻结。上一次状态提取无效，"
        "现在只修复当前章逐字证据，不得修改任何事件 ID 或状态。\n"
        f"输入：{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n"
        "evidence 必须逐字复制正文；跨句只能用‘……’连接按正文顺序出现的片段。"
        "三个 evidence map 的 key 必须严格等于冻结 ID 集合；"
        "knowledge_evidence 的 key 必须逐项逐字复制 required_knowledge_evidence_keys，"
        "禁止把 key 中的 source_event_id 换成正文看似更匹配的其他事件；"
        "knowledge_evidence 必须逐项选择 required_knowledge_sentence_contracts 中"
        "required_prefix 紧接 source_event_text 的正文连续句，并把同一句完整加入"
        "对应 source_event_id 的 evidence；不得选择缺少 required_prefix 的较短复述。"
        "current_immutable_timeline 为空时 timeline_evidence 必须是空对象。"
        "诊断中的 source_candidate 是从正文计算出的最长连续逐字候选；"
        "若它能证明对应事件，直接复制其 text，不得保留候选之外的说话人前缀。"
        "failure_kind=quote_rewrite 时，exact_offsets=[] 且没有 source_candidate 的片段"
        "必须删除；其余片段按最早 exact_offset 升序重排后再用‘……’连接，"
        "不得保留模型原先的乱序。"
        "timeline_evidence[timeline-id] 必须包含固定日期，并逐字复用 "
        "evidence[current_chapter_contract.timeline_event_bindings[timeline-id]] "
        "的完整片段；不得借用同章其他事件。不得添加说话人、代词或概括，"
        "不得使用计划措辞代替正文。"
        "knowledge_evidence 的每个 value 必须完整、连续地包含在 "
        "evidence[对应 source event] 的某个逐字片段中，明确写出目标角色及其"
        "获知关系；knowledge_evidence 自身不得用省略号拼接。"
        "只输出严格 JSON："
        '{"evidence":{"event-id":"正文逐字片段"},'
        '"knowledge_evidence":{"character-id|fact-id|event-id":"连续获知句"},'
        '"timeline_evidence":{"time-id":"日期……同一事件逐字片段"}}'
    )
