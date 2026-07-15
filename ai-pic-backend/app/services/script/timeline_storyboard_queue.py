from __future__ import annotations

from copy import deepcopy
from typing import Sequence

from app.models.script import Episode, Script
from app.models.task import Task
from app.models.timeline import Timeline
from app.repositories.storyboard_media_repository import (
    save_storyboard_reference_context,
)
from app.services.audio.storyboard_from_timeline_spec import (
    generate_storyboard_support_from_timeline_spec,
)
from app.services.audio.storyboard_timeline_helpers import storyboard_has_assets
from app.services.storyboard.storyboard_audio_context_enricher import (
    enrich_storyboard_frames_with_story_context,
)
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
    existing_frames = (
        existing_storyboard.get("frames")
        if isinstance(existing_storyboard, dict)
        and isinstance(existing_storyboard.get("frames"), list)
        else []
    )
    if not overwrite_storyboard and storyboard_has_assets(existing_storyboard):
        result = StoryboardImageQueueResult(
            status="skipped",
            child_task_id=None,
            queued_frame_indexes=[],
            skipped_frame_indexes=list(range(len(existing_frames))),
            require_reference_images=True,
            reason="existing_storyboard_assets",
        )
        record_storyboard_image_queue_metadata(db, parent_task, result)
        return result
    if not overwrite_storyboard and _matches_current_timeline(
        existing_storyboard, timeline
    ):
        refreshed_frames = [
            deepcopy(frame) if isinstance(frame, dict) else frame
            for frame in existing_frames
        ]
        _hydrate_frame_identity_from_timeline(
            frames=refreshed_frames,
            timeline=timeline,
        )
        enrich_storyboard_frames_with_story_context(
            db,
            story_id=episode.story_id,
            script_id=script.id,
            frames=refreshed_frames,
            max_reference_images=3,
            max_character_cards=3,
            update_prompt_context=False,
        )
        if refreshed_frames != existing_frames:
            save_storyboard_reference_context(
                db,
                script=script,
                frames=refreshed_frames,
            )
        return queue_storyboard_image_generation_for_parent_task(
            db,
            parent_task,
            script_id=script.id,
            user_id=user_id,
            frames=refreshed_frames,
            aspect_ratio=getattr(episode, "aspect_ratio", None),
            reference_images=reference_images,
        )

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


def _matches_current_timeline(storyboard: object, timeline: Timeline) -> bool:
    if not isinstance(storyboard, dict):
        return False
    frames = storyboard.get("frames")
    meta = storyboard.get("meta")
    return bool(
        isinstance(frames, list)
        and frames
        and isinstance(meta, dict)
        and meta.get("generation_source") == "timeline_spec"
        and meta.get("timeline_id") == timeline.id
        and meta.get("timeline_version") == timeline.version
    )


def _hydrate_frame_identity_from_timeline(
    *,
    frames: list[object],
    timeline: Timeline,
) -> None:
    """Backfill canonical identity fields missing from older placeholders."""

    clips_by_id: dict[str, dict] = {}
    tracks = (timeline.spec or {}).get("tracks")
    for track in tracks if isinstance(tracks, list) else []:
        if not isinstance(track, dict):
            continue
        if track.get("track_type") != "video" and track.get("type") != "video":
            continue
        clips = track.get("clips")
        for clip in clips if isinstance(clips, list) else []:
            clip_id = clip.get("clip_id") if isinstance(clip, dict) else None
            if isinstance(clip_id, str) and clip_id:
                clips_by_id[clip_id] = clip

    for frame in frames:
        if not isinstance(frame, dict):
            continue
        clip_id = frame.get("timeline_clip_id")
        clip = clips_by_id.get(clip_id) if isinstance(clip_id, str) else None
        if not clip:
            continue
        speaker = clip.get("speaker_name")
        if (
            not frame.get("speaker_name")
            and isinstance(speaker, str)
            and speaker.strip()
        ):
            frame["speaker_name"] = speaker.strip()
        if frame.get("characters"):
            continue
        characters: list[str] = []
        for key in ("characters", "character_names"):
            values = clip.get(key)
            if not isinstance(values, list):
                continue
            characters.extend(
                value.strip()
                for value in values
                if isinstance(value, str) and value.strip()
            )
        if isinstance(speaker, str) and speaker.strip():
            characters.append(speaker.strip())
        if characters:
            frame["characters"] = list(dict.fromkeys(characters))
