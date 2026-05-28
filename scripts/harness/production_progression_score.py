"""Beat progression checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any


def progression_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        beats = scene.get("beats")
        if not isinstance(beats, list) or len(beats) < 2:
            continue
        screen_states = [
            _beat_screen_state(beat) for beat in beats if isinstance(beat, dict)
        ]
        if len(screen_states) > 1 and len(set(screen_states)) < len(screen_states):
            failed.append("beat_progression_repetition")
    return failed


def _beat_screen_state(beat: dict[str, Any]) -> str:
    parts = [str(beat.get("visible_event") or "")]
    parts.extend(_beat_action_texts(beat))
    return _compact_text("".join(parts))


def _beat_action_texts(beat: dict[str, Any]) -> list[str]:
    actions = beat.get("action") or beat.get("action_lines") or []
    if not isinstance(actions, list):
        return []
    texts: list[str] = []
    for item in actions:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict) and item.get("content"):
            texts.append(str(item["content"]))
    return texts


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
