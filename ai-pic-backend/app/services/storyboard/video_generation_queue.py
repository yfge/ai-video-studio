from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.models.script import Script
from app.models.task import Task
from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.storyboard_media_repository import (
    load_storyboard_frames,
    resolve_storyboard_aspect_ratio,
)
from app.repositories.timeline_repository import TimelineRepository
from app.services.storyboard.storyboard_video_task_dispatch import (
    create_or_reuse_storyboard_video_task,
)
from app.services.task_worker import storyboard_video_generate_task
from sqlalchemy.orm import Session

VIDEO_WORKER_FRAME_INPUT_KEYS = (
    "frame_id",
    "description",
    "ai_prompt",
    "start_image_url",
    "start_image_urls",
    "image_url",
    "end_image_url",
    "end_image_urls",
    "reference_images",
    "start_ms",
    "end_ms",
    "duration_seconds",
)


@dataclass(frozen=True)
class StoryboardVideoQueueResult:
    task: Task
    frame_count: int
    selected_candidate_count: int
    timeline_id: int
    timeline_version: int
    mapped_clip_count: int
    reused: bool


def queue_storyboard_video_generation_task(
    db: Session,
    user: User,
    script: Script,
    *,
    prompt: str | None = None,
    frame_indexes: Sequence[int] | None = None,
    model: str | None = None,
    duration: float | None = None,
    fps: int | None = None,
    resolution: str | None = None,
    ratio: str | None = None,
    camera_fixed: bool | None = None,
    start_frame_url: str | None = None,
    target_business_id: str | None = None,
    canvas_branch: dict | None = None,
) -> StoryboardVideoQueueResult:
    frames = load_storyboard_frames(db, int(script.id))
    if not frames:
        raise ValueError("no_storyboard_frames")

    indexes = _normalize_frame_indexes(frame_indexes, len(frames))
    if start_frame_url:
        if indexes is None or len(indexes) != 1:
            raise ValueError("start_frame_requires_single_frame")
        selections = [{"frame_index": indexes[0], "start_image_url": start_frame_url}]
    else:
        selections = _latest_candidate_selections(frames, indexes)
    timeline = TimelineRepository(db).get_latest_for_episode_script(
        episode_id=int(script.episode_id),
        script_id=int(script.id),
    )
    if timeline is None:
        raise ValueError("timeline_not_found")
    timeline_rework_by_frame = _timeline_rework_contexts(
        frames,
        indexes,
        timeline,
    )
    payload = {
        "script_id": int(script.id),
        "frame_indexes": indexes,
        "frames": indexes,
        "selections": selections or None,
        "prompt": prompt,
        "model": model,
        "duration": duration,
        "fps": fps or 24,
        "resolution": resolution or "720p",
        "ratio": resolve_storyboard_aspect_ratio(db, script=script, requested=ratio),
        "watermark": None,
        "seed": None,
        "camera_fixed": camera_fixed,
        "camera_control": None,
        "service_tier": None,
        "execution_expires_after": None,
        "return_last_frame": True,
        "use_end_frame": False,
        "timeline_id": timeline.id,
        "timeline_version": timeline.version,
        "timeline_rework_by_frame": timeline_rework_by_frame,
        "canvas_branch": canvas_branch,
    }
    target_indexes = indexes if indexes is not None else list(range(len(frames)))
    dispatch_result = create_or_reuse_storyboard_video_task(
        db,
        user_id=int(user.id),
        script_id=int(script.id),
        target_business_id=target_business_id,
        payload=payload,
        frame_snapshots=[
            _video_worker_frame_snapshot(frames[index], index)
            for index in target_indexes
        ],
        dispatch=storyboard_video_generate_task.delay,
    )
    return StoryboardVideoQueueResult(
        task=dispatch_result.task,
        frame_count=len(frames),
        selected_candidate_count=len(selections),
        timeline_id=int(timeline.id),
        timeline_version=int(timeline.version),
        mapped_clip_count=len(timeline_rework_by_frame),
        reused=dispatch_result.reused,
    )


def _video_worker_frame_snapshot(frame: dict, frame_index: int) -> dict:
    """Capture provider inputs while excluding mutable generated-video outputs."""
    return {
        "frame_index": frame_index,
        "frame": {
            key: frame[key] for key in VIDEO_WORKER_FRAME_INPUT_KEYS if key in frame
        },
    }


def _timeline_rework_contexts(
    frames: list[dict],
    indexes: list[int] | None,
    timeline: Timeline,
) -> dict[str, dict]:
    target_indexes = indexes if indexes is not None else list(range(len(frames)))
    clip_ids = _video_clip_ids(timeline)
    contexts: dict[str, dict] = {}
    for index in target_indexes:
        source = frames[index].get("source")
        source = source if isinstance(source, dict) else {}
        clip_id = source.get("clip_id")
        source_version = source.get("timeline_version")
        if (
            source.get("timeline_id") != timeline.id
            or not isinstance(source_version, int)
            or source_version < 1
            or source_version > timeline.version
            or clip_id not in clip_ids
        ):
            raise ValueError("timeline_clip_mapping_missing")
        contexts[str(index)] = {
            "timeline_id": timeline.id,
            "timeline_business_id": timeline.business_id,
            "timeline_version": timeline.version,
            "source_timeline_version": source_version,
            "clip_id": clip_id,
            "action": "re_render",
            "asset_role": "generated_video",
            "reason": "production_canvas_video_candidates",
            "auto_render": False,
        }
    return contexts


def _video_clip_ids(timeline: Timeline) -> set[str]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    return {
        str(clip.get("clip_id"))
        for track in spec.get("tracks") or []
        if isinstance(track, dict)
        and (track.get("track_type") or track.get("type")) == "video"
        for clip in track.get("clips") or []
        if isinstance(clip, dict) and clip.get("clip_id")
    }


def _latest_candidate_selections(
    frames: list[dict],
    indexes: list[int] | None,
) -> list[dict]:
    target_indexes = indexes if indexes is not None else list(range(len(frames)))
    selections: list[dict] = []
    for index in target_indexes:
        frame = frames[index]
        candidates = frame.get("start_image_urls")
        latest = (
            next(
                (
                    item.strip()
                    for item in reversed(candidates)
                    if isinstance(item, str) and item.strip()
                ),
                None,
            )
            if isinstance(candidates, list)
            else None
        )
        if latest:
            selections.append({"frame_index": index, "start_image_url": latest})
    return selections


def _normalize_frame_indexes(
    frame_indexes: Sequence[int] | None,
    frame_count: int,
) -> list[int] | None:
    if frame_indexes is None:
        return None
    normalized: list[int] = []
    for raw in frame_indexes:
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            continue
        if idx < 0 or idx >= frame_count or idx in normalized:
            continue
        normalized.append(idx)
    return normalized
