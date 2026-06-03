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

    dialogue_list = _script_list_field(script, "dialogues")

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

    stage_list = _script_list_field(script, "stage_directions")

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


def _script_list_field(script: Script | None, field_name: str) -> list[Any]:
    if not script:
        return []

    direct_value = getattr(script, field_name, None)
    if isinstance(direct_value, list):
        return direct_value

    raw_content = getattr(script, "content", None)
    if not isinstance(raw_content, dict):
        return []

    embedded_value = raw_content.get(field_name) or []
    if isinstance(embedded_value, list):
        return embedded_value
    return []
