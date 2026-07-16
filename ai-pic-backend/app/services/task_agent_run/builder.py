from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.task_agent_run.builders_assets import (
    build_environment_images_agent_run,
    build_virtual_ip_image_agent_run,
    build_virtual_ip_variant_agent_run,
)
from app.services.task_agent_run.builders_narrative import (
    build_episode_agent_run,
    build_script_run,
    build_story_agent_run,
    parse_episode_task_ids,
)
from app.services.task_agent_run.builders_script_ops import (
    build_dialogue_audio_agent_run,
    build_storyboard_from_audio_timeline_agent_run,
    build_storyboard_generation_agent_run,
    build_storyboard_image_agent_run,
    build_timeline_generation_agent_run,
    build_timeline_pipeline_agent_run,
)
from app.services.task_agent_run.builders_text import build_story_novel_export_agent_run
from app.services.task_agent_run.builders_video import build_video_generation_agent_run
from app.services.task_agent_run.utils import (
    loads_task_parameters,
    maybe_int,
    parse_result_id,
)


def build_agent_run(
    db,
    task,
    *,
    user_id: int,
    kind: str,
    request_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if kind == "story":
        return build_story_agent_run(db, task, user_id=user_id)

    if kind == "episode":
        story_id, created_episode_ids = parse_episode_task_ids(
            task, request_dict=request_dict
        )
        if story_id is None:
            params = loads_task_parameters(getattr(task, "parameters", None))
            story_id = maybe_int(params.get("story_id"))
        return build_episode_agent_run(
            db,
            task,
            user_id=user_id,
            story_id=story_id,
            created_episode_ids=created_episode_ids,
        )

    if kind == "script":
        result = parse_result_id(
            getattr(task, "result_file_path", None), prefix="script"
        )
        if not result:
            return {}
        script_id_token = result.split(":", 1)[0]
        script_id = maybe_int(script_id_token)
        if script_id is None:
            return {}
        return build_script_run(db, task, user_id=user_id, script_id=script_id)

    if kind == "dialogue_audio":
        return build_dialogue_audio_agent_run(db, task, user_id=user_id)

    if kind == "timeline_generation":
        return build_timeline_generation_agent_run(db, task, user_id=user_id)

    if kind == "timeline_pipeline":
        return build_timeline_pipeline_agent_run(db, task, user_id=user_id)

    if kind == "storyboard_generation":
        return build_storyboard_generation_agent_run(db, task, user_id=user_id)

    if kind == "storyboard_from_audio_timeline":
        return build_storyboard_from_audio_timeline_agent_run(db, task, user_id=user_id)

    if kind == "storyboard_images":
        return build_storyboard_image_agent_run(db, task, user_id=user_id)

    if kind == "environment_images":
        return build_environment_images_agent_run(
            db, task, user_id=user_id, variant=False
        )

    if kind == "environment_image_variants":
        return build_environment_images_agent_run(
            db, task, user_id=user_id, variant=True
        )

    if kind == "virtual_ip_image":
        return build_virtual_ip_image_agent_run(db, task, user_id=user_id)

    if kind == "virtual_ip_image_variants":
        return build_virtual_ip_variant_agent_run(db, task, user_id=user_id)

    if kind == "text_generation":
        return build_story_novel_export_agent_run(db, task, user_id=user_id)

    if kind == "video_generation":
        return build_video_generation_agent_run(db, task, user_id=user_id)

    return {}
