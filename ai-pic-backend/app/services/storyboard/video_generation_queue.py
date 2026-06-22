from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

from app.models.script import Script
from app.models.task import Task, TaskType
from app.models.user import User
from app.repositories.storyboard_media_repository import (
    load_storyboard_frames,
    resolve_storyboard_aspect_ratio,
)
from app.services.task_worker import storyboard_video_generate_task
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class StoryboardVideoQueueResult:
    task: Task
    frame_count: int


def queue_storyboard_video_generation_task(
    db: Session,
    user: User,
    script: Script,
    *,
    prompt: str | None = None,
    frame_indexes: Sequence[int] | None = None,
    model: str | None = None,
    duration: float | None = None,
    fps: int | None = None,
    resolution: str | None = None,
    ratio: str | None = None,
    camera_fixed: bool | None = None,
    target_business_id: str | None = None,
) -> StoryboardVideoQueueResult:
    frames = load_storyboard_frames(db, int(script.id))
    if not frames:
        raise ValueError("no_storyboard_frames")

    indexes = _normalize_frame_indexes(frame_indexes, len(frames))
    payload = {
        "script_id": int(script.id),
        "frame_indexes": indexes,
        "frames": indexes,
        "selections": None,
        "prompt": prompt,
        "model": model,
        "duration": duration,
        "fps": fps or 24,
        "resolution": resolution or "720p",
        "ratio": resolve_storyboard_aspect_ratio(db, script=script, requested=ratio),
        "watermark": None,
        "seed": None,
        "camera_fixed": camera_fixed,
        "camera_control": None,
        "service_tier": None,
        "execution_expires_after": None,
        "return_last_frame": True,
        "use_end_frame": False,
    }
    task = Task(
        title=f"分镜视频候选生成 - 剧本{script.id}",
        description="Production canvas video.candidates skill dispatch",
        task_type=TaskType.VIDEO_GENERATION,
        prompt=f"Storyboard video generation for script {script.id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=user.id,
        target_business_id=target_business_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    storyboard_video_generate_task.delay(task.id, payload, user.id)
    return StoryboardVideoQueueResult(task=task, frame_count=len(frames))


def _normalize_frame_indexes(
    frame_indexes: Sequence[int] | None,
    frame_count: int,
) -> list[int] | None:
    if frame_indexes is None:
        return None
    normalized: list[int] = []
    for raw in frame_indexes:
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            continue
        if idx < 0 or idx >= frame_count or idx in normalized:
            continue
        normalized.append(idx)
    return normalized
