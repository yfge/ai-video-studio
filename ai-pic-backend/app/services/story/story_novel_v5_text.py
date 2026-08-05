"""Continuous-prose normalization, truncation merge, and span replacement."""

from __future__ import annotations

import re

from .story_novel_sentence_spans import sentence_spans


def clean_prose(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^```(?:text|markdown)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    if not text:
        raise ValueError("prose output is empty")
    if text.startswith("{") and "content_text" in text[:200]:
        raise ValueError("v5 prose must not be a JSON envelope")
    return text.strip()


def complete_sentence_prefix(value: str) -> str:
    text = clean_prose(value)
    matches = list(re.finditer(r"[。！？!?；;]+[”’」』）》】]*", text))
    return text[: matches[-1].end()].rstrip() if matches else ""


def merge_continuation(prefix: str, continuation: str) -> str:
    left, right = clean_prose(prefix), clean_prose(continuation)
    max_overlap = min(len(left), len(right), 800)
    overlap = next(
        (size for size in range(max_overlap, 3, -1) if left[-size:] == right[:size]),
        0,
    )
    merged = f"{left}{right[overlap:]}".strip()
    if merged == left:
        raise ValueError("continuation contains no new prose")
    return merged


def replace_span(content: str, sentence_ids: list[str], replacement: str) -> str:
    rows = sentence_spans(content)
    selected = [item for item in rows if item["sentence_id"] in set(sentence_ids)]
    if not selected or len(selected) != len(sentence_ids):
        raise ValueError("repair span references unknown sentences")
    positions = [rows.index(item) for item in selected]
    if positions != list(range(min(positions), max(positions) + 1)):
        raise ValueError("repair span must be contiguous")
    start, end = selected[0]["start"], selected[-1]["end"]
    return f"{content[:start]}{clean_prose(replacement)}{content[end:]}".strip()


def neighbor_context(content: str, sentence_ids: list[str]) -> dict:
    rows = sentence_spans(content)
    selected = [item for item in rows if item["sentence_id"] in set(sentence_ids)]
    first, last = rows.index(selected[0]), rows.index(selected[-1])
    return {
        "before_sentence": rows[first - 1]["text"] if first else None,
        "editable_span": "".join(item["text"] for item in selected),
        "after_sentence": rows[last + 1]["text"] if last + 1 < len(rows) else None,
    }
