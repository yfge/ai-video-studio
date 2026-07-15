from __future__ import annotations

from typing import Any

IMAGE_TASK_CHECKPOINT_KEY = "storyboard_image_task_checkpoint"


def task_is_cancelled(db, task) -> bool:
    if task is None:
        return False
    db.refresh(task)
    return task.status.value == "cancelled"


def partition_image_task_indexes(
    frames: list[Any], target_indexes: list[int], task_id: int
) -> tuple[list[int], list[int]]:
    completed = [
        index
        for index in target_indexes
        if 0 <= index < len(frames)
        and isinstance(frames[index], dict)
        and _frame_completed_by_task(frames[index], task_id)
    ]
    completed_set = set(completed)
    pending = [index for index in target_indexes if index not in completed_set]
    return pending, completed


def ensure_requested_frame_indexes_generated(
    requested_indexes: list[int], generated_frame_indexes: list[int]
) -> None:
    generated = set(generated_frame_indexes)
    missing = [index for index in requested_indexes if index not in generated]
    if missing:
        raise RuntimeError(
            "storyboard image generation produced no persisted images "
            f"for frames: {missing}"
        )


def checkpoint_image_task_frame(
    frame: dict[str, Any], task_id: int, result_meta: dict[str, Any]
) -> None:
    urls = [
        url
        for url in result_meta.get("generated_urls") or []
        if isinstance(url, str) and url.strip()
    ]
    if urls:
        frame[IMAGE_TASK_CHECKPOINT_KEY] = {
            "task_id": task_id,
            "generated_urls": urls,
        }


def _frame_completed_by_task(frame: dict[str, Any], task_id: int) -> bool:
    checkpoint = frame.get(IMAGE_TASK_CHECKPOINT_KEY)
    if not isinstance(checkpoint, dict) or checkpoint.get("task_id") != task_id:
        return False
    return bool(
        frame.get("start_image_url")
        or frame.get("image_url")
        or frame.get("start_image_urls")
    )
