from __future__ import annotations

from app.models.script import Episode, Script
from app.models.task import Task
from app.models.timeline import Timeline
from app.services.audio.storyboard_from_timeline_spec import (
    generate_storyboard_support_from_timeline_spec,
)
from app.services.storyboard.storyboard_image_autogen import (
    StoryboardImageQueueResult,
    queue_storyboard_image_generation_for_parent_task,
)


def generate_storyboard_placeholders_and_queue_images(
    db,
    *,
    parent_task: Task | None,
    script: Script,
    episode: Episode,
    timeline: Timeline,
    user_id: int,
    overwrite_storyboard: bool,
    min_pause_ms: int,
) -> StoryboardImageQueueResult:
    storyboard = generate_storyboard_support_from_timeline_spec(
        db,
        script=script,
        episode=episode,
        timeline=timeline,
        overwrite_existing=overwrite_storyboard,
        min_pause_duration_ms=min_pause_ms,
    )
    return queue_storyboard_image_generation_for_parent_task(
        db,
        parent_task,
        script_id=script.id,
        user_id=user_id,
        frames=storyboard.get("frames") or [],
        aspect_ratio=getattr(episode, "aspect_ratio", None),
    )
