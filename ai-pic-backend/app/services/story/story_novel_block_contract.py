"""Parse, assemble, and locally replace v3 prose blocks."""

from __future__ import annotations

import copy
import json
import re

from app.utils.json_utils import extract_json_block

from .story_novel_context_utils import value_hash


def parse_prose_blocks(payload, expected_count: int | None = None) -> list[dict]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("正文 blocks 不是有效 JSON") from exc
    if not isinstance(payload, dict) or set(payload).difference({"schema", "blocks"}):
        raise ValueError("正文响应只能包含 blocks")
    if payload.get("schema") not in {None, "story_novel_prose_blocks.v1"}:
        raise ValueError("正文 blocks schema 无效")
    blocks = list(payload.get("blocks") or [])
    if expected_count is not None and len(blocks) != expected_count:
        raise ValueError(f"正文必须包含 {expected_count} 个 blocks")
    expected_ids = [f"B{index:02d}" for index in range(1, len(blocks) + 1)]
    if [item.get("block_id") for item in blocks] != expected_ids:
        raise ValueError("block ID 必须从 B01 连续编号")
    for item in blocks:
        if not isinstance(item, dict) or set(item) != {"block_id", "content_text"}:
            raise ValueError("block 只能包含 block_id/content_text")
        if not isinstance(item["content_text"], str) or not re.search(
            r"\S", item["content_text"]
        ):
            raise ValueError("block 正文不能为空")
        item["content_text"] = item["content_text"].strip()
    return copy.deepcopy(blocks)


def parse_prose_block_response(raw: str, expected_count: int) -> list[dict]:
    payload = extract_json_block(raw)
    if payload is not None:
        return parse_prose_blocks(payload, expected_count=expected_count)
    return recover_unescaped_prose_blocks(raw, expected_count)


def recover_unescaped_prose_blocks(raw: str, expected_count: int) -> list[dict]:
    """Recover a complete blocks-only envelope with unescaped dialogue quotes."""
    text = str(raw or "").strip()
    if not re.match(r'^\{\s*"blocks"\s*:\s*\[', text):
        raise ValueError("正文响应只能包含 blocks")
    starts = list(
        re.finditer(
            r'\{\s*"block_id"\s*:\s*"([^"]+)"\s*,\s*' r'"content_text"\s*:\s*"',
            text,
        )
    )
    if len(starts) != expected_count:
        raise ValueError(f"正文必须包含 {expected_count} 个 blocks")
    blocks = []
    for index, match in enumerate(starts):
        next_start = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        tail = text[match.end() : next_start]
        boundary = (
            re.search(r'"\s*}\s*,\s*$', tail)
            if index + 1 < len(starts)
            else re.search(r'"\s*}\s*]\s*}\s*$', tail)
        )
        if boundary is None:
            raise ValueError("正文 blocks 结构不完整")
        blocks.append(
            {
                "block_id": match.group(1),
                "content_text": _unescape_prose_text(tail[: boundary.start()]),
            }
        )
    return parse_prose_blocks({"blocks": blocks}, expected_count=expected_count)


def _unescape_prose_text(value: str) -> str:
    return (
        value.replace(r"\n", "\n")
        .replace(r"\t", "\t")
        .replace(r"\"", '"')
        .replace(r"\\", "\\")
    )


def recover_complete_prose_blocks(raw: str) -> list[dict]:
    """Recover only complete leading block objects from truncated JSON."""
    decoder = json.JSONDecoder()
    recovered = []
    for match in re.finditer(r'\{\s*"block_id"\s*:', str(raw or "")):
        try:
            value, _end = decoder.raw_decode(str(raw)[match.start() :])
        except json.JSONDecodeError:
            continue
        try:
            candidate = parse_prose_blocks({"blocks": [*recovered, value]})
        except ValueError:
            continue
        recovered = candidate
    return recovered


def assemble_prose_blocks(blocks: list[dict]) -> dict:
    normalized = parse_prose_blocks({"blocks": blocks})
    content_text = "\n\n".join(item["content_text"] for item in normalized)
    rows = []
    cursor = 0
    for index, item in enumerate(normalized):
        text = item["content_text"]
        start = cursor
        end = start + len(text)
        rows.append(
            {
                "block_id": item["block_id"],
                "start": start,
                "end": end,
                "char_count": len(re.sub(r"\s+", "", text)),
                "content_hash": value_hash(text),
            }
        )
        cursor = end + (2 if index < len(normalized) - 1 else 0)
    return {
        "content_text": content_text,
        "source_hash": value_hash(content_text),
        "char_count": len(re.sub(r"\s+", "", content_text)),
        "blocks": rows,
    }


def replace_prose_blocks(blocks: list[dict], replacements) -> list[dict]:
    normalized = parse_prose_blocks({"blocks": blocks})
    if isinstance(replacements, dict):
        replacement_map = dict(replacements)
    else:
        replacement_rows = list(replacements or [])
        replacement_map = {
            item.get("block_id"): item.get("content_text") for item in replacement_rows
        }
        if len(replacement_map) != len(replacement_rows):
            raise ValueError("replacement block ID 重复")
    known = {item["block_id"] for item in normalized}
    invalid = set(replacement_map).difference(known)
    if invalid:
        raise ValueError(f"replacement 引用了未知 block: {sorted(invalid)}")
    if not replacement_map:
        raise ValueError("replacement 不能为空")
    result = copy.deepcopy(normalized)
    for item in result:
        if item["block_id"] in replacement_map:
            item["content_text"] = replacement_map[item["block_id"]]
    return parse_prose_blocks({"blocks": result}, expected_count=len(normalized))


def repair_block_context(blocks: list[dict], failed_ids: set[str]) -> list[dict]:
    """Return failed blocks plus adjacent read-only blocks for temporal continuity."""
    indexes = set()
    for index, item in enumerate(blocks):
        if item.get("block_id") in failed_ids:
            indexes.update(range(max(0, index - 1), min(len(blocks), index + 2)))
    return [
        {**blocks[index], "editable": blocks[index].get("block_id") in failed_ids}
        for index in sorted(indexes)
    ]


def prose_token_budget(prose_input: dict) -> int:
    target = int(prose_input["chapter_length"]["target_chars"])
    return min(16_000, max(12_000, target * 3))
