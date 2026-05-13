"""Queue storyboard image generation after storyboard structure creation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Sequence

from app.models.task import Task, TaskType
from app.repositories.storyboard_media_repository import load_storyboard_frames
from app.services.task_worker import storyboard_image_generate_task

STORYBOARD_IMAGE_METADATA_KEY = "storyboard_image_generation"


@dataclass(frozen=True)
class StoryboardImageQueueResult:
    """Result of attempting to queue follow-up storyboard image generation."""

    status: str
    child_task_id: int | None
    queued_frame_indexes: list[int]
    skipped_frame_indexes: list[int]
    require_reference_images: bool
    reason: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status,
            "child_task_id": self.child_task_id,
            "queued_frame_indexes": self.queued_frame_indexes,
            "queued_frame_count": len(self.queued_frame_indexes),
            "skipped_frame_indexes": self.skipped_frame_indexes,
            "skipped_frame_count": len(self.skipped_frame_indexes),
            "require_reference_images": self.require_reference_images,
        }
        if self.reason:
            payload["reason"] = self.reason
        return payload


def queue_storyboard_image_generation(
    db,
    *,
    script_id: int,
    user_id: int | None,
    frames: Sequence[dict[str, Any]] | None = None,
    frame_indexes: Sequence[int] | None = None,
    model: str | None = None,
    aspect_ratio: str | None = None,
    require_reference_images: bool = True,
) -> StoryboardImageQueueResult:
    """Create the follow-up task that turns storyboard frames into images.

    Parent pipeline tasks complete once storyboard placeholders exist. This
    helper only creates a child image task for frames that have usable reference
    images, and returns explicit metadata for skipped frames.
    """

    target_frames = (
        list(frames) if frames is not None else load_storyboard_frames(db, script_id)
    )
    target_indexes = _normalize_frame_indexes(frame_indexes, len(target_frames))
    if user_id is None:
        return StoryboardImageQueueResult(
            status="skipped",
            child_task_id=None,
            queued_frame_indexes=[],
            skipped_frame_indexes=target_indexes,
            require_reference_images=require_reference_images,
            reason="missing_user_id",
        )
    if not target_indexes:
        return StoryboardImageQueueResult(
            status="skipped",
            child_task_id=None,
            queued_frame_indexes=[],
            skipped_frame_indexes=[],
            require_reference_images=require_reference_images,
            reason="no_storyboard_frames",
        )

    if require_reference_images:
        queued_indexes = [
            idx
            for idx in target_indexes
            if _frame_has_reference_images(target_frames[idx])
        ]
        skipped_indexes = [idx for idx in target_indexes if idx not in queued_indexes]
    else:
        queued_indexes = target_indexes
        skipped_indexes = []

    if not queued_indexes:
        return StoryboardImageQueueResult(
            status="skipped",
            child_task_id=None,
            queued_frame_indexes=[],
            skipped_frame_indexes=skipped_indexes,
            require_reference_images=require_reference_images,
            reason="no_reference_images",
        )

    payload: dict[str, Any] = {
        "script_id": script_id,
        "frame_indexes": queued_indexes,
        "frames": queued_indexes,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "keyframe_mode": "start_end",
        "start_enabled": True,
        "end_enabled": True,
        "count": 4,
        "require_reference_images": require_reference_images,
    }
    task = Task(
        title=f"分镜画面生成 - 剧本{script_id}",
        description="分镜生成后的自动画面任务，使用场景/角色参考图生成首尾帧",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        prompt=f"Storyboard image generation for script {script_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=user_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    storyboard_image_generate_task.delay(task.id, payload, user_id)
    return StoryboardImageQueueResult(
        status="queued",
        child_task_id=task.id,
        queued_frame_indexes=queued_indexes,
        skipped_frame_indexes=skipped_indexes,
        require_reference_images=require_reference_images,
    )


def record_storyboard_image_queue_metadata(
    db,
    parent_task: Task | None,
    result: StoryboardImageQueueResult,
) -> None:
    """Attach child image queue status to parent task parameters."""

    if not parent_task:
        return
    params = _decode_parameters(parent_task.parameters)
    params[STORYBOARD_IMAGE_METADATA_KEY] = result.to_metadata()
    parent_task.parameters = json.dumps(params, ensure_ascii=False)
    db.add(parent_task)
    db.commit()


def queue_storyboard_image_generation_for_parent_task(
    db,
    parent_task: Task | None,
    *,
    script_id: int,
    user_id: int | None,
    frames: Sequence[dict[str, Any]] | None = None,
    aspect_ratio: str | None = None,
) -> StoryboardImageQueueResult:
    result = queue_storyboard_image_generation(
        db,
        script_id=script_id,
        user_id=user_id,
        frames=frames,
        aspect_ratio=aspect_ratio,
        require_reference_images=True,
    )
    record_storyboard_image_queue_metadata(db, parent_task, result)
    return result


def storyboard_image_queue_progress_message(
    result: StoryboardImageQueueResult,
    *,
    prefix: str,
) -> str:
    queued = len(result.queued_frame_indexes)
    skipped = len(result.skipped_frame_indexes)
    if result.child_task_id:
        return (
            f"{prefix}：分镜画面任务已创建 "
            f"task_id={result.child_task_id} queued={queued} skipped={skipped}"
        )
    return (
        f"{prefix}：分镜画面任务已跳过 "
        f"reason={result.reason or 'no_eligible_frames'} skipped={skipped}"
    )


def _normalize_frame_indexes(
    frame_indexes: Sequence[int] | None,
    frame_count: int,
) -> list[int]:
    if frame_count <= 0:
        return []
    if frame_indexes is None:
        return list(range(frame_count))

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


def _frame_has_reference_images(frame: dict[str, Any]) -> bool:
    for key in (
        "reference_images",
        "reference_image_urls",
        "start_reference_images",
        "end_reference_images",
    ):
        value = frame.get(key)
        if isinstance(value, list) and any(_has_non_empty_url(item) for item in value):
            return True
    for key in ("reference_image", "environment_reference_image"):
        if _has_non_empty_url(frame.get(key)):
            return True
    return False


def _has_non_empty_url(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _decode_parameters(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {"_raw_parameters": raw}
    return value if isinstance(value, dict) else {"_raw_parameters": value}
