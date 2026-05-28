"""Filmability checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_UNFILMABLE_PHRASES = (
    "意识到",
    "明白",
    "想到",
    "感到",
    "感觉到",
    "内心",
    "心里",
    "情绪",
    "崩溃",
    "命运",
    "关系变化",
    "心理变化",
    "产生变化",
)


def filmability_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        beats = scene.get("beats")
        if not isinstance(beats, list):
            continue
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            if _is_unfilmable_text(beat.get("visible_event")):
                failed.append("beat_visible_event_specificity")
            actions = beat.get("action") or beat.get("action_lines") or []
            if isinstance(actions, list) and actions:
                action_text = " ".join(_action_text(item) for item in actions)
                if _is_unfilmable_text(action_text):
                    failed.append("beat_action_specificity")
    return failed


def _action_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("content") or "")
    return ""


def _is_unfilmable_text(value: Any) -> bool:
    text = str(value or "")
    return any(phrase in text for phrase in _UNFILMABLE_PHRASES)
