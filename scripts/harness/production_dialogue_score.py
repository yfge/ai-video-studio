"""Dialogue substance checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_FILLER_DIALOGUE = {
    "嗯",
    "嗯嗯",
    "啊",
    "哦",
    "好",
    "好的",
    "好吧",
    "行",
    "可以",
    "知道了",
    "我知道了",
    "明白了",
    "是的",
    "不是",
    "没事",
    "怎么办",
    "怎么会这样",
}


def dialogue_failed_checks(
    scenes: list[dict[str, Any]], *, max_visible_chars: int = 15
) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        for dialogue_texts in _scene_dialogue_groups(scene):
            for content in dialogue_texts:
                if len(content) > max_visible_chars:
                    failed.append("dialogue_line_length")
                if content in _FILLER_DIALOGUE:
                    failed.append("dialogue_substance")
            if (
                len(dialogue_texts) > 1
                and len(set(dialogue_texts)) < len(dialogue_texts)
            ):
                failed.append("dialogue_progression_repetition")
    return failed


def _scene_dialogue_groups(scene: dict[str, Any]) -> list[list[str]]:
    groups: list[list[str]] = []
    scene_dialogue = scene.get("dialogue")
    if isinstance(scene_dialogue, list):
        groups.append(_compact_dialogue_lines(scene_dialogue))
    beat_lines: list[dict[str, Any]] = []
    beats = scene.get("beats")
    if not isinstance(beats, list):
        return [group for group in groups if group]
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        beat_dialogue = beat.get("dialogue") or beat.get("dialogue_lines") or []
        if isinstance(beat_dialogue, list):
            beat_lines.extend(line for line in beat_dialogue if isinstance(line, dict))
    groups.append(_compact_dialogue_lines(beat_lines))
    return [group for group in groups if group]


def _compact_dialogue_lines(lines: list[dict[str, Any]]) -> list[str]:
    return [
        _compact_text(str(line.get("line") or line.get("content") or ""))
        for line in lines
    ]


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
