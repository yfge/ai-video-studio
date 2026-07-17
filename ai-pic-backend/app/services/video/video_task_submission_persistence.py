from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from app.models.task import Task
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.services.video.video_task_generation_metadata import (
    build_video_generation_metadata,
)
from app.services.video.video_task_utils import (
    build_parameters_payload,
    timeline_rework_for_frame,
)

VIDEO_TASK_TIMEOUT = timedelta(hours=1)


def persist_submitted_video_task(
    repo,
    *,
    task: Task,
    script_id: int,
    frame_index: int,
    response: Any,
    prompt: str | None,
    start_url: str | None,
    end_url: str | None,
    reference_images: list[str] | None,
    target_duration_seconds: float,
    provider_duration_seconds: int,
    opts: dict[str, Any],
) -> None:
    provider_task_id = str((response.data or {}).get("task_id"))
    params_payload = build_parameters_payload(
        prompt,
        start_url,
        end_url,
        reference_images,
        provider_duration_seconds,
        opts,
        target_duration_seconds=round(float(target_duration_seconds), 3),
        provider_duration_seconds=provider_duration_seconds,
        timeline_rework=timeline_rework_for_frame(opts, frame_index),
    )
    repo.create(
        task_id=task.id,
        script_id=script_id,
        frame_index=frame_index,
        user_id=task.user_id,
        provider=response.provider,
        provider_task_id=provider_task_id,
        model=response.model,
        model_type="image_to_video",
        prompt=prompt,
        parameters=json.dumps(params_payload, ensure_ascii=False),
        generation_metadata=build_video_generation_metadata(
            response.provider,
            response.model,
            provider_task_id,
            "image_to_video",
            params_payload,
        ),
        status=VideoGenerationTaskStatus.SUBMITTED,
        submitted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + VIDEO_TASK_TIMEOUT,
    )


def persist_submitted_timeline_video_task(
    repo,
    *,
    task_id: int,
    user_id: int,
    response: Any,
    provider_task_id: str,
    prompt: str | None,
    start_url: str | None,
    end_url: str | None,
    reference_images: list[str] | None,
    target_duration_seconds: float,
    provider_duration_seconds: int,
    model_type: str,
    opts: dict[str, Any],
    timeline_rework: dict[str, Any],
) -> None:
    params_payload = build_parameters_payload(
        prompt,
        start_url,
        end_url,
        reference_images,
        provider_duration_seconds,
        opts,
        target_duration_seconds=round(float(target_duration_seconds), 3),
        provider_duration_seconds=provider_duration_seconds,
        timeline_rework=timeline_rework,
    )
    params_payload.update(_duration_resolution_fields(response))
    repo.create(
        task_id=task_id,
        script_id=None,
        frame_index=None,
        user_id=user_id,
        provider=response.provider,
        provider_task_id=provider_task_id,
        model=response.model,
        model_type=model_type,
        prompt=prompt,
        parameters=json.dumps(params_payload, ensure_ascii=False),
        generation_metadata=build_video_generation_metadata(
            response.provider,
            response.model,
            provider_task_id,
            model_type,
            params_payload,
        ),
        status=VideoGenerationTaskStatus.SUBMITTED,
        submitted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + VIDEO_TASK_TIMEOUT,
    )


def _duration_resolution_fields(response: Any) -> dict[str, Any]:
    data = response.data if isinstance(response.data, dict) else {}
    return {
        key: data[key]
        for key in (
            "target_duration_seconds",
            "provider_duration_seconds",
            "allowed_durations",
            "capability_source",
        )
        if key in data
    }


def persist_failed_video_task(
    repo,
    *,
    task: Task,
    script_id: int,
    frame_index: int,
    error_message: str,
) -> None:
    repo.create(
        task_id=task.id,
        script_id=script_id,
        frame_index=frame_index,
        user_id=task.user_id,
        provider="unknown",
        provider_task_id="",
        model=None,
        model_type="image_to_video",
        prompt=None,
        parameters=json.dumps({}, ensure_ascii=False),
        status=VideoGenerationTaskStatus.FAILED,
        error_message=error_message,
    )
