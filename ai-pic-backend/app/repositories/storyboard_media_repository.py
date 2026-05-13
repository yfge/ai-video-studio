"""Repository helpers for storyboard media tasks and endpoint payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.script import Episode, Script, Story
from app.models.task import Task


def get_task_by_id(db, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def get_script_by_id(db, script_id: int) -> Script | None:
    return db.query(Script).filter(Script.id == script_id).first()


def load_storyboard_frames(db, script_id: int) -> list[dict[str, Any]]:
    script = get_script_by_id(db, script_id)
    if not script:
        return []
    storyboard = (script.extra_metadata or {}).get("storyboard")
    if not isinstance(storyboard, dict):
        return []
    frames = storyboard.get("frames")
    if not isinstance(frames, list):
        return []
    return [frame for frame in frames if isinstance(frame, dict)]


def resolve_storyboard_aspect_ratio(
    db,
    *,
    script: Script,
    requested: str | None,
) -> str | None:
    if requested:
        return requested
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    story = (
        db.query(Story).filter(Story.id == episode.story_id).first()
        if episode
        else None
    )
    if episode and episode.extra_metadata:
        value = episode.extra_metadata.get("aspect_ratio")
        if value:
            return value
    if story and story.extra_metadata:
        return story.extra_metadata.get("aspect_ratio")
    return None


def save_storyboard_image_frames(
    db,
    *,
    script_id: int,
    storyboard: dict[str, Any] | None,
    frames: list[Any],
    style: str,
    style_preset_id: str | None,
    style_spec: dict[str, Any] | None,
    resolved_style_spec: dict[str, Any] | None,
    resolved_resolution: Any,
) -> None:
    script = get_script_by_id(db, script_id)
    if not script:
        return
    extra = dict(script.extra_metadata or {})
    storyboard_payload = dict(storyboard or {})
    meta_payload = (
        dict(storyboard_payload.get("meta") or {})
        if isinstance(storyboard_payload.get("meta"), dict)
        else {}
    )
    meta_payload.update(
        {
            "image_generation_updated_at": datetime.utcnow().isoformat(),
            "image_generation_style": style,
            "image_generation_style_preset_id": (
                (style_preset_id or "").strip() or None
            ),
            "image_generation_style_spec": resolved_style_spec
            or (style_spec if isinstance(style_spec, dict) else None),
            "image_generation_style_spec_resolution": resolved_resolution,
        }
    )
    storyboard_payload["meta"] = meta_payload
    storyboard_payload["frames"] = frames
    extra["storyboard"] = storyboard_payload
    script.extra_metadata = extra
    db.add(script)
    db.commit()
