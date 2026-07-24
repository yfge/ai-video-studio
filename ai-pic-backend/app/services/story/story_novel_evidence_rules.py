"""Deterministic source-evidence checks for generated novel chapters."""

from __future__ import annotations

import re

from app.services.narrative_memory.source_evidence import source_contains_evidence

from .story_novel_evidence_alignment import (
    DATE_ANCHOR_PATTERN,
    date_precedes_evidence_event,
    event_date_anchors,
    exact_date_anchor,
    semantic_text,
)
from .story_novel_timeline_contract import (
    bound_event_id,
    chapter_timeline_binding_issues,
)


def evidence_violations(content_text: str, delta: dict) -> list[dict]:
    evidence = delta.get("evidence") or {}
    event_ids = list(delta.get("occurred_event_ids") or []) + list(
        delta.get("premature_future_event_ids") or []
    )
    violations = []
    if set(evidence) != set(event_ids):
        violations.append(
            {
                "code": "canon_violation",
                "message": "正文事件证据必须逐项等于发生事件",
            }
        )
    violations.extend(
        [
            {
                "code": "canon_violation",
                "message": f"事件缺少可核对的正文证据: {event_id}",
            }
            for event_id in dict.fromkeys(event_ids)
            if not evidence.get(event_id)
            or not source_contains_evidence(content_text, str(evidence[event_id]))
        ]
    )
    return violations


def required_event_anchor_violations(
    content_text: str, chapter_plan: dict
) -> list[dict]:
    """Require literal current-contract dates so semantic audits cannot shift them."""
    compact_body = re.sub(r"\s+", "", content_text)
    anchors = event_date_anchors(chapter_plan)
    return [
        {
            "code": "canon_violation",
            "message": f"正文缺少当前事件固定日期: {anchor}",
        }
        for anchor in anchors
        if re.sub(r"\s+", "", anchor) not in compact_body
    ]


def timeline_evidence_violations(
    content_text: str, canon: dict, chapter_plan: dict, delta: dict
) -> list[dict]:
    timeline = {
        item["id"]: item
        for item in canon.get("timeline") or []
        if item.get("immutable")
    }
    expected = {ref for ref in chapter_plan.get("canon_refs") or [] if ref in timeline}
    evidence = delta.get("timeline_evidence") or {}
    violations = [
        {"code": "canon_violation", "message": issue}
        for issue in chapter_timeline_binding_issues(chapter_plan, set(timeline))
    ]
    if set(evidence) != expected:
        violations.append(
            {
                "code": "canon_violation",
                "message": "正文时间证据必须逐项等于当前章节 immutable timeline",
            }
        )
    compact_body = re.sub(r"\s+", "", content_text)
    for timeline_id in sorted(expected):
        quote = str(evidence.get(timeline_id) or "")
        if not quote or not source_contains_evidence(content_text, quote):
            violations.append(
                {
                    "code": "canon_violation",
                    "message": f"时间线缺少正文证据: {timeline_id}",
                }
            )
        event_id = bound_event_id(chapter_plan, timeline_id)
        if not _shares_bound_event_evidence(
            quote,
            delta,
            event_id,
            str(timeline[timeline_id].get("story_time") or ""),
        ):
            violations.append(
                {
                    "code": "canon_violation",
                    "message": f"时间线证据未对应绑定事件: {timeline_id}",
                }
            )
        date = exact_date_anchor(str(timeline[timeline_id].get("story_time") or ""))
        if date and re.sub(r"\s+", "", date) not in re.sub(r"\s+", "", quote):
            violations.append(
                {
                    "code": "canon_violation",
                    "message": f"时间线证据缺少固定日期 {date}: {timeline_id}",
                }
            )
        elif date and not date_precedes_evidence_event(quote, date):
            violations.append(
                {
                    "code": "canon_violation",
                    "message": f"时间线证据固定日期晚于或缺少对应事件: {timeline_id}",
                }
            )
        if date and re.sub(r"\s+", "", date) not in compact_body:
            violations.append(
                {
                    "code": "canon_violation",
                    "message": f"正文缺少固定日期 {date}: {timeline_id}",
                }
            )
    return violations


def _shares_bound_event_evidence(
    timeline_quote: str,
    delta: dict,
    event_id: str | None,
    story_time: str,
) -> bool:
    if not event_id or event_id not in set(delta.get("occurred_event_ids") or []):
        return False
    event_quote = (delta.get("evidence") or {}).get(event_id)
    event_text = _timeline_semantic_text(str(event_quote or ""))
    timeline_text = _timeline_semantic_text(timeline_quote)
    if len(event_text) < 8 or not timeline_text.endswith(event_text):
        return False
    prefix = timeline_text[: -len(event_text)]
    anchor = _timeline_semantic_text(story_time)
    if not anchor:
        return not prefix
    variants = {
        anchor,
        f"{anchor}时",
        f"{anchor}时分",
        f"{anchor}前后",
        f"{anchor}左右",
    }
    return prefix in variants or (
        not prefix and any(timeline_text.startswith(value) for value in variants)
    )


def _timeline_semantic_text(value: str) -> str:
    # Keep 08:00/傍晚 qualifiers: they are part of the immutable event time.
    return semantic_text(DATE_ANCHOR_PATTERN.sub("", value))
