"""Storyboard support generation from Timeline Spec v1 clips."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.script import Episode, Script
from app.models.timeline import Timeline
from app.repositories.timeline_repository import TimelineRepository
from app.services.audio.storyboard_from_timeline import (
    build_storyboard_frames_from_audio_timeline,
)
from app.services.audio.storyboard_from_timeline_shot_plan import (
    build_storyboard_frames_from_timeline_shot_plan,
)
from app.services.audio.storyboard_timeline_helpers import check_existing_assets
from app.services.storyboard.storyboard_prompt_utils import (
    apply_storyboard_prompt_optimizations,
)
from sqlalchemy.orm import Session


def build_storyboard_frames_from_timeline_spec(
    *,
    timeline_spec: dict[str, Any],
    min_pause_duration_ms: int = 1500,
) -> list[dict[str, Any]]:
    """Build storyboard support frames from Timeline Spec v1 clips."""
    shot_plan_frames = build_storyboard_frames_from_timeline_shot_plan(
        timeline_spec=timeline_spec
    )
    if shot_plan_frames:
        return shot_plan_frames

    beats = _timeline_spec_clips_to_beats(timeline_spec)
    if not beats:
        raise RuntimeError("timeline_spec_missing_clips")
    return build_storyboard_frames_from_audio_timeline(
        audio_timeline={"beats": beats},
        min_pause_duration_ms=min_pause_duration_ms,
    )


def generate_storyboard_support_from_timeline_spec(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    timeline: Timeline | None = None,
    timeline_spec: dict[str, Any] | None = None,
    overwrite_existing: bool = False,
    min_pause_duration_ms: int = 1500,
) -> dict[str, Any]:
    """Generate storyboard support view from the latest Timeline Spec v1."""
    if timeline_spec is None:
        if timeline is None:
            timeline = TimelineRepository(db).get_latest_for_episode_script(
                episode_id=episode.id,
                script_id=script.id,
            )
        timeline_spec = timeline.spec if timeline is not None else None

    if not isinstance(timeline_spec, dict):
        raise RuntimeError("timeline_spec_not_found")
    if timeline_spec.get("script_id") != script.id:
        raise RuntimeError("timeline_spec_script_mismatch")

    frames = build_storyboard_frames_from_timeline_spec(
        timeline_spec=timeline_spec,
        min_pause_duration_ms=min_pause_duration_ms,
    )
    from app.services.storyboard.storyboard_audio_context_enricher import (
        enrich_storyboard_frames_with_story_context,
    )

    enrich_storyboard_frames_with_story_context(
        db,
        story_id=episode.story_id,
        script_id=script.id,
        frames=frames,
        max_reference_images=3,
        max_character_cards=3,
    )
    apply_storyboard_prompt_optimizations(frames)
    if not frames:
        raise RuntimeError("no_frames_generated_from_timeline_spec")

    extra = dict(script.extra_metadata or {})
    existing = extra.get("storyboard") if isinstance(extra, dict) else None
    if not overwrite_existing and isinstance(existing, dict):
        check_existing_assets(existing)

    timeline_id = getattr(timeline, "id", None) or timeline_spec.get("timeline_id")
    timeline_version = getattr(timeline, "version", None) or timeline_spec.get(
        "version"
    )
    source_audio_version = getattr(
        timeline, "source_audio_timeline_version", None
    ) or timeline_spec.get("source_audio_timeline_version")
    generation_method = _frame_generation_method(frames)
    sb_meta = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generation_source": "timeline_spec",
        "generation_method": generation_method,
        "source_role": "storyboard_support_view",
        "script_id": script.id,
        "episode_id": episode.id,
        "timeline_id": timeline_id,
        "timeline_version": timeline_version,
        "source_audio_timeline_version": source_audio_version,
        "audio_timeline_version": source_audio_version,
    }
    extra["storyboard"] = {"frames": frames, "meta": sb_meta}
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.utcnow()
    script.storyboard_version = (script.storyboard_version or 0) + 1
    db.add(script)
    db.commit()
    db.refresh(script)
    return {"frames": frames, "meta": sb_meta}


def _timeline_spec_clips_to_beats(
    timeline_spec: dict[str, Any]
) -> list[dict[str, Any]]:
    tracks = timeline_spec.get("tracks")
    if not isinstance(tracks, list):
        return []

    dialogue_clips = _clips_for_track(tracks, "dialogue")
    clips = dialogue_clips or _clips_for_track(tracks, "video")
    timeline_id = timeline_spec.get("timeline_id")
    timeline_version = timeline_spec.get("version")
    source_audio_version = timeline_spec.get("source_audio_timeline_version")

    beats: list[dict[str, Any]] = []
    for clip in clips:
        if not isinstance(clip, dict):
            continue
        start_ms = clip.get("start_ms")
        end_ms = clip.get("end_ms")
        if start_ms is None or end_ms is None:
            continue
        source = clip.get("source") if isinstance(clip.get("source"), dict) else {}
        source_refs = (
            clip.get("source_refs") if isinstance(clip.get("source_refs"), dict) else {}
        )
        scene_id = clip.get("scene_id") or source.get("scene_id")
        beat_id = (
            clip.get("beat_id")
            or source.get("beat_id")
            or source_refs.get("scene_beat_id")
        )
        beats.append(
            {
                "scene_id": scene_id,
                "scene_number": clip.get("scene_number"),
                "beat_id": beat_id,
                "beat_type": clip.get("beat_type") or "dialogue",
                "speaker_name": clip.get("speaker_name"),
                "text": clip.get("text"),
                "dialogue_action": clip.get("dialogue_action"),
                "dialogue_emotion": clip.get("dialogue_emotion"),
                "characters_involved": clip.get("character_ids") or [],
                "start_ms": start_ms,
                "end_ms": end_ms,
                "generation_source": "timeline_spec",
                "generation_method": "timeline_spec",
                "timeline_clip_id": clip.get("clip_id"),
                "timeline_track_type": clip.get("track_type"),
                "timeline_id": timeline_id,
                "timeline_version": timeline_version,
                "source_audio_timeline_version": source_audio_version,
                "source": {
                    "kind": "timeline_clip",
                    "clip_id": clip.get("clip_id"),
                    "track_type": clip.get("track_type"),
                    "scene_id": scene_id,
                    "beat_id": beat_id,
                    "timeline_id": timeline_id,
                    "timeline_version": timeline_version,
                },
            }
        )
    return sorted(
        beats,
        key=lambda beat: (_safe_ms(beat["start_ms"]), _safe_ms(beat["end_ms"])),
    )


def _clips_for_track(tracks: list[Any], track_type: str) -> list[dict[str, Any]]:
    for track in tracks:
        if not isinstance(track, dict):
            continue
        if track.get("track_type") != track_type and track.get("type") != track_type:
            continue
        clips = track.get("clips")
        return clips if isinstance(clips, list) else []
    return []


def _safe_ms(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _frame_generation_method(frames: list[dict[str, Any]]) -> str:
    methods = {
        str(frame.get("generation_method") or "")
        for frame in frames
        if isinstance(frame, dict)
    }
    if "timeline_shot_plan" in methods:
        return "timeline_shot_plan"
    return "timeline_spec"
