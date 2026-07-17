from __future__ import annotations

from typing import Any

LOW_VALUE_CHARACTERS = {"录音", "短信", "旁白"}


def has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def compact(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def visible_len(text: str) -> int:
    return len(compact(text))


def to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def scene_role(index: int, count: int) -> str:
    return "hook" if index == 1 else "cliffhanger" if index == count else "escalation"


def preferred_character(beats: list[dict[str, Any]]) -> str | None:
    counts: dict[str, int] = {}
    for beat in beats:
        for line in beat.get("dialogue_lines") or []:
            character = (
                str(line.get("character") or "").strip()
                if isinstance(line, dict)
                else ""
            )
            if character and character not in LOW_VALUE_CHARACTERS:
                counts[character] = counts.get(character, 0) + 1
    return max(counts, key=counts.get) if counts else None


def beat_screen_text(beat: dict[str, Any]) -> str:
    return "".join(
        str(action.get("content") or "")
        for action in beat.get("action_lines", [])
        if isinstance(action, dict)
    )


def beat_text(beat: dict[str, Any]) -> str:
    return compact(str(beat.get("visible_event") or "") + beat_screen_text(beat))


def scene_screen_text(beats: list[dict[str, Any]]) -> str:
    return compact(
        "".join(
            str(beat.get("visible_event") or "") + beat_screen_text(beat)
            for beat in beats
        )
    )
