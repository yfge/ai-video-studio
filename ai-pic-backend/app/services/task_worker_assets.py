"""
Celery task registrations for asset/image generation.

Kept in a dedicated module to keep app.services.task_worker under the 250-line
service file limit.
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.virtual_ip_image_generate")
def virtual_ip_image_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步虚拟 IP 文生图任务入口。"""
    from app.api.v1.endpoints.virtual_ip_images import process_virtual_ip_image_task

    process_virtual_ip_image_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="virtual_ip_image",
    )


@celery_app.task(name="tasks.virtual_ip_image_variant")
def virtual_ip_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步虚拟 IP 图生图任务入口。"""
    from app.api.v1.endpoints.virtual_ip_images import (
        process_virtual_ip_image_variant_task,
    )

    process_virtual_ip_image_variant_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="virtual_ip_image_variants",
    )


@celery_app.task(name="tasks.environment_image_generate")
def environment_image_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步环境文生图任务入口。"""
    from app.api.v1.endpoints.story_structure import process_environment_image_task

    process_environment_image_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="environment_images",
    )


@celery_app.task(name="tasks.environment_image_variant")
def environment_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """异步环境图生图任务入口。"""
    from app.api.v1.endpoints.story_structure import (
        process_environment_image_variant_task,
    )

    process_environment_image_variant_task(task_id, payload, user_id)
    from app.services.task_agent_run_persistence import persist_task_agent_run

    persist_task_agent_run(
        task_id=task_id,
        user_id=user_id,
        kind="environment_image_variants",
    )

