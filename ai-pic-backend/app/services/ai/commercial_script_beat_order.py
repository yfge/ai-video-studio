from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def has_beat_ordered_items(
    dialogues: List[Dict[str, Any]], stage_directions: List[Dict[str, Any]]
) -> bool:
    return any(_to_int(item.get("beat_order_index")) for item in dialogues) or any(
        _to_int(item.get("beat_order_index")) for item in stage_directions
    )


def append_beat_ordered_scene(
    lines: List[str],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
) -> None:
    for order in _beat_orders(dialogues, stage_directions):
        seen_stage: set[str] = set()
        for direction in _items_for_beat(stage_directions, order):
            stage_line = _stage_line(direction)
            if stage_line in seen_stage:
                continue
            lines.append(stage_line)
            seen_stage.add(stage_line)
        for dialogue in _items_for_beat(dialogues, order):
            lines.append(_dialogue_line(dialogue))


def _beat_orders(
    dialogues: List[Dict[str, Any]], stage_directions: List[Dict[str, Any]]
) -> list[int]:
    return sorted(
        {
            order
            for item in [*stage_directions, *dialogues]
            if (order := _to_int(item.get("beat_order_index"))) is not None
        }
    )


def _items_for_beat(
    items: List[Dict[str, Any]], beat_order_index: int
) -> List[Dict[str, Any]]:
    return [
        item
        for item in items
        if _to_int(item.get("beat_order_index")) == beat_order_index
    ]


def _stage_line(direction: Dict[str, Any]) -> str:
    content = str(
        direction.get("content")
        or direction.get("direction")
        or direction.get("description")
        or ""
    ).strip()
    if not content:
        content = "镜头压近人物反应。"
    if content.startswith("▲"):
        return content
    return f"▲{content}"


def _dialogue_line(dialogue: Dict[str, Any]) -> str:
    speaker = _clean_speaker(str(dialogue.get("character") or "旁白")) or "旁白"
    content = str(
        dialogue.get("content") or dialogue.get("line") or dialogue.get("text") or ""
    ).strip()
    state = _dialogue_state(dialogue)
    if state:
        return f"{speaker}({state})：{content}"
    return f"{speaker}：{content}"


def _dialogue_state(dialogue: Dict[str, Any]) -> str:
    state = str(dialogue.get("emotion") or dialogue.get("action") or "").strip()
    state = re.sub(r"[。！？!?：:]+$", "", state)
    if len(state) > 18:
        state = state[:18]
    return state


def _clean_speaker(speaker: str) -> str:
    return re.sub(r"\s+", "", speaker.strip())


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
