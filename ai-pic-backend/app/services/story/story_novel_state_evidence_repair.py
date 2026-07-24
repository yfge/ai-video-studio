"""Bounded current-chapter-only repair for typed-state source evidence."""

from __future__ import annotations

import copy
import json

from app.utils.json_utils import extract_json_block

STATE_EVIDENCE_REPAIR_MAX_TOKENS = 16000


async def repair_state_evidence(
    revision,
    *,
    chapter_plan: dict,
    content_text: str,
    current_timeline: list[dict],
    delta: dict,
    diagnostics: list[dict],
    error: str | None,
    generate_text,
) -> str:
    """Return the frozen delta with only its two evidence maps replaced."""
    response = await generate_text(
        revision,
        _prompt(
            chapter_plan=chapter_plan,
            content_text=content_text,
            current_timeline=current_timeline,
            delta=delta,
            diagnostics=diagnostics,
            error=error,
        ),
        max_tokens=STATE_EVIDENCE_REPAIR_MAX_TOKENS,
        temperature=0.0,
    )
    patch = extract_json_block(response)
    _validate_patch(patch, delta, chapter_plan, current_timeline)
    merged = copy.deepcopy(delta)
    merged["evidence"] = patch["evidence"]
    merged["timeline_evidence"] = patch["timeline_evidence"]
    return json.dumps(merged, ensure_ascii=False, separators=(",", ":"))


def _validate_patch(
    patch: object,
    delta: dict,
    chapter_plan: dict,
    current_timeline: list[dict],
) -> None:
    if not isinstance(patch, dict) or set(patch) != {
        "evidence",
        "timeline_evidence",
    }:
        raise ValueError("状态证据返修只能返回 evidence 与 timeline_evidence")
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
        ("timeline_evidence", timeline_ids),
    ):
        value = patch.get(field)
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
            "timeline_evidence",
        )
    }
    payload = {
        "current_chapter_contract": current,
        "current_immutable_timeline": current_timeline,
        "content_text": content_text,
        "frozen_event_ids_and_quotes": frozen,
        "evidence_diagnostics": diagnostics,
        "validation_error": error,
    }
    return (
        "从实际小说正文提取的 typed state 已冻结。上一次状态提取无效，"
        "现在只修复当前章逐字证据，不得修改任何事件 ID 或状态。\n"
        f"输入：{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n"
        "evidence 必须逐字复制正文；跨句只能用‘……’连接按正文顺序出现的片段。"
        "两个 evidence map 的 key 必须严格等于冻结 ID 集合；"
        "current_immutable_timeline 为空时 timeline_evidence 必须是空对象。"
        "诊断中的 source_candidate 是从正文计算出的最长连续逐字候选；"
        "若它能证明对应事件，直接复制其 text，不得保留候选之外的说话人前缀。"
        "timeline_evidence[timeline-id] 必须包含固定日期，并逐字复用 "
        "evidence[current_chapter_contract.timeline_event_bindings[timeline-id]] "
        "的完整片段；不得借用同章其他事件。不得添加说话人、代词或概括，"
        "不得使用计划措辞代替正文。"
        "只输出严格 JSON："
        '{"evidence":{"event-id":"正文逐字片段"},'
        '"timeline_evidence":{"time-id":"日期……同一事件逐字片段"}}'
    )
