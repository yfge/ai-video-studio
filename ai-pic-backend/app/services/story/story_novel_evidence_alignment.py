"""Source-backed quote alignment and calendar normalization for novel evidence."""

from __future__ import annotations

import re

from app.services.narrative_memory.source_evidence import (
    align_source_evidence,
    source_contains_evidence,
)

DATE_ANCHOR_PATTERN = re.compile(
    r"(?:(?P<year>\d{2,4}|[〇零一二三四五六七八九十百]{2,5})年)?"
    r"(?P<month>\d{1,2}|[〇零一二三四五六七八九十]{1,3})月"
    r"(?P<day>\d{1,2}|[〇零一二三四五六七八九十]{1,3})日"
)
QUOTE_SPLIT_PATTERN = re.compile(r"(?:…+|\.{3,})")
CLAUSE_SPLIT_PATTERN = re.compile(r"[。！？!?；;]+")
_CHINESE_DIGITS = dict(zip("〇零一二三四五六七八九", "00123456789"))


def event_date_anchors(chapter_plan: dict) -> list[str]:
    return list(
        dict.fromkeys(
            anchor
            for event in chapter_plan.get("key_events") or []
            for anchor in text_date_anchors(str(event))
        )
    )


def text_date_anchors(value: str) -> list[str]:
    return [match.group(0) for match in DATE_ANCHOR_PATTERN.finditer(value)]


def date_anchor_key(value: str) -> tuple[int | None, int, int] | None:
    match = DATE_ANCHOR_PATTERN.match(value)
    if not match:
        return None
    return (
        _number(match.group("year")) if match.group("year") else None,
        _number(match.group("month")),
        _number(match.group("day")),
    )


def date_anchors_match(left: str, right: str) -> bool:
    left_key, right_key = date_anchor_key(left), date_anchor_key(right)
    if not left_key or not right_key or left_key[1:] != right_key[1:]:
        return False
    return left_key[0] == right_key[0] or None in {left_key[0], right_key[0]}


def normalize_extracted_evidence(
    content_text: str, canon: dict, chapter_plan: dict, delta: dict
) -> None:
    """Rewrite only source-backed model quotes into deterministic ordered fragments."""
    for field in ("evidence", "timeline_evidence"):
        quotes = delta.get(field) or {}
        for item_id, quote in list(quotes.items()):
            quotes[item_id] = align_source_evidence(content_text, str(quote))
    timeline = {item["id"]: item for item in canon.get("timeline") or []}
    for item_id in chapter_plan.get("canon_refs") or []:
        item = timeline.get(item_id) or {}
        date = exact_date_anchor(str(item.get("story_time") or ""))
        quote = str((delta.get("timeline_evidence") or {}).get(item_id) or "")
        if date and re.sub(r"\s+", "", date) not in re.sub(r"\s+", "", quote):
            delta["timeline_evidence"][item_id] = _quote_with_date(
                content_text, quote, date
            )


def exact_date_anchor(value: str) -> str | None:
    match = re.search(r"\d{4}年\d{1,2}月\d{1,2}日", value)
    return match.group(0) if match else None


def date_precedes_evidence_event(quote: str, date: str) -> bool:
    parts = [item for item in QUOTE_SPLIT_PATTERN.split(quote) if item.strip()]
    exact = semantic_text(date)
    target_index = next(
        (index for index, item in enumerate(parts) if exact in semantic_text(item)),
        None,
    )
    if target_index is None:
        return False
    if any(
        not any(
            date_anchors_match(anchor, date)
            for anchor in text_date_anchors(parts[index])
        )
        for index in range(target_index)
    ):
        return False
    target = semantic_text(parts[target_index])
    exact_position = target.find(exact)
    if exact_position != 0:
        return False
    trailing = target[exact_position + len(exact) :] + "".join(
        parts[target_index + 1 :]
    )
    without_dates = DATE_ANCHOR_PATTERN.sub("", trailing)
    return len(semantic_text(without_dates)) >= 3


def evidence_semantic_parts(value: str) -> list[str]:
    return [
        semantic
        for section in QUOTE_SPLIT_PATTERN.split(value)
        for item in CLAUSE_SPLIT_PATTERN.split(section)
        if (semantic := semantic_text(DATE_ANCHOR_PATTERN.sub("", item)))
    ]


def _quote_with_date(source_text: str, quote: str, date: str) -> str:
    parts = _matched_quote_parts(source_text, align_source_evidence(source_text, quote))
    source = semantic_text(source_text)
    if not parts:
        semantic_quote = semantic_text(quote)
        quote_position = source.find(semantic_quote)
        if len(semantic_quote) < 8 or quote_position < 0:
            return quote
        parts = [(quote_position, quote)]
    date_position = source.find(semantic_text(date))
    event_positions = [
        position
        for position, text in parts
        if not any(
            date_anchors_match(anchor, date) for anchor in text_date_anchors(text)
        )
    ]
    if date_position < 0 or not event_positions or date_position > min(event_positions):
        return quote
    parts.append((date_position, date))
    candidate = "……".join(text for _, text in sorted(parts))
    return candidate if source_contains_evidence(source_text, candidate) else quote


def _matched_quote_parts(source_text: str, quote: str) -> list[tuple[int, str]]:
    source, cursor, matched = semantic_text(source_text), 0, []
    sections = [
        item.strip() for item in QUOTE_SPLIT_PATTERN.split(quote) if item.strip()
    ]
    for section in sections:
        candidates = [section]
        semantic = semantic_text(section)
        if source.find(semantic, cursor) < 0:
            candidates = [
                item.strip()
                for item in CLAUSE_SPLIT_PATTERN.split(section)
                if len(semantic_text(item)) >= 3
            ]
            if len(candidates) < 2:
                return []
        for candidate in candidates:
            semantic = semantic_text(candidate)
            position = source.find(semantic, cursor)
            if position < 0:
                return []
            matched.append((position, candidate))
            cursor = position + len(semantic)
    if len(matched) < 2 or sum(len(semantic_text(item)) for _, item in matched) < 16:
        return []
    return matched


def semantic_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)


def _number(value: str) -> int:
    if value.isdigit():
        return int(value)
    if "十" in value:
        left, right = value.split("十", 1)
        return (int(_CHINESE_DIGITS[left]) if left else 1) * 10 + (
            int(_CHINESE_DIGITS[right]) if right else 0
        )
    return int("".join(_CHINESE_DIGITS[item] for item in value))
