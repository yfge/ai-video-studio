from __future__ import annotations

from typing import Any


def _as_nonempty_str(value: object | None) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _to_int(value: object | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _scene_from_plot_point(plot_point: object, scene_number: int) -> dict[str, Any]:
    desc = None
    timing = None
    if isinstance(plot_point, dict):
        desc = _as_nonempty_str(plot_point.get("description"))
        timing = _as_nonempty_str(plot_point.get("timing"))
    elif isinstance(plot_point, str):
        desc = _as_nonempty_str(plot_point)

    return {
        "scene_number": scene_number,
        "slug_line": f"SCENE {scene_number} - {timing or 'beat'}",
        "summary": desc or "本场景推进剧情。",
        "time_of_day": "unspecified",
        "location": "unspecified",
    }


def _plot_point_scenes(plot_points: object) -> list[dict[str, Any]]:
    if not isinstance(plot_points, list):
        return []
    return [
        _scene_from_plot_point(item, idx) for idx, item in enumerate(plot_points, 1)
    ]


def _coerce_scene(raw: object, fallback_number: int) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None

    slug_line = _as_nonempty_str(raw.get("slug_line")) or _as_nonempty_str(
        raw.get("title")
    )
    summary = (
        _as_nonempty_str(raw.get("summary"))
        or _as_nonempty_str(raw.get("description"))
        or _as_nonempty_str(raw.get("beat_summary"))
    )
    location = (
        _as_nonempty_str(raw.get("location"))
        or _as_nonempty_str(raw.get("environment"))
        or _as_nonempty_str(raw.get("setting"))
    )
    time_of_day = (
        _as_nonempty_str(raw.get("time_of_day"))
        or _as_nonempty_str(raw.get("time"))
        or _as_nonempty_str(raw.get("period"))
    )

    if not (slug_line or summary or location or time_of_day):
        return None

    scene_number = _to_int(raw.get("scene_number")) or fallback_number
    return {
        **raw,
        "scene_number": scene_number,
        "slug_line": slug_line or f"SCENE {scene_number} - beat",
        "summary": summary or "本场景推进剧情。",
        "time_of_day": time_of_day or "unspecified",
        "location": location or "unspecified",
    }


def _summary_scene(ep_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "scene_number": 1,
        "slug_line": "SCENE 1 - beat",
        "summary": _as_nonempty_str(ep_data.get("summary")) or "本集开篇场景。",
        "time_of_day": "unspecified",
        "location": "unspecified",
    }


def _target_scene_count(
    raw_scene_count: int | None,
    scenes: list[dict[str, Any]],
    plot_scenes: list[dict[str, Any]],
) -> int | None:
    candidates = [
        count
        for count in (raw_scene_count, len(scenes), len(plot_scenes))
        if count is not None and count > 0
    ]
    return max(candidates) if candidates else None


def _pad_scenes(
    scenes: list[dict[str, Any]],
    plot_scenes: list[dict[str, Any]],
    target_scene_count: int,
) -> list[dict[str, Any]]:
    while len(scenes) < target_scene_count:
        idx = len(scenes) + 1
        if idx <= len(plot_scenes):
            scenes.append(dict(plot_scenes[idx - 1]))
        else:
            scenes.append(_scene_from_plot_point(None, idx))
    return scenes


def ensure_scenes(ep_data: dict[str, Any]) -> tuple[list[dict[str, Any]], int | None]:
    """Normalize episode scenes and keep scene_count aligned with usable scenes."""
    raw_scene_count = _to_int(ep_data.get("scene_count"))
    target_from_model = (
        raw_scene_count if raw_scene_count and raw_scene_count > 0 else None
    )

    scenes: list[dict[str, Any]] = []
    raw_scenes = ep_data.get("scenes")
    if isinstance(raw_scenes, list):
        for idx, raw in enumerate(raw_scenes, start=1):
            scene = _coerce_scene(raw, idx)
            if scene:
                scenes.append(scene)

    plot_scenes = _plot_point_scenes(ep_data.get("plot_points"))
    if not scenes:
        scenes = [dict(scene) for scene in plot_scenes] or [_summary_scene(ep_data)]

    target_scene_count = _target_scene_count(target_from_model, scenes, plot_scenes)
    if target_scene_count:
        scenes = _pad_scenes(scenes, plot_scenes, target_scene_count)

    for idx, scene in enumerate(scenes, start=1):
        scene["scene_number"] = idx
        scene.setdefault("slug_line", f"SCENE {idx} - beat")
        scene.setdefault("summary", "本场景推进剧情。")
        scene.setdefault("time_of_day", "unspecified")
        scene.setdefault("location", "unspecified")

    scene_count = len(scenes) if scenes else target_scene_count
    ep_data["scenes"] = scenes
    if scene_count is not None:
        ep_data["scene_count"] = scene_count
    return scenes, scene_count
