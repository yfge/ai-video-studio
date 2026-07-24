"""Conservative deterministic checks for prematurely asserted future conclusions."""

from __future__ import annotations

import json
import re

_CERTAINTY_MARKERS = (
    "确认",
    "证明",
    "只可能",
    "确定",
    "断定",
    "认定",
    "无疑",
    "就是",
)
_ASSERTION_MARKERS = (*_CERTAINTY_MARKERS, "来自", "源自", "表明", "意味着")
_VERIFICATION_MARKERS = (
    "确认",
    "证明",
    "查明",
    "揭露",
    "核验",
    "化验",
    "调查",
    "见证",
    "断定",
    "认定",
)
_UNCERTAINTY_MARKERS = (
    "也许",
    "可能",
    "疑似",
    "怀疑",
    "猜测",
    "尚不确定",
    "无法确认",
    "有待",
    "待查",
    "待化验",
    "似乎",
    "或许",
)
_INVALID_FUTURE_ID_PREFIX = "premature_future_event_ids 引用了目录外事件: "


def paired_future_events(chapter: dict) -> list[dict]:
    event_ids = list(chapter.get("required_event_ids") or [])
    descriptions = list(chapter.get("key_events") or [])
    fallback = chapter.get("goal") or chapter.get("title")
    if len(event_ids) == 1:
        descriptions = ["；".join(descriptions) or fallback]
    elif len(descriptions) > len(event_ids):
        boundary = len(event_ids) - 1
        descriptions = [
            *descriptions[:boundary],
            "；".join(descriptions[boundary:]),
        ]
    return [
        {
            "event_id": event_id,
            "description": (
                descriptions[index] if index < len(descriptions) else fallback
            ),
        }
        for index, event_id in enumerate(event_ids)
    ]


def future_audit_id_violations(catalog: list[dict], delta: dict) -> list[dict]:
    allowed = {
        str(event.get("event_id"))
        for chapter in catalog
        for event in chapter.get("events") or []
        if event.get("event_id")
    }
    invalid = sorted(
        set(delta.get("premature_future_event_ids") or []).difference(allowed)
    )
    return [
        {
            "code": "canon_violation",
            "message": f"{_INVALID_FUTURE_ID_PREFIX}{event_id}",
        }
        for event_id in invalid
    ]


def is_future_audit_id_issue(issue: dict) -> bool:
    return str(issue.get("message") or "").startswith(_INVALID_FUTURE_ID_PREFIX)


def future_claim_violations(
    chapters: list[dict], position: int, content_text: str
) -> list[dict]:
    """Catch future-only conclusions asserted before their planned verification."""
    visible = _compact(
        "".join(
            json.dumps(item, ensure_ascii=False, default=str)
            for item in chapters
            if int(item["position"]) <= position
        )
    )
    body = _compact(content_text)
    violations = []
    for chapter in chapters:
        if int(chapter["position"]) <= position:
            continue
        for event in paired_future_events(chapter):
            claim = _claim_target(str(event.get("description") or ""))
            terms = _future_only_body_terms(claim, visible, body) if claim else []
            if terms and any(_asserts_term(content_text, term) for term in terms):
                violations.append(
                    {
                        "code": "canon_violation",
                        "message": f"正文提前完成未来事件: {event['event_id']}",
                    }
                )
    return violations


def _claim_target(description: str) -> str:
    compact = _compact(description)
    ends = [
        compact.find(marker) + len(marker)
        for marker in _VERIFICATION_MARKERS
        if marker in compact
    ]
    return compact[max(ends) :] if ends else ""


def _future_only_body_terms(future: str, visible: str, body: str) -> list[str]:
    matches = []
    for size in range(min(8, len(future)), 3, -1):
        for start in range(0, len(future) - size + 1):
            term = future[start : start + size]
            if (
                term in visible
                or term not in body
                or any(term in existing for existing in matches)
            ):
                continue
            matches.append(term)
    return matches


def _asserts_term(content_text: str, term: str) -> bool:
    compact = _compact(content_text)
    for match in re.finditer(re.escape(term), compact):
        window = compact[max(0, match.start() - 80) : match.end() + 80]
        uncertain = any(
            marker in window.replace("只可能", "") for marker in _UNCERTAINTY_MARKERS
        )
        if not uncertain and any(marker in window for marker in _ASSERTION_MARKERS):
            return True
    return False


def _compact(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
