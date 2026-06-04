"""Shared helpers for script dialogue audio/timeline pipeline endpoints."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from app.models.script import Episode, Script
from app.models.story_structure import Scene
from app.models.task import Task
from app.models.user import User
from app.repositories.script_repository import ScriptRepository
from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

T = TypeVar("T")
PIPELINE_DEPRECATION_SUNSET = "Thu, 31 Dec 2026 23:59:59 GMT"


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


def load_script_with_access(db: Session, script_id: int, user: User) -> Script | None:
    """Load script by id and enforce owner/admin access control."""
    user_id = None if user.is_admin or user.is_superuser else user.id
    return ScriptRepository(db).get_with_relations(script_id=script_id, user_id=user_id)


def mark_pipeline_endpoint_deprecated(
    response: Response,
    *,
    successor_path: str,
) -> None:
    """Attach deprecation headers for legacy step-by-step timeline endpoints."""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = PIPELINE_DEPRECATION_SUNSET
    response.headers["Link"] = f'<{successor_path}>; rel="successor-version"'
    response.headers["X-API-Deprecated"] = "Use timeline-pipeline endpoint"


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


def format_pipeline_error(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        detail = _format_http_exception_detail(exc.detail)
        if detail:
            return detail
    message = str(exc).strip()
    return message or exc.__class__.__name__


def _format_http_exception_detail(detail: object) -> str:
    if isinstance(detail, str):
        return detail.strip()
    if isinstance(detail, dict):
        for key in ("message", "detail", "error"):
            value = detail.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(detail, ensure_ascii=False, default=str)
    if isinstance(detail, list):
        return json.dumps(detail, ensure_ascii=False, default=str)
    return ""
