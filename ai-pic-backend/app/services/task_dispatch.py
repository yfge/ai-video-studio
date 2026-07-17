"""Route persisted tasks to their matching Celery workers."""

from __future__ import annotations

import json

from app.models.task import Task, TaskType


def dispatch_celery_task(task: Task, user_id: int) -> bool:
    """Dispatch a task to its matching Celery worker."""
    params = {}
    if task.parameters:
        try:
            params = json.loads(task.parameters)
        except Exception:
            params = {}

    from app.services.task_worker import (
        episode_generate_task,
        script_audio_timeline_generate_task,
        script_dialogue_audio_generate_task,
        script_generate_task,
        script_regenerate_task,
        story_generate_task,
        story_novel_generate_task,
        storyboard_generate_task,
        timeline_pipeline_generate_task,
    )
    from app.services.task_worker_assets import (
        environment_image_generate_task,
        environment_image_variant_task,
        virtual_ip_image_generate_task,
        virtual_ip_image_variant_task,
    )
    from app.services.task_worker_grid_storyboard import (
        grid_storyboard_sheet_generate_task,
    )
    from app.services.task_worker_storyboard_media import (
        storyboard_image_generate_task,
        storyboard_video_generate_task,
    )
    from app.services.task_worker_timeline_rework import (
        timeline_clip_rework_video_generate_task,
    )

    if (
        task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION
        and isinstance(params, dict)
        and params.get("kind")
        in {"timeline_clip_storyboard", "timeline_storyboard_grid"}
    ):
        grid_storyboard_sheet_generate_task.delay(task.id, params, user_id)
        return True

    if (
        task.task_type == TaskType.VIDEO_GENERATION
        and isinstance(params, dict)
        and params.get("timeline_id")
        and params.get("clip_id")
    ):
        timeline_clip_rework_video_generate_task.delay(task.id, params, user_id)
        return True

    dispatch_map = {
        TaskType.STORY_GENERATION: story_generate_task,
        TaskType.TEXT_GENERATION: story_novel_generate_task,
        TaskType.EPISODE_GENERATION: episode_generate_task,
        TaskType.SCRIPT_GENERATION: script_generate_task,
        TaskType.SCRIPT_REVIEW: script_regenerate_task,
        TaskType.DIALOGUE_AUDIO_GENERATION: script_dialogue_audio_generate_task,
        TaskType.TIMELINE_GENERATION: script_audio_timeline_generate_task,
        TaskType.STORYBOARD_GENERATION: storyboard_generate_task,
        TaskType.TIMELINE_PIPELINE: timeline_pipeline_generate_task,
        TaskType.VIRTUAL_IP_IMAGE_GENERATION: virtual_ip_image_generate_task,
        TaskType.VIRTUAL_IP_IMAGE_VARIANT_GENERATION: virtual_ip_image_variant_task,
        TaskType.ENVIRONMENT_IMAGE_GENERATION: environment_image_generate_task,
        TaskType.ENVIRONMENT_IMAGE_VARIANT_GENERATION: environment_image_variant_task,
        TaskType.STORYBOARD_IMAGE_GENERATION: storyboard_image_generate_task,
        TaskType.VIDEO_GENERATION: storyboard_video_generate_task,
    }

    celery_task = dispatch_map.get(task.task_type)
    if celery_task is None:
        return False

    celery_task.delay(task.id, params, user_id)
    return True
