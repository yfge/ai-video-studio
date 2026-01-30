"""
Celery 任务入口

目前主要用于调度 Story/Episode/Script 相关的异步生成任务。
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app

# Re-export asset/image tasks for legacy imports (e.g. scripts_legacy.py).
from app.services.task_worker_assets import (  # noqa: F401
    environment_image_generate_task,
    environment_image_variant_task,
    virtual_ip_image_generate_task,
    virtual_ip_image_variant_task,
)

# Re-export storyboard media tasks for legacy imports (e.g. scripts_legacy.py).
from app.services.task_worker_storyboard_media import (  # noqa: F401
    storyboard_image_generate_task,
    storyboard_video_generate_task,
)


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
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="story",
        request_dict=request_dict,
    )


@celery_app.task(name="tasks.story_novel_generate")
def story_novel_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步导出知乎体小说任务入口。"""
    from app.api.v1.endpoints.stories import process_story_novel_export_task

    process_story_novel_export_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="text_generation",
    )


@celery_app.task(name="tasks.episode_generate")
def episode_generate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """异步剧集生成任务入口。"""
    from app.api.v1.endpoints.episodes import process_episode_generation_task

    process_episode_generation_task(task_id, request_dict, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="episode",
        request_dict=request_dict,
    )


@celery_app.task(name="tasks.script_generate")
def script_generate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """异步剧本生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_generation_task

    _process_script_generation_task(task_id, request_dict, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="script",
        request_dict=request_dict,
    )


@celery_app.task(name="tasks.script_regenerate")
def script_regenerate_task(
    task_id: int, request_dict: Dict[str, Any], user_id: int
) -> None:
    """异步剧本重新生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_regeneration_task

    _process_script_regeneration_task(task_id, request_dict, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="script",
        request_dict=request_dict,
    )


@celery_app.task(name="tasks.script_dialogue_audio_generate")
def script_dialogue_audio_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步生成剧本场景对白音轨任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_dialogue_audio_task

    _process_script_dialogue_audio_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="dialogue_audio",
    )


@celery_app.task(name="tasks.script_audio_timeline_generate")
def script_audio_timeline_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步生成 episode 对白音轨拼接与时间轴任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_audio_timeline_task

    _process_script_audio_timeline_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="timeline_generation",
    )


@celery_app.task(name="tasks.script_audio_storyboard_generate")
def script_audio_storyboard_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步从 episode 音频时间轴生成分镜帧占位任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_audio_storyboard_task

    _process_script_audio_storyboard_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="storyboard_from_audio_timeline",
    )


@celery_app.task(name="tasks.storyboard_generate")
def storyboard_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步分镜结构生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_storyboard_generation_task

    _process_storyboard_generation_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="storyboard_generation",
    )


@celery_app.task(name="tasks.timeline_pipeline_generate")
def timeline_pipeline_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """一键生成时间轴流水线任务入口（对白音轨 → 时间轴 → 分镜帧占位）。"""
    from app.api.v1.endpoints.scripts_legacy import _process_timeline_pipeline_task

    _process_timeline_pipeline_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="timeline_pipeline",
    )


@celery_app.task(name="tasks.video_generation_poll")
def video_generation_poll_task(limit: int = 50) -> int:
    """集中轮询视频生成任务状态。"""
    from app.services.video.video_task_entrypoints import poll_pending_video_tasks

    return poll_pending_video_tasks(limit=limit)
