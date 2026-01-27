"""
Celery task registrations for storyboard image/video generation.

Kept in a dedicated module to keep app.services.task_worker under the 250-line
service file limit.
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.storyboard_image_generate")
def storyboard_image_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步分镜图像生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_storyboard_image_task

    script_id = int(payload.get("script_id"))
    frame_indexes = payload.get("frames") or []
    try:
        count_int = int(payload.get("count") or 1)
    except (TypeError, ValueError):
        count_int = 1
    if count_int < 1:
        count_int = 1
    if count_int > 4:
        count_int = 4

    def _maybe_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _maybe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    _process_storyboard_image_task(
        task_id,
        script_id,
        frame_indexes,
        prompt_override=payload.get("prompt"),
        model=payload.get("model"),
        generation_profile=payload.get("generation_profile"),
        size=payload.get("size"),
        width=_maybe_int(payload.get("width")),
        height=_maybe_int(payload.get("height")),
        style=payload.get("style") or "realistic",
        style_preset_id=payload.get("style_preset_id"),
        style_spec=payload.get("style_spec"),
        aspect_ratio=payload.get("aspect_ratio"),
        seed=_maybe_int(payload.get("seed")),
        steps=_maybe_int(payload.get("steps")),
        cfg_scale=_maybe_float(payload.get("cfg_scale")),
        negative_prompt=payload.get("negative_prompt"),
        strength=_maybe_float(payload.get("strength")),
        reference_images=payload.get("reference_images") or [],
        labeled_references=payload.get("labeled_references"),
        count=count_int,
        keyframe_mode=(payload.get("keyframe_mode") or "single"),
        start_enabled=payload.get("start_enabled", True),
        end_enabled=payload.get("end_enabled", True),
    )
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="storyboard_images",
    )


@celery_app.task(name="tasks.storyboard_video_generate")
def storyboard_video_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步分镜视频生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_storyboard_video_task

    script_id = int(payload.get("script_id"))
    frame_indexes = payload.get("frames") or []
    selections = payload.get("selections") or []
    options = {
        "prompt": payload.get("prompt"),
        "model": payload.get("model"),
        "duration": payload.get("duration"),
        "fps": payload.get("fps"),
        "resolution": payload.get("resolution"),
        "ratio": payload.get("ratio"),
        "watermark": payload.get("watermark"),
        "seed": payload.get("seed"),
        "camera_fixed": payload.get("camera_fixed"),
        "service_tier": payload.get("service_tier"),
        "execution_expires_after": payload.get("execution_expires_after"),
        "return_last_frame": payload.get("return_last_frame"),
        "camera_control": payload.get("camera_control"),
    }
    _process_storyboard_video_task(
        task_id,
        script_id,
        frame_indexes,
        selections,
        options=options,
    )
