from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.models.script import Episode, Script, Story
from app.services import story_structure_service as story_structure_svc
from app.services.audio.episode_audio_builder import generate_episode_audio_timeline
from app.services.audio.scene_audio_generator import generate_scene_dialogue_audio
from app.services.audio.storyboard_from_timeline_spec import (
    generate_storyboard_support_from_timeline_spec,
)
from app.services.storyboard.storyboard_image_autogen import (
    queue_storyboard_image_generation,
)
from app.services.script.production_storyboard_hooks import (
    annotate_storyboard_frames_with_hooks,
)
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from sqlalchemy.orm import Session

ProgressCallback = Callable[[str], None]


async def run_auto_timeline_placeholders(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    hook_schedule: Dict[str, Any],
    scoring: Optional[Dict[str, Any]],
    tts_model: str = "speech-2.6-hd",
    timing_model: Optional[str] = None,
    min_pause_duration_ms: int = 1500,
    progress_callback: Optional[ProgressCallback] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate dialogue audio, episode audio timeline, and storyboard placeholders."""

    scenes = story_structure_svc.list_scenes_by_script(db, script.id)
    scenes = sorted(scenes, key=lambda scene: _safe_int(scene.scene_number))
    if not scenes:
        raise RuntimeError("production_pipeline_no_scenes_for_timeline")

    total = len(scenes)
    for idx, scene in enumerate(scenes, start=1):
        if progress_callback:
            progress_callback(f"生产级链路：对白音轨 {idx}/{total}")
        has_dialogue_audio = _scene_has_dialogue_audio(scene, script.id)
        has_scene_beats = bool(story_structure_svc.list_beats_by_scene(db, scene.id))
        if has_dialogue_audio and has_scene_beats:
            continue
        await generate_scene_dialogue_audio(
            db,
            story=story,
            episode=episode,
            script=script,
            scene=scene,
            tts_model=tts_model,
            overwrite_beats=True,
            timing_model=timing_model,
            target_duration_seconds=getattr(scene, "estimated_duration_seconds", None),
        )

    if progress_callback:
        progress_callback("生产级链路：生成 episode audio timeline")
    timeline = await generate_episode_audio_timeline(
        db,
        story=story,
        episode=episode,
        script=script,
    )
    import_result = import_audio_timeline_to_timeline_spec(
        db,
        episode=episode,
        script=script,
        audio_timeline=timeline,
        overwrite=True,
        user_id=user_id or getattr(story, "user_id", None),
    )

    if progress_callback:
        progress_callback("生产级链路：生成分镜占位")
    storyboard = generate_storyboard_support_from_timeline_spec(
        db,
        script=script,
        episode=episode,
        timeline=import_result.timeline,
        overwrite_existing=True,
        min_pause_duration_ms=min_pause_duration_ms,
    )
    changed = annotate_storyboard_frames_with_hooks(
        storyboard.get("frames") or [],
        hook_schedule=hook_schedule,
        scoring=scoring,
    )
    extra = dict(script.extra_metadata or {})
    sb = dict(extra.get("storyboard") or {})
    sb["frames"] = storyboard.get("frames") or []
    meta = dict(sb.get("meta") or storyboard.get("meta") or {})
    meta["hook_annotation_count"] = changed
    sb["meta"] = meta
    extra["storyboard"] = sb
    script.extra_metadata = extra
    db.add(script)
    db.commit()
    db.refresh(script)
    if progress_callback:
        progress_callback("生产级链路：创建分镜画面生成任务")
    image_result = queue_storyboard_image_generation(
        db,
        script_id=script.id,
        user_id=user_id or getattr(story, "user_id", None),
        frames=storyboard.get("frames") or [],
        aspect_ratio=getattr(episode, "aspect_ratio", None),
        require_reference_images=True,
    )
    return {
        "status": "completed",
        "audio_timeline_version": ((timeline or {}).get("episode_audio") or {}).get(
            "version"
        ),
        "timeline_spec": {
            "id": import_result.timeline.id,
            "version": import_result.timeline.version,
            "source_audio_timeline_version": (
                import_result.timeline.source_audio_timeline_version
            ),
            "action": import_result.action,
        },
        "storyboard_version": script.storyboard_version,
        "hook_annotation_count": changed,
        "storyboard_image_generation": image_result.to_metadata(),
    }


def _scene_has_dialogue_audio(scene: Any, script_id: int) -> bool:
    meta = getattr(scene, "extra_metadata", None)
    if not isinstance(meta, dict):
        return False
    payload = meta.get("dialogue_audio")
    if not isinstance(payload, dict):
        return False
    return payload.get("script_id") == script_id and bool(payload.get("oss_url"))


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
