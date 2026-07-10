from __future__ import annotations

from typing import Sequence

from app.models.script import Episode, Script
from app.models.task import Task
from app.models.timeline import Timeline
from app.services.audio.storyboard_from_timeline_spec import (
    generate_storyboard_support_from_timeline_spec,
)
from app.services.audio.storyboard_timeline_helpers import storyboard_has_assets
from app.services.storyboard.storyboard_image_autogen import (
    StoryboardImageQueueResult,
    queue_storyboard_image_generation_for_parent_task,
    record_storyboard_image_queue_metadata,
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
    reference_images: Sequence[str] | None = None,
) -> StoryboardImageQueueResult:
    existing_storyboard = (
        (script.extra_metadata or {}).get("storyboard")
        if isinstance(script.extra_metadata, dict)
        else None
    )
    if not overwrite_storyboard and storyboard_has_assets(existing_storyboard):
        frames = (
            existing_storyboard.get("frames")
            if isinstance(existing_storyboard, dict)
            else []
        )
        result = StoryboardImageQueueResult(
            status="skipped",
            child_task_id=None,
            queued_frame_indexes=[],
            skipped_frame_indexes=list(range(len(frames or []))),
            require_reference_images=True,
            reason="existing_storyboard_assets",
        )
        record_storyboard_image_queue_metadata(db, parent_task, result)
        return result

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
        reference_images=reference_images,
    )
