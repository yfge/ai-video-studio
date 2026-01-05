"""
Celery 任务入口

目前主要用于调度 Story/Episode/Script 相关的异步生成任务。
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.story_generate")
def story_generate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """
    异步故事生成任务入口。

    为避免导入环造成副作用，这里的依赖在函数内部按需导入。
    """
    from app.api.v1.endpoints.stories import _process_story_generation_task

    _process_story_generation_task(task_id, request_dict, user_id)


@celery_app.task(name="tasks.episode_generate")
def episode_generate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """异步剧集生成任务入口。"""
    from app.api.v1.endpoints.episodes import process_episode_generation_task

    process_episode_generation_task(task_id, request_dict, user_id)


@celery_app.task(name="tasks.script_generate")
def script_generate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """异步剧本生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_generation_task

    _process_script_generation_task(task_id, request_dict, user_id)


@celery_app.task(name="tasks.script_regenerate")
def script_regenerate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """异步剧本重新生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_regeneration_task

    _process_script_regeneration_task(task_id, request_dict, user_id)


@celery_app.task(name="tasks.script_dialogue_audio_generate")
def script_dialogue_audio_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步生成剧本场景对白音轨任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_dialogue_audio_task

    _process_script_dialogue_audio_task(task_id, payload, user_id)


@celery_app.task(name="tasks.script_audio_timeline_generate")
def script_audio_timeline_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步生成 episode 对白音轨拼接与时间轴任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_audio_timeline_task

    _process_script_audio_timeline_task(task_id, payload, user_id)


@celery_app.task(name="tasks.script_audio_storyboard_generate")
def script_audio_storyboard_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步从 episode 音频时间轴生成分镜帧占位任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_audio_storyboard_task

    _process_script_audio_storyboard_task(task_id, payload, user_id)


@celery_app.task(name="tasks.virtual_ip_image_generate")
def virtual_ip_image_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步虚拟 IP 文生图任务入口。"""
    from app.api.v1.endpoints.virtual_ip_images import process_virtual_ip_image_task

    process_virtual_ip_image_task(task_id, payload, user_id)


@celery_app.task(name="tasks.virtual_ip_image_variant")
def virtual_ip_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步虚拟 IP 图生图任务入口。"""
    from app.api.v1.endpoints.virtual_ip_images import (
        process_virtual_ip_image_variant_task,
    )

    process_virtual_ip_image_variant_task(task_id, payload, user_id)


@celery_app.task(name="tasks.environment_image_generate")
def environment_image_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步环境文生图任务入口。"""
    from app.api.v1.endpoints.story_structure import process_environment_image_task

    process_environment_image_task(task_id, payload, user_id)


@celery_app.task(name="tasks.environment_image_variant")
def environment_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步环境图生图任务入口。"""
    from app.api.v1.endpoints.story_structure import (
        process_environment_image_variant_task,
    )

    process_environment_image_variant_task(task_id, payload, user_id)


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
    _process_storyboard_image_task(
        task_id,
        script_id,
        frame_indexes,
        prompt_override=payload.get("prompt"),
        model=payload.get("model"),
        size=payload.get("size"),
        width=_maybe_int(payload.get("width")),
        height=_maybe_int(payload.get("height")),
        style=payload.get("style") or "realistic",
        style_preset_id=payload.get("style_preset_id"),
        style_spec=payload.get("style_spec"),
        aspect_ratio=payload.get("aspect_ratio"),
        reference_images=payload.get("reference_images") or [],
        labeled_references=payload.get("labeled_references"),
        count=count_int,
        keyframe_mode=(payload.get("keyframe_mode") or "single"),
        start_enabled=payload.get("start_enabled", True),
        end_enabled=payload.get("end_enabled", True),
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


@celery_app.task(name="tasks.storyboard_generate")
def storyboard_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步分镜结构生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_storyboard_generation_task

    _process_storyboard_generation_task(task_id, payload, user_id)


@celery_app.task(name="tasks.timeline_pipeline_generate")
def timeline_pipeline_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """一键生成时间轴流水线任务入口（对白音轨 → 时间轴 → 分镜帧占位）。"""
    from app.api.v1.endpoints.scripts_legacy import _process_timeline_pipeline_task

    _process_timeline_pipeline_task(task_id, payload, user_id)


@celery_app.task(name="tasks.video_generation_poll")
def video_generation_poll_task(limit: int = 50) -> int:
    """集中轮询视频生成任务状态。"""
    from app.services.video.video_task_entrypoints import poll_pending_video_tasks

    return poll_pending_video_tasks(limit=limit)
