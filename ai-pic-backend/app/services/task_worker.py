"""
Celery 任务入口

目前主要用于调度 Story/Episode/Script 相关的异步生成任务。
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.story_generate")
def story_generate_task(task_id: int, request_dict: Dict[str, Any], user_id: int) -> None:
    """
    异步故事生成任务入口。

    为避免导入环造成副作用，这里的依赖在函数内部按需导入。
    """
    from app.api.v1.endpoints.stories import _process_story_generation_task

    _process_story_generation_task(task_id, request_dict, user_id)


@celery_app.task(name="tasks.episode_generate")
def episode_generate_task(task_id: int, request_dict: Dict[str, Any], user_id: int) -> None:
    """异步剧集生成任务入口。"""
    from app.api.v1.endpoints.episodes import _process_episode_generation_task

    _process_episode_generation_task(task_id, request_dict, user_id)


@celery_app.task(name="tasks.script_generate")
def script_generate_task(task_id: int, request_dict: Dict[str, Any], user_id: int) -> None:
    """异步剧本生成任务入口。"""
    from app.api.v1.endpoints.scripts import _process_script_generation_task

    _process_script_generation_task(task_id, request_dict, user_id)

