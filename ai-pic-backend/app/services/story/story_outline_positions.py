"""Extract explicit chapter coverage without imposing a chapter cap."""

import re

_CHAPTER_MARKER = re.compile(r"第\s*(\d+|[零〇一二两三四五六七八九十百千]+)\s*章")
_CHAPTER_RANGE = re.compile(
    r"第\s*(\d+|[零〇一二两三四五六七八九十百千]+)\s*章"
    r"\s*(?:至|到|-|—|~|～)\s*"
    r"第?\s*(\d+|[零〇一二两三四五六七八九十百千]+)\s*章"
)
_CN_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_CN_UNITS = {"十": 10, "百": 100, "千": 1000}


def _chapter_number(raw: str) -> int:
    if raw.isdigit():
        return int(raw)
    total = 0
    current = 0
    for char in raw:
        if char in _CN_DIGITS:
            current = _CN_DIGITS[char]
        else:
            total += (current or 1) * _CN_UNITS[char]
            current = 0
    return total + current


def explicit_outline_positions(snapshot: dict) -> list[int]:
    seed = snapshot.get("story_seed") or {}
    structured = (seed.get("structured_outline") or {}).get("chapters") or []
    structured_positions = [item.get("position") for item in structured]
    if structured and structured_positions == list(range(1, len(structured) + 1)):
        return structured_positions
    outline = str(seed.get("outline_text") or seed.get("outline") or "")
    range_match = _CHAPTER_RANGE.search(outline)
    if range_match:
        start, end = (_chapter_number(value) for value in range_match.groups())
        if start == 1 and end >= start:
            return list(range(start, end + 1))
    positions = list(
        dict.fromkeys(
            _chapter_number(match) for match in _CHAPTER_MARKER.findall(outline)
        )
    )
    if len(positions) >= 2 and positions == list(range(1, positions[-1] + 1)):
        return positions
    return []
