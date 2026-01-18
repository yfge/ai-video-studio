from __future__ import annotations

from typing import Any, Dict, Optional

DURATION_TOLERANCE_LOW = 0.85
DURATION_TOLERANCE_HIGH = 1.15
DEFAULT_SCENE_DURATION_SECONDS = 30
MAX_REACT_REGENERATE_ATTEMPTS = 3
MAX_FALLBACK_SCENES = 12


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
    if any(isinstance(c, dict) for c in conflicts):
        return True, None
    return False, "invalid_conflicts"


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

    return {
        "episode_number": ep_num,
        "title": title,
        "summary": logline,
        "plot_points": plot_points or [],
        "character_arcs": None,
        "conflicts": [{"description": logline, "intensity": "medium"}],
        "scene_count": len(scenes) if scenes else None,
        "scenes": scenes or None,
        "fallback_from_outline": True,
    }
