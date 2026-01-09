from __future__ import annotations

from typing import Any, Dict, Optional

DURATION_TOLERANCE_LOW = 0.85
DURATION_TOLERANCE_HIGH = 1.15
DEFAULT_SCENE_DURATION_SECONDS = 30
MAX_REACT_REGENERATE_ATTEMPTS = 3


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
    return min_seconds <= current_seconds <= max_seconds, current_seconds, target_seconds


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
    return {
        "episode_number": ep_num,
        "title": title,
        "summary": logline,
        "plot_points": [],
        "character_arcs": None,
        "conflicts": [{"description": logline, "intensity": "medium"}],
        "scene_count": None,
        "fallback_from_outline": True,
    }
