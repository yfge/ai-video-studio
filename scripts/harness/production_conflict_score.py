"""Scene conflict checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_VAGUE_CONFLICT_PHRASES = (
    "推进剧情",
    "推动剧情",
    "剧情继续",
    "故事继续",
    "制造悬念",
    "留下悬念",
    "制造冲突",
    "推动冲突",
    "升级冲突",
    "出现转折",
    "发生反转",
    "完成转折",
    "关系变化",
    "情绪变化",
)


def conflict_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        if not _is_specific_text(_scene_field(scene, "question")):
            failed.append("scene_conflict_question")
        if not _is_specific_text(_scene_field(scene, "turn")):
            failed.append("scene_conflict_turn")
    return failed


def _scene_field(scene: dict[str, Any], field: str) -> str:
    value = scene.get(field)
    if value:
        return str(value)
    conflict = scene.get("conflict")
    if isinstance(conflict, dict):
        return str(conflict.get(field) or "")
    return ""


def _is_specific_text(value: str) -> bool:
    text = _compact_text(value)
    if len(text) < 4:
        return False
    return not any(phrase in text for phrase in _VAGUE_CONFLICT_PHRASES)


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
