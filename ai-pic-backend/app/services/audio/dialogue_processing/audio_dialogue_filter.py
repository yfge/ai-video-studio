"""Classify script dialogue entries for spoken audio generation."""

from __future__ import annotations

import re
from typing import Any, Sequence

from app.services.audio.dialogue_processing.prose_dialogue_splitter import (
    split_prose_dialogue_block,
)

_HAS_QUOTE_RE = re.compile(r"[“\"「『‘]")

_GENERIC_NARRATION_SPEAKERS = {
    "",
    "旁白",
    "画外音",
    "旁白/画外音",
    "narrator",
    "voiceover",
}

_ACTION_PROSE_PREFIXES = (
    "冲突升级：",
    "冲突升级:",
    "爽点：",
    "爽点:",
    "卡点：",
    "卡点:",
)

_NARRATION_CUES = (
    "女主",
    "男主",
    "镜头",
    "特写",
    "屏幕",
    "画面",
    "会议室",
    "办公区",
    "公寓",
    "咖啡馆",
    "面试现场",
)


def should_treat_dialogue_as_action_for_audio(item: dict[str, Any]) -> bool:
    """Return True for generic narrator prose that should stay silent/action."""
    if not isinstance(item, dict):
        return False
    speaker = _speaker_name(item).lower()
    if speaker not in _GENERIC_NARRATION_SPEAKERS:
        return False
    text = _dialogue_text(item)
    if not text:
        return False
    if _starts_with_action_prose_prefix(text):
        return True
    if item.get("fallback") is True or item.get("fallback_reason"):
        return _looks_like_prose_narration(text)
    if len(text) >= 160 and _HAS_QUOTE_RE.search(text):
        return _looks_like_prose_narration(text)
    return False


def split_audio_dialogues_and_action_blocks(
    dialogues: Sequence[dict[str, Any]],
    *,
    alias_to_canonical: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split spoken dialogue from fallback prose that should become action."""
    repaired: list[dict[str, Any]] = []
    action_blocks: list[dict[str, Any]] = []
    for dlg in dialogues or []:
        if not isinstance(dlg, dict):
            continue
        speaker = str(dlg.get("character") or "旁白")
        content = str(dlg.get("content") or "").strip()
        if not content:
            continue

        if speaker in {"旁白", "路人", "店员"} and _HAS_QUOTE_RE.search(content):
            split = split_prose_dialogue_block(
                content,
                alias_to_canonical=alias_to_canonical,
                default_speaker="旁白",
            )
            if len(split) >= 2:
                for seg in split:
                    seg_out = dict(seg)
                    if dlg.get("emotion") is not None:
                        seg_out["emotion"] = dlg.get("emotion")
                    if dlg.get("action") is not None:
                        seg_out["action"] = dlg.get("action")
                    repaired.append(seg_out)
                continue

        if should_treat_dialogue_as_action_for_audio(dlg):
            action_blocks.append(
                {
                    "type": "action",
                    "timing": "mid",
                    "content": content,
                    "scene_number": dlg.get("scene_number"),
                    "source": "dialogue_fallback",
                }
            )
            continue

        repaired.append(dlg)

    return repaired, action_blocks


def repair_scene_dialogues_for_audio(
    dialogues: Sequence[dict[str, Any]],
    *,
    alias_to_canonical: dict[str, str],
) -> list[dict[str, Any]]:
    """Repair a scene dialogue list by splitting narrations when possible."""
    repaired, _ = split_audio_dialogues_and_action_blocks(
        dialogues,
        alias_to_canonical=alias_to_canonical,
    )
    return repaired


def _speaker_name(item: dict[str, Any]) -> str:
    return str(
        item.get("character") or item.get("speaker_name") or item.get("speaker") or ""
    ).strip()


def _dialogue_text(item: dict[str, Any]) -> str:
    return str(
        item.get("content") or item.get("text") or item.get("dialogue_excerpt") or ""
    ).strip()


def _starts_with_action_prose_prefix(text: str) -> bool:
    return text.startswith(_ACTION_PROSE_PREFIXES)


def _looks_like_prose_narration(text: str) -> bool:
    value = text.strip()
    if not value:
        return False
    if _starts_with_action_prose_prefix(value):
        return True
    if len(value) < 120:
        return False
    return any(cue in value for cue in _NARRATION_CUES) and "。" in value
