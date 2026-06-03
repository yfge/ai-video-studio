"""Script content normalization helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.ai.script_text import build_script_text
from app.services.script.scene_utils import to_int


def normalize_script_content(
    ai_content: Dict[str, Any],
    *,
    format_type: str,
    language: str,
    default_scenes: Optional[List[Dict[str, Any]]] = None,
    episode_number: Optional[int] = None,
    template_style: Optional[str] = None,
    target_chars_per_episode: Optional[int] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize AI script payloads into the shape expected downstream."""
    normalized = dict(ai_content or {})
    fallback_scenes = default_scenes or []

    raw_scenes = normalized.get("scenes")
    if not isinstance(raw_scenes, list) or len(raw_scenes) == 0:
        raw_scenes = fallback_scenes
    scenes: List[Dict[str, Any]] = []
    for idx, scene in enumerate(raw_scenes, start=1):
        base = (
            dict(scene)
            if isinstance(scene, dict)
            else {"description": str(scene) if scene is not None else ""}
        )
        scene_no = to_int(base.get("scene_number")) or idx
        conflict = (
            base.get("conflict") if isinstance(base.get("conflict"), dict) else {}
        )
        desc = (
            base.get("description")
            or base.get("summary")
            or conflict.get("question")
            or base.get("slug_line")
            or base.get("story_beat")
            or base.get("title")
        )
        base["scene_number"] = scene_no
        if desc:
            base.setdefault("description", desc)
            base.setdefault("summary", desc)
        if not base.get("slug_line"):
            location = base.get("location") or base.get("place")
            time_of_day = base.get("time_of_day") or base.get("time")
            if location and time_of_day:
                base["slug_line"] = f"{location} - {time_of_day}"
            elif desc:
                base["slug_line"] = desc[:80]
        scenes.append(base)

    metadata = normalized.get("metadata") or {}
    if metadata.get("estimated_duration") is not None and not isinstance(
        metadata.get("estimated_duration"), str
    ):
        metadata["estimated_duration"] = str(metadata["estimated_duration"])
    if scenes and not metadata.get("total_scenes"):
        metadata["total_scenes"] = len(scenes)
    normalized["metadata"] = metadata
    normalized["scenes"] = scenes

    raw_dialogues = normalized.get("dialogues") or []
    dialogues: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_dialogues, start=1):
        if isinstance(item, str):
            dialogues.append(
                {
                    "scene_number": (
                        scenes[idx - 1]["scene_number"]
                        if idx - 1 < len(scenes)
                        else idx
                    ),
                    "content": item,
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        dialog = dict(item)
        content = (
            dialog.get("content")
            or dialog.get("line")
            or dialog.get("text")
            or dialog.get("dialogue")
        )
        if not content:
            continue
        dialog["content"] = content
        sn = to_int(dialog.get("scene_number"))
        if sn is None:
            dialog["scene_number"] = (
                scenes[idx - 1]["scene_number"] if idx - 1 < len(scenes) else idx
            )
        dialogues.append(dialog)

    raw_stage = normalized.get("stage_directions") or []
    stage_directions: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_stage, start=1):
        if isinstance(item, str):
            stage_directions.append(
                {
                    "scene_number": (
                        scenes[idx - 1]["scene_number"]
                        if idx - 1 < len(scenes)
                        else idx
                    ),
                    "content": item,
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        direction = dict(item)
        content = (
            direction.get("content")
            or direction.get("direction")
            or direction.get("description")
        )
        if not content:
            continue
        direction["content"] = content
        sn = to_int(direction.get("scene_number"))
        if sn is None:
            direction["scene_number"] = (
                scenes[idx - 1]["scene_number"] if idx - 1 < len(scenes) else idx
            )
        stage_directions.append(direction)

    if not scenes:
        scene_numbers = {
            item.get("scene_number")
            for item in dialogues
            if isinstance(item, dict) and item.get("scene_number")
        }
        scene_numbers |= {
            item.get("scene_number")
            for item in stage_directions
            if isinstance(item, dict) and item.get("scene_number")
        }
        scene_numbers = {sn for sn in scene_numbers if sn is not None}
        for idx, sn in enumerate(sorted(scene_numbers)):
            scenes.append(
                {
                    "scene_number": to_int(sn) or idx + 1,
                    "slug_line": f"Scene {sn}",
                    "summary": "",
                    "description": "",
                }
            )

    normalized["scenes"] = scenes
    normalized["dialogues"] = dialogues
    normalized["stage_directions"] = stage_directions

    content_value = normalized.get("content")
    if isinstance(content_value, dict):
        content_text = content_value.get("content") or ""
    else:
        content_text = content_value or ""
    if not content_text:
        content_text = build_script_text(
            scenes,
            dialogues,
            stage_directions,
            format_type=format_type,
            language=language,
            episode_number=episode_number,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=title,
        )
    normalized["content"] = content_text
    return normalized
