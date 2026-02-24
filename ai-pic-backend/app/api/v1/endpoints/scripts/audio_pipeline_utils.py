"""Shared helpers for script dialogue audio/timeline pipeline endpoints."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.models.task import Task
from app.models.user import User
from sqlalchemy.orm import Session

T = TypeVar("T")


def to_int(value: Any) -> int | None:
    """Best effort conversion to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def update_task_progress(db: Session, task: Task | None, description: str) -> None:
    """Persist task description progress for async job monitoring."""
    if not task:
        return
    task.description = description
    db.commit()


def scene_has_dialogue_audio(scene: Scene, script_id: int) -> bool:
    """Check whether a scene already has dialogue audio for this script."""
    meta = scene.extra_metadata
    if not isinstance(meta, dict):
        return False
    payload = meta.get("dialogue_audio")
    if not isinstance(payload, dict):
        return False
    if payload.get("script_id") != script_id:
        return False
    return bool(payload.get("oss_url"))


def scene_number_sort_key(scene: Scene) -> tuple[int, int, str]:
    """Sort scenes by numeric scene_number first, then lexicographic fallback."""
    raw = getattr(scene, "scene_number", None)
    num = to_int(raw)
    if num is None:
        return (1, 0, str(raw or ""))
    return (0, num, str(raw or ""))


def episode_has_audio_timeline(episode: Episode, script_id: int) -> bool:
    """Check whether an episode already has generated audio timeline."""
    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    timeline = meta.get("audio_timeline") if isinstance(meta, dict) else None
    if not isinstance(timeline, dict):
        return False
    if timeline.get("script_id") != script_id:
        return False
    ep_audio = timeline.get("episode_audio")
    if not isinstance(ep_audio, dict) or not ep_audio.get("oss_url"):
        return False
    beats = timeline.get("beats")
    return isinstance(beats, list) and len(beats) > 0


def friendly_task_title(
    prefix: str,
    script: Script,
    episode: Episode | None,
    story: Story | None,
) -> str:
    """Build a consistent task title with story/episode context."""
    story_label = ""
    if story and story.title:
        story_label = str(story.title)
    elif story:
        story_label = f"故事{story.id}"

    episode_label = ""
    if episode:
        ep_num = (
            f"第{episode.episode_number}集"
            if episode.episode_number is not None
            else f"剧集{episode.id}"
        )
        ep_title = f" {episode.title}" if episode.title else ""
        episode_label = f"{ep_num}{ep_title}"

    parts = [prefix]
    if story_label and episode_label:
        parts.append(f"{story_label} / {episode_label}")
    elif story_label:
        parts.append(story_label)
    elif episode_label:
        parts.append(episode_label)
    else:
        parts.append(f"剧本{script.id}")
    return " - ".join(parts)


def load_script_with_access(db: Session, script_id: int, user: User) -> Script | None:
    """Load script by id and enforce owner/admin access control."""
    return (
        db.query(Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
        .filter(
            True if user.is_admin or user.is_superuser else Story.user_id == user.id
        )
        .first()
    )


def run_async_task_sync(entrypoint: Callable[[], Awaitable[T]]) -> T:
    """
    Run async task logic from sync Celery handlers.

    In eager mode, Celery may execute in the request thread where an event loop is
    already running; in that case, run the coroutine in a dedicated thread.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        import anyio

        return anyio.run(entrypoint)

    result: dict[str, Any] = {}

    def _runner() -> None:
        import anyio

        try:
            result["value"] = anyio.run(entrypoint)
        except Exception as exc:  # pragma: no cover - exercised via caller paths
            result["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in result:
        raise cast(Exception, result["error"])
    return cast(T, result["value"])
