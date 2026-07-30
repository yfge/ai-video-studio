"""Deterministic Unicode sentence spans for source-bound v3 evidence."""

from __future__ import annotations

import re

from .story_novel_context_utils import value_hash

_BOUNDARY = re.compile(r"[。！？!?；;]+[”’」』）》】]*|\n+")


def sentence_spans(content_text: str) -> list[dict]:
    if not isinstance(content_text, str):
        raise ValueError("content_text 必须是字符串")
    source_hash = value_hash(content_text)
    ranges: list[tuple[int, int]] = []
    start = 0
    for match in _BOUNDARY.finditer(content_text):
        end = match.end()
        _append_trimmed_range(ranges, content_text, start, end)
        start = end
    _append_trimmed_range(ranges, content_text, start, len(content_text))
    return [
        {
            "sentence_id": f"S{index:04d}",
            "start": start,
            "end": end,
            "text": content_text[start:end],
            "source_hash": source_hash,
        }
        for index, (start, end) in enumerate(ranges, start=1)
    ]


def audit_sentence_index(rows: list[dict]) -> list[dict]:
    """Expose only source text references needed by the proof model."""
    return [{"sentence_id": row["sentence_id"], "text": row["text"]} for row in rows]


def resolve_sentence_refs(
    content_text: str, sentence_ids, expected_source_hash: str | None = None
) -> dict:
    source_hash = value_hash(content_text)
    if expected_source_hash is not None and expected_source_hash != source_hash:
        raise ValueError("正文 source hash 已变化")
    rows = sentence_spans(content_text)
    by_id = {item["sentence_id"]: item for item in rows}
    requested = list(sentence_ids or [])
    if not requested or len(requested) != len(set(requested)):
        raise ValueError("sentence refs 必须非空且不能重复")
    invalid = set(requested).difference(by_id)
    if invalid:
        raise ValueError(f"sentence refs 包含未知 ID: {sorted(invalid)}")
    selected = [by_id[item] for item in requested]
    return {
        "source_hash": source_hash,
        "sentence_index_hash": sentence_index_hash(rows),
        "sentence_ids": requested,
        "spans": selected,
        "quote": "……".join(item["text"] for item in selected),
    }


def sentence_index_hash(rows: list[dict]) -> str:
    return value_hash(
        [
            {key: row[key] for key in ("sentence_id", "start", "end", "source_hash")}
            for row in rows
        ]
    )


def _append_trimmed_range(
    ranges: list[tuple[int, int]], content_text: str, start: int, end: int
) -> None:
    while start < end and content_text[start].isspace():
        start += 1
    while end > start and content_text[end - 1].isspace():
        end -= 1
    if start < end:
        ranges.append((start, end))
