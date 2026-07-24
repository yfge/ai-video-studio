"""Explain invalid typed-state evidence without weakening source verification."""

from __future__ import annotations

import re

from app.services.narrative_memory.source_evidence import (
    align_source_evidence,
    source_contains_evidence,
)

_EVIDENCE_ONLY_MESSAGES = (
    "正文事件证据必须逐项等于发生事件",
    "事件缺少可核对的正文证据:",
    "正文时间证据必须逐项等于当前章节 immutable timeline",
    "时间线缺少正文证据:",
    "时间线证据未对应绑定事件:",
    "时间线证据缺少固定日期 ",
    "时间线证据固定日期晚于或缺少对应事件:",
)
_ELLIPSIS = re.compile(r"(?:…+|\.{3,})")
_DROPPABLE_LEADING_CHARACTERS = frozenset("他她它其将把")


def evidence_repair_diagnostics(
    content_text: str, delta: dict, issues: list[dict]
) -> list[dict]:
    messages = [str(item.get("message") or "") for item in issues]
    diagnostics = []
    for field, generic in (
        ("evidence", "正文事件证据必须逐项等于发生事件"),
        (
            "timeline_evidence",
            "正文时间证据必须逐项等于当前章节 immutable timeline",
        ),
    ):
        for item_id, quote in (delta.get(field) or {}).items():
            relevant = [
                message
                for message in messages
                if message == generic or message.endswith(f": {item_id}")
            ]
            if not relevant:
                continue
            parts = [
                fragment.strip()
                for fragment in _ELLIPSIS.split(str(quote))
                if fragment.strip()
            ]
            fragments = []
            for fragment in parts:
                offsets = _exact_offsets(content_text, fragment)
                item = {"text": fragment, "exact_offsets": offsets}
                candidate = (
                    None if offsets else _source_candidate(content_text, fragment)
                )
                if candidate:
                    item["source_candidate"] = candidate
                fragments.append(item)
            first = next(
                (
                    {"fragment_index": index, "text": item["text"]}
                    for index, item in enumerate(fragments)
                    if not item["exact_offsets"]
                ),
                None,
            )
            found_any = any(item["exact_offsets"] for item in fragments)
            diagnostics.append(
                {
                    "field": field,
                    "id": item_id,
                    "failure_kind": (
                        "quote_rewrite"
                        if first and found_any
                        else (
                            "body_event_unverified"
                            if first
                            else "timeline_or_key_mismatch"
                        )
                    ),
                    "fragments": fragments,
                    "first_mismatch": first,
                    "issues": relevant,
                }
            )
    return diagnostics


def only_evidence_issues(issues: list[dict]) -> bool:
    messages = [str(item.get("message") or "") for item in issues]
    return bool(messages) and all(
        message.startswith(_EVIDENCE_ONLY_MESSAGES) for message in messages
    )


def _exact_offsets(content_text: str, fragment: str) -> list[int]:
    offsets, cursor = [], 0
    while (offset := content_text.find(fragment, cursor)) >= 0:
        offsets.append(offset)
        cursor = offset + 1
    return offsets


def _source_candidate(content_text: str, fragment: str) -> dict | None:
    text = align_source_evidence(content_text, fragment)
    if text == fragment or not source_contains_evidence(content_text, text):
        text = _unique_trimmed_candidate(content_text, fragment)
        if not text:
            return None
    offset = content_text.find(text)
    return {"text": text, "exact_offset": offset} if offset >= 0 else None


def _unique_trimmed_candidate(content_text: str, fragment: str) -> str:
    """Offer one exact suffix without guessing a named actor or dialogue speaker."""
    stripped = fragment.strip()
    if (
        not stripped
        or stripped[0] not in _DROPPABLE_LEADING_CHARACTERS
        or any(mark in stripped for mark in '“”"')
    ):
        return ""
    candidate = stripped[1:].lstrip()
    if len(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", candidate)) < 12:
        return ""
    return candidate if content_text.count(candidate) == 1 else ""
