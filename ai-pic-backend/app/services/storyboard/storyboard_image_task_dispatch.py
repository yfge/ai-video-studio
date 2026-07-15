"""Idempotent persistence and dispatch for storyboard image tasks."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from app.models.task import Task, TaskStatus, TaskType
from app.repositories.task_repository import TaskRepository

REQUEST_FINGERPRINT_VERSION = 1


@dataclass(frozen=True)
class StoryboardImageDispatchResult:
    task: Task
    reused: bool


def build_storyboard_image_request_fingerprint(
    *,
    user_id: int,
    script_id: int,
    payload: dict[str, Any],
    frame_snapshots: Sequence[dict[str, Any]],
) -> str:
    """Return a stable fingerprint for all inputs observed by the image worker."""
    canonical_request = {
        "version": REQUEST_FINGERPRINT_VERSION,
        "user_id": user_id,
        "script_id": script_id,
        "payload": payload,
        "frame_snapshots": list(frame_snapshots),
    }
    canonical_json = json.dumps(
        canonical_request,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def create_or_reuse_storyboard_image_task(
    db,
    *,
    user_id: int,
    script_id: int,
    payload: dict[str, Any],
    frame_snapshots: Sequence[dict[str, Any]],
    dispatch: Callable[[int, dict[str, Any], int], Any],
) -> StoryboardImageDispatchResult:
    """Reuse an identical active task or persist and dispatch a new one."""
    fingerprint = build_storyboard_image_request_fingerprint(
        user_id=user_id,
        script_id=script_id,
        payload=payload,
        frame_snapshots=frame_snapshots,
    )
    repository = TaskRepository(db)
    for candidate in repository.list_active_by_request_fingerprint(
        user_id=user_id,
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        request_fingerprint=fingerprint,
    ):
        if _request_fingerprint(candidate.parameters) == fingerprint:
            return StoryboardImageDispatchResult(task=candidate, reused=True)

    task_payload = {
        **payload,
        "request_fingerprint_version": REQUEST_FINGERPRINT_VERSION,
        "request_fingerprint": fingerprint,
    }
    task = repository.create(
        title=f"分镜画面生成 - 剧本{script_id}",
        description="分镜生成后的自动画面任务，使用场景/角色参考图生成镜头支撑帧",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        prompt=f"Storyboard image generation for script {script_id}",
        parameters=json.dumps(task_payload, ensure_ascii=False),
        user_id=user_id,
    )
    db.commit()
    db.refresh(task)
    try:
        dispatch(task.id, task_payload, user_id)
    except Exception as exc:
        repository.update(
            task,
            status=TaskStatus.FAILED,
            error_message=f"storyboard_image_dispatch_failed: {exc}",
        )
        db.commit()
        db.refresh(task)
        raise
    return StoryboardImageDispatchResult(task=task, reused=False)


def _request_fingerprint(raw_parameters: str | None) -> str | None:
    if not raw_parameters:
        return None
    try:
        payload = json.loads(raw_parameters)
    except (TypeError, ValueError):
        return None
    fingerprint = (
        payload.get("request_fingerprint") if isinstance(payload, dict) else None
    )
    return fingerprint if isinstance(fingerprint, str) else None
