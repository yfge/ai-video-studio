"""
Dialogue processing utilities.

Provides functions for extracting and processing dialogue from scripts,
including text sanitization, scene extraction, and segment planning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence

from app.models.script import Script
from app.models.story_structure import Scene, SceneBeat


# Regex patterns for dialogue processing
_ONLY_PUNCT_OR_SPACE = re.compile(
    r"^[\s\.\,\!\?\-\—\_\~\·\…\，\。\！\？\、\：\；\"\"\(\)\（\）]+$"
)

_LEADING_INLINE_ACTION_RE = re.compile(
    r"^\s*[\(\（\[\【](?P<action>[^)\）\]\】]{1,200})[\)\）\]\】]\s*"
)
_TRAILING_INLINE_ACTION_RE = re.compile(
    r"\s*[\(\（\[\【](?P<action>[^)\）\]\】]{1,200})[\)\）\]\】]\s*$"
)
_SPEECH_ATTR_RE = re.compile(
    r"^\s*(?P<attr>.{1,80}?)(?P<sep>[:：]|\s+|“|\"|‘|'|「|『)(?P<text>.+)$"
)
_TRIVIAL_SPEECH_ATTR_RE = re.compile(
    r"^(?:我|你|他|她|它|我们|你们|他们|她们|大家|众人|所有人)(?:们)?(?:说|说道|问|问道|答|答道)$"
)

_SPEECH_ATTR_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            "低声说", "轻声说", "小声说", "大声说", "笑着说", "冷冷地说",
            "嘀咕道", "呢喃道", "咆哮道", "吼道", "喊道", "说道",
            "问道", "答道", "说", "问", "答",
        },
        key=len,
        reverse=True,
    )
)


def norm_name(name: str) -> str:
    """Normalize character name for comparison."""
    return "".join((name or "").strip().lower().split())


def looks_like_silence(text: str) -> bool:
    """Check if text represents silence or pause."""
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if _ONLY_PUNCT_OR_SPACE.match(cleaned):
        return True
    lowered = cleaned.lower()
    if lowered in {"...", "……", "…", "（沉默）", "(silence)", "[silence]"}:
        return True
    return False


def sanitize_dialogue_content(
    content: str,
    *,
    action: str | None = None,
) -> tuple[str, str | None]:
    """
    Remove inline stage directions from dialogue text.

    Examples:
    - "（叹气）你好" -> text="你好", action+="叹气"
    - "叹了一口气，站起来说：你好" -> text="你好", action+="叹了一口气，站起来说"
    """
    text = str(content or "").strip()
    actions: list[str] = []

    if isinstance(action, str) and action.strip():
        actions.append(action.strip())

    # Extract leading inline actions
    while True:
        m = _LEADING_INLINE_ACTION_RE.match(text)
        if not m:
            break
        inline = m.group("action").strip()
        if inline:
            actions.append(inline)
        text = text[m.end():].strip()

    # Extract trailing inline actions
    while True:
        m = _TRAILING_INLINE_ACTION_RE.search(text)
        if not m:
            break
        inline = m.group("action").strip()
        if inline:
            actions.append(inline)
        text = text[:m.start()].strip()

    # Extract speech attribution
    m = _SPEECH_ATTR_RE.match(text)
    if m:
        attr = (m.group("attr") or "").strip()
        attr_no_space = "".join(attr.split())
        suffix_ok = any(attr_no_space.endswith(suf) for suf in _SPEECH_ATTR_SUFFIXES)
        if (
            suffix_ok
            and attr_no_space
            and not _TRIVIAL_SPEECH_ATTR_RE.match(attr_no_space)
        ):
            actions.append(attr)
            text = m.group("text").strip()

    combined_action = "；".join(actions) if actions else None
    return text, combined_action


def extract_scene_number(scene: Scene) -> int:
    """Extract scene number from Scene object."""
    raw = scene.scene_number if scene else None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            return 0
    return 0


def extract_dialogues_for_scene(
    script: Script,
    scene_number: int,
) -> list[dict[str, Any]]:
    """Extract dialogue entries for a specific scene from script."""
    raw_content = script.content if script else None
    if not isinstance(raw_content, dict):
        return []

    dialogue_list = raw_content.get("dialogues") or []
    if not isinstance(dialogue_list, list):
        return []

    result: list[dict[str, Any]] = []
    for item in dialogue_list:
        if not isinstance(item, dict):
            continue
        item_scene = item.get("scene_number")
        if item_scene is None:
            continue
        try:
            if int(item_scene) == scene_number:
                result.append(item)
        except (TypeError, ValueError):
            continue

    return result


def extract_stage_for_scene(
    script: Script,
    scene_number: int,
) -> list[dict[str, Any]]:
    """Extract stage directions for a specific scene from script."""
    raw_content = script.content if script else None
    if not isinstance(raw_content, dict):
        return []

    stage_list = raw_content.get("stage_directions") or []
    if not isinstance(stage_list, list):
        return []

    result: list[dict[str, Any]] = []
    for item in stage_list:
        if not isinstance(item, dict):
            continue
        item_scene = item.get("scene_number")
        if item_scene is None:
            continue
        try:
            if int(item_scene) == scene_number:
                result.append(item)
        except (TypeError, ValueError):
            continue

    return result


@dataclass(frozen=True)
class PlannedSegment:
    """A planned audio segment for a scene."""
    kind: str  # dialogue | action | pause
    text: str
    speaker_name: str | None = None
    emotion: str | None = None
    action: str | None = None
    timing: str | None = None  # start/mid/end (for action)
    planned_duration_ms: int | None = None


def plan_scene_segments(
    *,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
    pause_after_dialogue_ms: int = 300,
    action_base_ms: int = 800,
    action_per_char_ms: int = 20,
    action_max_ms: int = 3000,
) -> list[PlannedSegment]:
    """
    Build an ordered segment plan for a scene.

    - Dialogue: TTS
    - Action: silence placeholder (MVP)
    - Pause: silence
    """
    stages_start: list[str] = []
    stages_mid: list[str] = []
    stages_end: list[str] = []

    for sd in stage_directions:
        if not isinstance(sd, dict):
            continue
        content = str(sd.get("content") or "").strip()
        if not content:
            continue
        timing = str(sd.get("timing") or "mid").strip().lower()
        if timing in {"start", "begin", "opening"}:
            stages_start.append(content)
        elif timing in {"end", "closing"}:
            stages_end.append(content)
        else:
            stages_mid.append(content)

    planned: list[PlannedSegment] = []

    def _action_duration_ms(content: str) -> int:
        length = len(content)
        return min(
            action_max_ms,
            max(action_base_ms, action_base_ms + length * action_per_char_ms),
        )

    # Add start stage directions
    for content in stages_start:
        planned.append(
            PlannedSegment(
                kind="action",
                text=content,
                timing="start",
                planned_duration_ms=_action_duration_ms(content),
            )
        )

    mid_inserted = False

    # Process dialogues
    for idx, dlg in enumerate(dialogues):
        speaker = str(dlg.get("character") or "旁白")
        content = str(dlg.get("content") or "").strip()
        emotion = (
            str(dlg.get("emotion") or "").strip()
            if isinstance(dlg.get("emotion"), str)
            else None
        )
        emotion = emotion or None
        action = (
            str(dlg.get("action") or "").strip()
            if isinstance(dlg.get("action"), str)
            else None
        )
        action = action or None

        if looks_like_silence(content):
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text=content or "…",
                    speaker_name=speaker,
                    emotion=emotion,
                    action=action,
                    planned_duration_ms=800,
                )
            )
        else:
            planned.append(
                PlannedSegment(
                    kind="dialogue",
                    text=content,
                    speaker_name=speaker,
                    emotion=emotion,
                    action=action,
                )
            )

        # Add pause after dialogue
        if pause_after_dialogue_ms > 0:
            planned.append(
                PlannedSegment(
                    kind="pause",
                    text="",
                    planned_duration_ms=pause_after_dialogue_ms,
                )
            )

        # Insert mid-stage directions after first dialogue
        if not mid_inserted and idx == 0 and stages_mid:
            for content in stages_mid:
                planned.append(
                    PlannedSegment(
                        kind="action",
                        text=content,
                        timing="mid",
                        planned_duration_ms=_action_duration_ms(content),
                    )
                )
            mid_inserted = True

    # Add any remaining mid-stage directions at end
    if not mid_inserted and stages_mid:
        for content in stages_mid:
            planned.append(
                PlannedSegment(
                    kind="action",
                    text=content,
                    timing="mid",
                    planned_duration_ms=_action_duration_ms(content),
                )
            )

    # Add end stage directions
    for content in stages_end:
        planned.append(
            PlannedSegment(
                kind="action",
                text=content,
                timing="end",
                planned_duration_ms=_action_duration_ms(content),
            )
        )

    return planned
