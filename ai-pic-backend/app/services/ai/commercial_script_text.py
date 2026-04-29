from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def build_commercial_vertical_text(
    *,
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    episode_number: int,
    target_chars_per_episode: Optional[int],
    title: Optional[str],
) -> str:
    ordered_scenes = scenes or [{"scene_number": 1, "summary": title or "冲突爆发"}]
    lines: List[str] = [f"第{episode_number}集"]
    if not _first_lines_have_hook(lines + [_scene_summary(ordered_scenes[0])]):
        lines.append("▲【音效】砰！画面直接切入冲突现场，所有人猛地看向主角。")
    dialogues_by_scene = _group_by_scene(dialogues)
    stage_by_scene = _group_by_scene(stage_directions)
    for index, scene in enumerate(ordered_scenes, start=1):
        scene_no = _to_int(scene.get("scene_number")) or index
        lines.append("")
        lines.append(_scene_header(scene, episode_number, scene_no))
        scene_dialogues = dialogues_by_scene.get(scene_no, [])
        characters = _scene_characters(scene, scene_dialogues, fallback="旁白")
        lines.append("人物： " + "、".join(characters))

        scene_stage = stage_by_scene.get(scene_no, [])
        summary = _scene_summary(scene)
        if not scene_stage:
            scene_stage = [
                {
                    "content": summary or "众人僵在原地，镜头压近主角的反应。",
                    "timing": "intro",
                }
            ]
        if not scene_dialogues:
            scene_dialogues = [
                {
                    "character": "旁白",
                    "content": summary or "危机在这一刻升级。",
                    "emotion": "压低声",
                }
            ]

        stage_cursor = 0
        intro_stage, stage_cursor = _pop_intro_stage(scene_stage, stage_cursor)
        for direction in intro_stage:
            lines.append(_stage_line(direction))

        for dialogue_index, dialogue in enumerate(scene_dialogues, start=1):
            if dialogue_index > 1 and (dialogue_index - 1) % 3 == 0:
                while stage_cursor < len(scene_stage):
                    direction = scene_stage[stage_cursor]
                    stage_cursor += 1
                    lines.append(_stage_line(direction))
                    break
            lines.append(_dialogue_line(dialogue))
        while stage_cursor < len(scene_stage):
            lines.append(_stage_line(scene_stage[stage_cursor]))
            stage_cursor += 1
    if not _has_cliffhanger(lines):
        final_speaker = _last_dialogue_speaker(dialogues) or "旁白"
        lines.append("▲【特写】镜头停在关键线索上，所有声音突然压低。")
        lines.append(f"{final_speaker}(压低声)：你真以为，这就是全部真相？")
    return "\n".join(lines)


def _group_by_scene(items: List[Dict[str, Any]]) -> dict[int, List[Dict[str, Any]]]:
    grouped: dict[int, List[Dict[str, Any]]] = {}
    for idx, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            continue
        scene_no = _to_int(item.get("scene_number")) or idx
        grouped.setdefault(scene_no, []).append(item)
    return grouped


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _scene_header(scene: Dict[str, Any], episode_number: int, scene_no: int) -> str:
    slug = str(scene.get("slug_line") or "").strip()
    if re.match(r"^\d+[-－]\d+\s+", slug):
        return slug
    if slug.startswith(("内.", "外.", "内/外.", "外/内.")):
        return f"{episode_number}-{scene_no} {slug}"

    location = (
        scene.get("location")
        or scene.get("place")
        or _location_from_slug(slug)
        or "主要场景"
    )
    time_of_day = _normalize_time_of_day(
        scene.get("time_of_day") or scene.get("time") or slug
    )
    return f"{episode_number}-{scene_no} {_normalize_space_type(slug)}. {location} - {time_of_day}"


def _location_from_slug(slug: str) -> Optional[str]:
    if not slug:
        return None
    cleaned = re.sub(r"^(INT\.|EXT\.|内\.|外\.)\s*", "", slug, flags=re.I)
    return cleaned.split(" - ")[0].strip()[:40] or None


def _normalize_space_type(slug: str) -> str:
    upper = slug.upper()
    if upper.startswith("EXT.") or slug.startswith("外"):
        return "外"
    if "外" in slug and "内" not in slug:
        return "外"
    return "内"


def _normalize_time_of_day(value: Any) -> str:
    text = str(value or "").lower()
    if any(k in text for k in ("night", "夜", "晚")):
        return "夜"
    if any(k in text for k in ("morning", "晨", "早")):
        return "晨"
    if any(k in text for k in ("evening", "dusk", "黄昏", "昏")):
        return "昏"
    return "日"


def _scene_summary(scene: Dict[str, Any]) -> str:
    return str(
        scene.get("summary")
        or scene.get("description")
        or scene.get("story_beat")
        or scene.get("title")
        or scene.get("slug_line")
        or ""
    ).strip()


def _scene_characters(
    scene: Dict[str, Any],
    scene_dialogues: List[Dict[str, Any]],
    *,
    fallback: str,
) -> List[str]:
    names: List[str] = []
    raw_characters = scene.get("characters") or scene.get("characters_involved") or []
    if isinstance(raw_characters, str):
        raw_characters = re.split(r"[、,，/]", raw_characters)
    if isinstance(raw_characters, list):
        for raw in raw_characters:
            if isinstance(raw, dict):
                name = raw.get("name") or raw.get("character_name")
            else:
                name = raw
            _append_unique(names, _clean_speaker(str(name or "")))
    for dialogue in scene_dialogues:
        _append_unique(names, _clean_speaker(str(dialogue.get("character") or "")))
    return names or [fallback]


def _append_unique(items: List[str], value: str) -> None:
    value = value.strip()
    if value and value not in items:
        items.append(value)


def _pop_intro_stage(
    scene_stage: List[Dict[str, Any]], start: int
) -> tuple[List[Dict[str, Any]], int]:
    if start >= len(scene_stage):
        return [], start
    intro = []
    first = scene_stage[start]
    timing = str(first.get("timing") or "").lower()
    if timing in {"intro", "opening", "before", "开场", "对话前"} or start == 0:
        intro.append(first)
        start += 1
    return intro, start


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


def _first_lines_have_hook(lines: List[str]) -> bool:
    markers = ("！", "？", "?", "砰", "啪", "咚", "血", "跪", "杀", "开场钩子")
    return any(any(marker in line for marker in markers) for line in lines[:5])


def _has_cliffhanger(lines: List[str]) -> bool:
    pattern = r"[?？]|？！|!\?|卡点|特写|真相|身份|猛地|定格|突然"
    tail = [line.strip() for line in lines[-4:] if line.strip()]
    return any(re.search(pattern, line) for line in tail)


def _last_dialogue_speaker(dialogues: List[Dict[str, Any]]) -> Optional[str]:
    for dialogue in reversed(dialogues or []):
        if isinstance(dialogue, dict) and dialogue.get("character"):
            return _clean_speaker(str(dialogue["character"]))
    return None
