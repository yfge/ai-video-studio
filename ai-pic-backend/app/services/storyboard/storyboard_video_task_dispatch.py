"""Idempotent persistence and dispatch for storyboard video tasks."""

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
class StoryboardVideoDispatchResult:
    task: Task
    reused: bool


def build_storyboard_video_request_fingerprint(
    *,
    user_id: int,
    script_id: int,
    target_business_id: str | None,
    payload: dict[str, Any],
    frame_snapshots: Sequence[dict[str, Any]],
) -> str:
    canonical_request = {
        "version": REQUEST_FINGERPRINT_VERSION,
        "user_id": user_id,
        "script_id": script_id,
        "target_business_id": target_business_id,
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


def create_or_reuse_storyboard_video_task(
    db,
    *,
    user_id: int,
    script_id: int,
    target_business_id: str | None,
    payload: dict[str, Any],
    frame_snapshots: Sequence[dict[str, Any]],
    dispatch: Callable[[int, dict[str, Any], int], Any],
) -> StoryboardVideoDispatchResult:
    fingerprint = build_storyboard_video_request_fingerprint(
        user_id=user_id,
        script_id=script_id,
        target_business_id=target_business_id,
        payload=payload,
        frame_snapshots=frame_snapshots,
    )
    repository = TaskRepository(db)
    for candidate in repository.list_active_by_request_fingerprint(
        user_id=user_id,
        task_type=TaskType.VIDEO_GENERATION,
        request_fingerprint=fingerprint,
    ):
        if _request_fingerprint(candidate.parameters) == fingerprint:
            return StoryboardVideoDispatchResult(task=candidate, reused=True)

    task_payload = {
        **payload,
        "request_fingerprint_version": REQUEST_FINGERPRINT_VERSION,
        "request_fingerprint": fingerprint,
    }
    task = repository.create(
        title=f"分镜视频候选生成 - 剧本{script_id}",
        description="Production canvas video.candidates skill dispatch",
        task_type=TaskType.VIDEO_GENERATION,
        prompt=f"Storyboard video generation for script {script_id}",
        parameters=json.dumps(task_payload, ensure_ascii=False),
        user_id=user_id,
        target_business_id=target_business_id,
    )
    db.commit()
    db.refresh(task)
    try:
        dispatch(task.id, task_payload, user_id)
    except Exception as exc:
        repository.update(
            task,
            status=TaskStatus.FAILED,
            error_message=f"storyboard_video_dispatch_failed: {exc}",
        )
        db.commit()
        db.refresh(task)
        raise
    return StoryboardVideoDispatchResult(task=task, reused=False)


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
