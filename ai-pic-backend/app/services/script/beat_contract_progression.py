from __future__ import annotations

from typing import Any


def progression_issues(scene: Any) -> list[dict[str, Any]]:
    if len(scene.beats) < 2:
        return []

    screen_states = [_beat_screen_state(beat) for beat in scene.beats]
    if len(set(screen_states)) == len(screen_states):
        return []

    return [
        {
            "check_id": "beat_progression_repetition",
            "message": "scene beats must show distinct screen states",
            "scene_number": scene.scene_number,
            "beat_order_index": None,
            "evidence": {"screen_state_count": len(set(screen_states))},
        }
    ]


def _beat_screen_state(beat: Any) -> str:
    parts = [beat.visible_event]
    parts.extend(action.content for action in beat.action_lines)
    return _compact_text("".join(parts))


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
