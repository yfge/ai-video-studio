from __future__ import annotations

from typing import Any, Dict, Optional

DURATION_TOLERANCE_LOW = 0.85
DURATION_TOLERANCE_HIGH = 1.15
DEFAULT_SCENE_DURATION_SECONDS = 30
MAX_REACT_REGENERATE_ATTEMPTS = 3
MAX_FALLBACK_SCENES = 12
MIN_ACCEPTED_SCENES = 2
DEFAULT_FALLBACK_SCENES = (
    ("开场钩子", "开场钩子：围绕核心冲突抛出直接可拍的信息爆点。"),
    ("升级推进", "升级推进：主角被迫做出选择，冲突继续加压。"),
    ("爽点落点", "爽点：主角抓住证据或机会完成一次明确反击。"),
    ("结尾卡点", "卡点：更大的危机或反转出现，推动观众追下一集。"),
)


def calculate_episode_duration_seconds(episode_obj: Dict[str, Any]) -> int:
    scenes = episode_obj.get("scenes") or []
    total_seconds = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        duration = scene.get("estimated_duration_seconds")
        total_seconds += (
            int(duration) if duration is not None else DEFAULT_SCENE_DURATION_SECONDS
        )
    return total_seconds


def validate_episode_duration(
    episode_obj: Dict[str, Any], target_minutes: Optional[int]
) -> tuple[bool, int, int]:
    if not target_minutes:
        return True, 0, 0
    target_seconds = target_minutes * 60
    current_seconds = calculate_episode_duration_seconds(episode_obj)
    min_seconds = int(target_seconds * DURATION_TOLERANCE_LOW)
    max_seconds = int(target_seconds * DURATION_TOLERANCE_HIGH)
    return (
        min_seconds <= current_seconds <= max_seconds,
        current_seconds,
        target_seconds,
    )


def validate_episode_payload(episode_obj: Dict[str, Any]) -> tuple[bool, str | None]:
    if not episode_obj.get("summary"):
        return False, "missing_summary"
    conflicts = episode_obj.get("conflicts")
    if not conflicts or not isinstance(conflicts, list):
        return False, "missing_conflicts"
    if not any(isinstance(c, dict) for c in conflicts):
        return False, "invalid_conflicts"

    _fill_missing_scenes_from_outline_stub(episode_obj)
    scenes = episode_obj.get("scenes")
    if not isinstance(scenes, list):
        return False, "missing_scenes"
    valid_scene_count = sum(1 for scene in scenes if isinstance(scene, dict) and scene)
    if valid_scene_count < MIN_ACCEPTED_SCENES:
        return False, "too_few_scenes"

    raw_scene_count = episode_obj.get("scene_count")
    if raw_scene_count is not None:
        try:
            scene_count = int(raw_scene_count)
        except (TypeError, ValueError):
            return False, "invalid_scene_count"
        if scene_count != len(scenes):
            return False, "scene_count_mismatch"
    return True, None


def _fill_missing_scenes_from_outline_stub(episode_obj: Dict[str, Any]) -> None:
    if isinstance(episode_obj.get("scenes"), list):
        return
    fallback = stub_episode_from_outline(
        {
            "episode_number": episode_obj.get("episode_number"),
            "title": episode_obj.get("title"),
            "logline": episode_obj.get("summary"),
        }
    )
    episode_obj["scenes"] = fallback["scenes"]
    episode_obj["scene_count"] = fallback["scene_count"]
    if not episode_obj.get("plot_points"):
        episode_obj["plot_points"] = fallback["plot_points"]
    episode_obj["fallback_from_outline"] = True


def _fallback_scenes_from_logline(
    logline: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenes: list[dict[str, Any]] = []
    plot_points: list[dict[str, Any]] = []
    for idx, (beat_title, summary) in enumerate(DEFAULT_FALLBACK_SCENES, start=1):
        scene_summary = f"{summary} 核心情境：{logline}"
        scenes.append(
            {
                "scene_number": idx,
                "slug_line": f"SCENE {idx} - {beat_title}",
                "location": "unspecified",
                "time_of_day": "unspecified",
                "summary": scene_summary,
                "story_beat": beat_title,
            }
        )
        plot_points.append(
            {
                "description": scene_summary,
                "timing": beat_title,
            }
        )
    return scenes, plot_points


def stub_episode_from_outline(outline: Dict[str, Any]) -> Dict[str, Any]:
    ep_num = outline.get("episode_number") or 1
    logline = (outline.get("logline") or "").strip() or "本集出现关键转折。"
    title = outline.get("title") or f"第{ep_num}集"

    plot_points: list[dict[str, Any]] = []
    scenes: list[dict[str, Any]] = []
    beats = outline.get("beats") or []
    if isinstance(beats, list) and beats:
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            summary = (
                beat.get("beat_summary") or beat.get("description") or ""
            ).strip()
            beat_title = (beat.get("beat_title") or "").strip()
            if not summary:
                summary = beat_title
            if not summary:
                continue

            act_label = (beat.get("act_label") or "").strip()
            timing_parts = [part for part in (act_label, beat_title) if part]
            plot_points.append(
                {
                    "description": summary,
                    "timing": " - ".join(timing_parts) if timing_parts else None,
                }
            )

            scene_number = len(scenes) + 1
            location_hint = (beat.get("location_hint") or "").strip()
            scenes.append(
                {
                    "scene_number": scene_number,
                    "slug_line": f"SCENE {scene_number} - {beat_title or 'beat'}",
                    "location": location_hint or "unspecified",
                    "time_of_day": "unspecified",
                    "summary": summary,
                    "story_beat": beat_title or "beat",
                }
            )
            if len(scenes) >= MAX_FALLBACK_SCENES:
                break

    if not scenes:
        scenes, plot_points = _fallback_scenes_from_logline(logline)

    return {
        "episode_number": ep_num,
        "title": title,
        "summary": logline,
        "plot_points": plot_points,
        "character_arcs": None,
        "conflicts": [{"description": logline, "intensity": "medium"}],
        "scene_count": len(scenes),
        "scenes": scenes,
        "fallback_from_outline": True,
    }
