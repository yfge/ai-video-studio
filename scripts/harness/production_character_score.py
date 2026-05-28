"""Character-anchor checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_GENERIC_SPEAKERS = {
    "角色",
    "角色A",
    "角色B",
    "人物",
    "某人",
    "主角",
    "男主",
    "女主",
    "男主角",
    "女主角",
    "旁白",
    "叙述者",
    "narrator",
    "speaker",
}


def character_anchor_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed: list[str] = []
    for scene in scenes:
        beats = scene.get("beats") if isinstance(scene.get("beats"), list) else []
        speaker_counts: dict[str, int] = {}
        has_dialogue = False

        for line in _scene_dialogue(scene):
            has_dialogue = True
            speaker = _speaker_name(line)
            if not _is_specific_speaker(speaker):
                failed.append("dialogue_character_specificity")
                continue
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1

        if has_dialogue and len(beats) > 1 and max(speaker_counts.values(), default=0) < 2:
            failed.append("scene_protagonist_presence")

    return failed


def _scene_dialogue(scene: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    scene_dialogue = scene.get("dialogue")
    if isinstance(scene_dialogue, list):
        lines.extend(line for line in scene_dialogue if isinstance(line, dict))
    beats = scene.get("beats")
    if not isinstance(beats, list):
        return lines
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        beat_dialogue = beat.get("dialogue") or beat.get("dialogue_lines") or []
        if isinstance(beat_dialogue, list):
            lines.extend(line for line in beat_dialogue if isinstance(line, dict))
    return lines


def _speaker_name(line: dict[str, Any]) -> str:
    return _compact_text(str(line.get("speaker") or line.get("character") or ""))


def _is_specific_speaker(speaker: str) -> bool:
    if len(speaker) < 2:
        return False
    return speaker not in _GENERIC_SPEAKERS


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
