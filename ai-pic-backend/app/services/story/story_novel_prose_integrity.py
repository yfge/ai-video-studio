"""Deterministic corruption checks shared by initial and repaired v3 prose."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_QUOTE_PAIRS = (("“", "”"), ("「", "」"), ("『", "』"))
_COMPLETE_ENDINGS = set("。！？!?…—”’」』）》】")


def prose_integrity_violations(blocks: list[dict]) -> list[dict]:
    """Reject objective assembly corruption without judging prose style."""
    normalized = [
        {
            "block_id": str(item.get("block_id") or f"B{index:02d}"),
            "content_text": str(item.get("content_text") or ""),
        }
        for index, item in enumerate(blocks or [], 1)
    ]
    violations = []
    for block in normalized:
        violations.extend(_block_corruption(block))
    violations.extend(_duplicate_passages(normalized))
    violations.extend(_unbalanced_quotes(normalized))
    return violations


def _block_corruption(block: dict) -> list[dict]:
    block_id, text = block["block_id"], block["content_text"]
    rows = []
    if re.search(r"\\[ntr]", text):
        rows.append(
            _issue(
                "literal_escape_sequence",
                "正文含未解析的转义序列",
                [block_id],
            )
        )
    ending = text.rstrip()[-1:] if text.strip() else ""
    if ending and ending not in _COMPLETE_ENDINGS:
        rows.append(
            _issue(
                "truncated_block_ending",
                "block 末尾不是完整句，疑似输出或机械裁剪造成截断",
                [block_id],
            )
        )
    return rows


def _duplicate_passages(blocks: list[dict]) -> list[dict]:
    issues, seen_paragraphs = [], {}
    compact = [_compact(item["content_text"]) for item in blocks]
    for block in blocks:
        for paragraph in re.split(r"\n+", block["content_text"]):
            value = _compact(paragraph)
            if len(value) < 80:
                continue
            previous = seen_paragraphs.get(value)
            if previous:
                issues.append(
                    _duplicate_issue(previous, block["block_id"], len(value), "exact")
                )
            else:
                seen_paragraphs[value] = block["block_id"]
    for right in range(1, len(blocks)):
        for left in range(right):
            first, second = compact[left], compact[right]
            if min(len(first), len(second)) < 160:
                continue
            match = SequenceMatcher(
                None, first, second, autojunk=False
            ).find_longest_match()
            threshold = max(140, min(len(first), len(second)) * 55 // 100)
            if match.size >= threshold:
                issues.append(
                    _duplicate_issue(
                        blocks[left]["block_id"],
                        blocks[right]["block_id"],
                        match.size,
                        "near",
                    )
                )
    return _dedupe(issues)


def _unbalanced_quotes(blocks: list[dict]) -> list[dict]:
    text = "\n\n".join(item["content_text"] for item in blocks)
    affected = [
        item["block_id"]
        for item in blocks
        if any(q in item["content_text"] for pair in _QUOTE_PAIRS for q in pair)
    ]
    return (
        [
            _issue(
                "unbalanced_quote",
                f"正文引号 {opening}{closing} 数量不平衡",
                affected[-1:] or [blocks[-1]["block_id"]],
            )
            for opening, closing in _QUOTE_PAIRS
            if text.count(opening) != text.count(closing)
        ]
        if blocks
        else []
    )


def _duplicate_issue(source: str, target: str, size: int, kind: str) -> dict:
    return {
        **_issue(
            "duplicate_passage",
            f"{target} 重复了 {source} 的长段正文（{size} 个非空白字符）",
            [target],
        ),
        "source_block_id": source,
        "duplicate_kind": kind,
    }


def _issue(reason_code: str, message: str, block_ids: list[str]) -> dict:
    return {
        "code": "prose_integrity_violation",
        "reason_code": reason_code,
        "message": message,
        "block_ids": block_ids,
    }


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _dedupe(items: list[dict]) -> list[dict]:
    return list(
        {
            (
                item["reason_code"],
                tuple(item["block_ids"]),
                item.get("source_block_id"),
            ): item
            for item in items
        }.values()
    )
