"""Scene-level extractors for scripts."""

from __future__ import annotations

from typing import Any

from app.models.script import Script
from app.models.story_structure import Scene


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
