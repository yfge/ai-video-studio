from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.script import Episode


def to_int(value: Any) -> Optional[int]:
    """Safely convert value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_episode_scenes(episode: Episode) -> List[Dict[str, Any]]:
    """Extract scenes from episode metadata."""
    if not episode:
        return []

    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    scenes_src = meta.get("scenes") if isinstance(meta, dict) else []
    if not isinstance(scenes_src, list):
        return []

    cleaned: List[Dict[str, Any]] = []
    for idx, raw in enumerate(scenes_src, start=1):
        if not isinstance(raw, dict):
            continue
        base = dict(raw)
        scene_no = to_int(base.get("scene_number")) or idx
        base["scene_number"] = scene_no
        summary = (
            base.get("summary") or base.get("description") or base.get("beat_summary")
        )
        location = base.get("location") or base.get("place") or base.get("setting")
        time_of_day = base.get("time_of_day") or base.get("time")

        if summary:
            base.setdefault("summary", summary)
            base.setdefault("description", summary)
        if location:
            base.setdefault("location", location)
        if time_of_day:
            base.setdefault("time_of_day", time_of_day)
        if not base.get("slug_line"):
            if location and time_of_day:
                base["slug_line"] = f"{location} - {time_of_day}"
            elif summary:
                base["slug_line"] = str(summary)[:80]
            else:
                base["slug_line"] = f"Scene {scene_no}"
        cleaned.append(base)

    return cleaned
