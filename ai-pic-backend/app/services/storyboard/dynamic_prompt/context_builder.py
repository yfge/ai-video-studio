"""Build scene-level script context for dynamic storyboard prompt generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.storyboard.dynamic_prompt.character_context import (
    build_frame_characters,
    character_appearance,
)

MAX_DIALOGUES = 6
MAX_STAGE_NOTES = 4
DIALOGUE_CHAR_LIMIT = 80
STORY_TONE_CHAR_LIMIT = 150
NEIGHBOR_SUMMARY_LIMIT = 80


def _trim(value: Any, limit: int) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_story_tone(script: Any) -> str:
    """Summarize story/episode tone from the ORM relations in one line."""
    bits: List[str] = []
    episode = getattr(script, "episode", None)
    story = getattr(episode, "story", None) if episode is not None else None
    if story is not None:
        if getattr(story, "title", None):
            bits.append(f"《{story.title}》")
        if getattr(story, "genre", None):
            bits.append(str(story.genre))
        if getattr(story, "theme", None):
            bits.append(_trim(story.theme, 40))
        if getattr(story, "world_building", None):
            bits.append(_trim(story.world_building, 60))
    if episode is not None and getattr(episode, "title", None):
        bits.append(f"第{getattr(episode, 'episode_number', '?')}集 {episode.title}")
    return _trim("，".join(bit for bit in bits if bit), STORY_TONE_CHAR_LIMIT)


def find_scene(script: Any, scene_number: Optional[int]) -> Dict[str, Any]:
    """Locate the scene dict in script.scenes by scene_number (1-based fallback)."""
    scenes = getattr(script, "scenes", None) or []
    if scene_number is not None:
        for raw in scenes:
            if (
                isinstance(raw, dict)
                and _to_int(raw.get("scene_number")) == scene_number
            ):
                return raw
        index = scene_number - 1
        if 0 <= index < len(scenes) and isinstance(scenes[index], dict):
            return scenes[index]
    return {}


def build_scene_info(script: Any, scene_number: Optional[int]) -> Dict[str, Any]:
    scene = find_scene(script, scene_number)
    return {
        "scene_number": scene_number if scene_number is not None else "未知",
        "location": _trim(scene.get("location") or scene.get("place"), 50),
        "time": _trim(scene.get("time") or scene.get("period"), 40),
        "description": _trim(scene.get("description"), 160),
    }


def collect_scene_items(
    items: Any,
    scene_number: Optional[int],
    content_keys: tuple,
    limit: int,
) -> List[str]:
    collected: List[str] = []
    for item in items or []:
        if isinstance(item, dict):
            sn = _to_int(item.get("scene_number"))
            content = next(
                (item.get(key) for key in content_keys if item.get(key)), None
            )
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        collected.append(_trim(content, DIALOGUE_CHAR_LIMIT))
        if len(collected) >= limit:
            break
    return collected


def build_scene_characters(
    scene_number: Optional[int],
    ref_ctx: Any,
    frame_descriptions: List[str],
) -> List[Dict[str, str]]:
    """Resolve characters appearing in the scene with their appearance text.

    Primary source: scene->shot character bindings in ImageRefContext.
    Fallback: alias-name matching against the frame descriptions.
    """
    char_ids: List[int] = []
    scene_obj = (
        ref_ctx.scene_by_number.get(scene_number) if scene_number is not None else None
    )
    if scene_obj is not None:
        char_ids = sorted(ref_ctx.scene_char_ids.get(scene_obj.id) or set())
    if not char_ids and getattr(ref_ctx, "name_to_vip_id", None):
        joined = " ".join(frame_descriptions)
        matched: List[int] = []
        for alias, vid in ref_ctx.name_to_vip_id.items():
            if alias and alias in joined and vid not in matched:
                matched.append(vid)
            if len(matched) >= 4:
                break
        char_ids = matched

    characters: List[Dict[str, str]] = []
    for cid in char_ids[:4]:
        vip = ref_ctx.vip_map.get(cid)
        if vip is None:
            continue
        name = getattr(vip, "name", None) or f"角色{cid}"
        appearance = character_appearance(vip)
        if appearance:
            characters.append({"name": str(name), "appearance": appearance})
    return characters


def build_scene_context(
    script: Any,
    scene_number: Optional[int],
    ref_ctx: Any,
    frame_descriptions: List[str],
    *,
    style: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble the full template context for one scene."""
    return {
        "story_tone": build_story_tone(script),
        "style": _trim(style, 120) if style else "",
        "scene": build_scene_info(script, scene_number),
        "characters": build_scene_characters(scene_number, ref_ctx, frame_descriptions),
        "dialogues": collect_scene_items(
            getattr(script, "dialogues", None),
            scene_number,
            ("content", "text", "line"),
            MAX_DIALOGUES,
        ),
        "stage_notes": collect_scene_items(
            getattr(script, "stage_directions", None),
            scene_number,
            ("content", "direction", "description"),
            MAX_STAGE_NOTES,
        ),
    }


def build_frame_input(
    frames: List[dict],
    index: int,
    *,
    scene_characters: List[Dict[str, str]] | None = None,
    ref_ctx: Any = None,
) -> Dict[str, Any]:
    """Build one frame's template input with neighbor summaries for continuity."""
    frame = frames[index]
    prev_frame = frames[index - 1] if index > 0 else None
    next_frame = frames[index + 1] if index + 1 < len(frames) else None

    def _summary(neighbor: Optional[dict]) -> str:
        if not isinstance(neighbor, dict):
            return ""
        return _trim(
            neighbor.get("description") or neighbor.get("ai_prompt"),
            NEIGHBOR_SUMMARY_LIMIT,
        )

    description = _trim(frame.get("description") or frame.get("ai_prompt"), 200)
    visual_context = _trim(frame.get("prompt_description"), 260)
    if visual_context == description:
        visual_context = ""
    return {
        "frame_index": index,
        "shot_type": frame.get("shot_type") or "",
        "camera_movement": frame.get("camera_movement") or "",
        "composition": frame.get("composition") or "",
        "duration": frame.get("duration_seconds"),
        "description": description,
        "characters": build_frame_characters(
            frame,
            scene_characters or [],
            ref_ctx=ref_ctx,
        ),
        "visual_context": visual_context,
        "prev_summary": _summary(prev_frame),
        "next_summary": _summary(next_frame),
    }


def group_target_frames_by_scene(
    frames: List[dict], target_indexes: List[int]
) -> Dict[Optional[int], List[int]]:
    """Group target frame indexes by scene_number, preserving frame order."""
    groups: Dict[Optional[int], List[int]] = {}
    for idx in target_indexes:
        if idx < 0 or idx >= len(frames) or not isinstance(frames[idx], dict):
            continue
        sn = _to_int(frames[idx].get("scene_number"))
        groups.setdefault(sn, []).append(idx)
    return groups
