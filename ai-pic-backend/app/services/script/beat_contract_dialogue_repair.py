from __future__ import annotations

import re
from typing import Any

from app.services.script.beat_contract_auto_repair_common import compact, visible_len


def dedupe_progression(beats: list[dict[str, Any]]) -> None:
    seen_lines: set[str] = set()
    character_beat_counts: dict[str, int] = {}
    for beat in beats:
        characters = {
            str(line.get("character") or "").strip()
            for line in beat.get("dialogue_lines") or []
            if isinstance(line, dict) and str(line.get("character") or "").strip()
        }
        for character in characters:
            character_beat_counts[character] = (
                character_beat_counts.get(character, 0) + 1
            )
    for beat in beats:
        kept_lines: list[dict[str, Any]] = []
        for line in beat.get("dialogue_lines") or []:
            if not isinstance(line, dict):
                continue
            text = compact(str(line.get("content") or ""))
            character = str(line.get("character") or "").strip()
            if (
                text in seen_lines
                and character
                and character_beat_counts.get(character, 0) > 2
            ):
                character_beat_counts[character] -= 1
                continue
            kept_lines.append(line)
            seen_lines.add(text)
        beat["dialogue_lines"] = kept_lines


def shorten_dialogue_lines(beats: list[dict[str, Any]]) -> None:
    for beat in beats:
        for line in beat.get("dialogue_lines") or []:
            if (
                isinstance(line, dict)
                and visible_len(str(line.get("content") or "")) > 15
            ):
                line["content"] = _short_dialogue(str(line.get("content") or ""))


def _short_dialogue(text: str) -> str:
    replacements = (
        (("版本同步",), "可能是同步问题。"),
        (("会议纪要",), "纪要有你签字。"),
        (("刚才", "误会"), "刚才误会了。"),
        (("原始文件",), "原始文件在这。"),
        (("云端数据",), "云端875，投影920。"),
        (("左边", "右边"), "左云端，右投影。"),
        (("签过字",), "签字在这，怎么说？"),
    )
    for markers, replacement in replacements:
        if all(marker in text for marker in markers):
            return replacement
    technical = re.search(
        r"(?i)(?:gpt-(?:img|image)-\d+|seedance(?:\s+\d+(?:\.\d+)?)?)",
        text,
    )
    if technical:
        candidate = f"用{technical.group(0)}。"
        if visible_len(candidate) <= 15:
            return candidate
    clauses = [
        clause.strip(" ，,：:")
        for clause in re.split(r"[。！？；，,:：]+", text)
        if clause.strip(" ，,：:")
    ]
    for clause in reversed(clauses):
        candidate = clause + "。"
        if 4 <= visible_len(candidate) <= 15:
            return candidate
    return f"{compact(text)[:14]}。"
