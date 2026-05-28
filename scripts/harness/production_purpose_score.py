"""Dramatic-purpose checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_VAGUE_PURPOSE_PHRASES = (
    "推进剧情",
    "推动剧情",
    "故事继续",
    "铺垫剧情",
    "制造悬念",
    "留下悬念",
    "制造冲突",
    "推动冲突",
    "升级冲突",
    "出现转折",
    "发生反转",
    "完成转折",
    "承上启下",
    "情绪变化",
    "关系变化",
)


def purpose_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        beats = scene.get("beats")
        if not isinstance(beats, list):
            continue
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            purpose = _compact_text(str(beat.get("dramatic_purpose") or ""))
            if len(purpose) < 4 or any(
                phrase in purpose for phrase in _VAGUE_PURPOSE_PHRASES
            ):
                failed.append("beat_dramatic_purpose_specificity")
    return failed


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
