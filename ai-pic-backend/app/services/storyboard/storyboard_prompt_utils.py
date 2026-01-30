from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.storyboard.langgraph_utils import (
    COMPOSITION_CYCLE,
    MOVEMENT_CYCLE,
    SHOT_CYCLE,
)

_SYSTEM_PREFIX_RE = re.compile(
    r"^\s*(?:\u7cfb\u7edf|system|assistant)\s*[\uFF1A:\uFF0C,]\s*",
    re.IGNORECASE,
)
_TAG_PREFIX_RE = re.compile(
    r"^\s*[\[\(\uFF08\u3010]\s*(?:\u7cfb\u7edf|system|assistant)\s*[\]\)\uFF09\u3011]\s*[\uFF1A:\uFF0C,]?\s*",
    re.IGNORECASE,
)
_SPEAKER_PREFIX_RE = re.compile(
    r"^\s*(?P<prefix>[^:\uFF1A\n]{1,12})[\uFF1A:]\s*(?P<body>.+)$"
)
_BLOCKED_PREFIXES = {
    "\u5730\u70b9",
    "\u65f6\u95f4",
    "\u573a\u666f",
    "\u955c\u5934",
    "\u666f\u522b",
    "\u8fd0\u955c",
    "\u6784\u56fe",
    "\u753b\u9762",
    "\u5185\u5bb9",
    "\u63cf\u8ff0",
    "\u63d0\u793a",
    "\u98ce\u683c",
    "\u4eba\u7269",
    "\u89d2\u8272",
    "scene",
    "shot",
    "camera",
    "composition",
    "prompt",
}


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    return text[:limit] + ("..." if len(text) > limit else "")


def _split_speaker_prefix(text: str) -> tuple[Optional[str], str]:
    match = _SPEAKER_PREFIX_RE.match(text or "")
    if not match:
        return None, text
    prefix = (match.group("prefix") or "").strip()
    body = (match.group("body") or "").strip()
    if not prefix:
        return None, text
    compact = prefix.replace(" ", "")
    if len(compact) > 10:
        return None, text
    lower = compact.lower()
    if any(token in lower for token in _BLOCKED_PREFIXES):
        return None, text
    if any(ch in compact for ch in ",.!?;:"):
        return None, text
    return prefix, body


def normalize_storyboard_text(text: str) -> str:
    raw = _compact_text(text)
    if not raw:
        return ""
    raw = _TAG_PREFIX_RE.sub("", raw)
    speaker, body = _split_speaker_prefix(raw)
    body = _SYSTEM_PREFIX_RE.sub("", body).strip()
    from app.services.audio.dialogue_processor import sanitize_dialogue_content

    body, action = sanitize_dialogue_content(body)
    body = _SYSTEM_PREFIX_RE.sub("", body).strip()

    parts = [p for p in (speaker, action, body) if p]
    return ", ".join(parts)


def _cycle_value(values: list[str], index: int) -> str:
    if not values:
        return ""
    return values[index % len(values)]


def _ensure_camera_fields(frame: Dict[str, Any], index: int) -> None:
    scene_offset = frame.get("scene_number") or 0
    try:
        scene_offset_int = int(scene_offset)
    except (TypeError, ValueError):
        scene_offset_int = 0
    if not frame.get("shot_type"):
        frame["shot_type"] = _cycle_value(SHOT_CYCLE, index + scene_offset_int)
    if not frame.get("camera_movement"):
        frame["camera_movement"] = _cycle_value(MOVEMENT_CYCLE, index)
    if not frame.get("composition"):
        frame["composition"] = _cycle_value(COMPOSITION_CYCLE, index)


def resolve_transition_data(
    prev_frame: Optional[Dict[str, Any]],
    frame: Dict[str, Any],
) -> Dict[str, Any]:
    if not prev_frame:
        return {"kind": "intro"}

    prev_scene = prev_frame.get("scene_number")
    curr_scene = frame.get("scene_number")
    if prev_scene is not None and curr_scene is not None and prev_scene != curr_scene:
        return {
            "kind": "scene_change",
            "from_scene": prev_scene,
            "to_scene": curr_scene,
        }

    prev_shot = prev_frame.get("shot_type")
    curr_shot = frame.get("shot_type")
    if prev_shot and curr_shot and prev_shot != curr_shot:
        return {
            "kind": "shot_change",
            "from_shot": prev_shot,
            "to_shot": curr_shot,
        }

    prev_move = prev_frame.get("camera_movement")
    curr_move = frame.get("camera_movement")
    if prev_move and curr_move and prev_move != curr_move:
        return {
            "kind": "movement_change",
            "from_move": prev_move,
            "to_move": curr_move,
        }

    prev_comp = prev_frame.get("composition")
    curr_comp = frame.get("composition")
    if prev_comp and curr_comp and prev_comp != curr_comp:
        return {
            "kind": "composition_change",
            "from_comp": prev_comp,
            "to_comp": curr_comp,
        }

    return {"kind": "match_cut"}


def render_storyboard_shot_prompt(
    *,
    description: str,
    frame: Dict[str, Any],
    transition: Dict[str, Any],
) -> str:
    variables = {
        "description": description,
        "shot_type": frame.get("shot_type"),
        "camera_movement": frame.get("camera_movement"),
        "composition": frame.get("composition"),
        "characters": frame.get("characters") or [],
        "transition": transition,
    }
    rendered = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_SHOT.value, variables
    )
    return _compact_text(rendered)


def render_keyframe_prompt(base_prompt: str, role: str) -> str:
    rendered = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_KEYFRAME.value,
        {"base_prompt": base_prompt, "role": role},
    )
    return _compact_text(rendered)


def apply_storyboard_prompt_optimizations(frames: Iterable[Dict[str, Any]]) -> None:
    prev_frame: Optional[Dict[str, Any]] = None
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue

        _ensure_camera_fields(frame, index)

        # Keep `description` as display-friendly text, but allow an explicit
        # `prompt_description` (visual-only) to drive downstream ai_prompt.
        display_description = normalize_storyboard_text(
            str(frame.get("description") or frame.get("ai_prompt") or "")
        )
        if display_description:
            frame["description"] = _truncate(display_description, 200)

        transition = resolve_transition_data(prev_frame, frame)
        prompt_description = normalize_storyboard_text(
            str(
                frame.get("prompt_description")
                or frame.get("description")
                or frame.get("ai_prompt")
                or ""
            )
        )
        prompt_text = render_storyboard_shot_prompt(
            description=prompt_description or (frame.get("description") or ""),
            frame=frame,
            transition=transition,
        )
        if prompt_text:
            frame["ai_prompt"] = _truncate(prompt_text, 500)

        base_prompt = frame.get("ai_prompt") or frame.get("description") or ""
        if base_prompt:
            frame["start_keyframe_prompt"] = _truncate(
                render_keyframe_prompt(base_prompt, "start"), 600
            )
            frame["end_keyframe_prompt"] = _truncate(
                render_keyframe_prompt(base_prompt, "end"), 600
            )

        prev_frame = frame
        if "characters" in frame:
            frame.pop("characters", None)
