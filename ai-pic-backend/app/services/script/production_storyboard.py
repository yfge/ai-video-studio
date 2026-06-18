from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session

from app.models.script import Episode, Script, Story
from app.services.audio.storyboard_from_timeline_spec import (
    generate_storyboard_support_from_timeline_spec,
)
from app.services.script.production_storyboard_hooks import (
    annotate_storyboard_frames_with_hooks,
)
from app.services.storyboard.storyboard_image_autogen import (
    queue_storyboard_image_generation,
)
from app.services.timeline_pipeline_runner import run_timeline_main_chain

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

    def _progress(message: str) -> None:
        if progress_callback:
            progress_callback(f"生产级链路：{message}")

    owner_user_id = user_id or getattr(story, "user_id", None)
    main_chain = await run_timeline_main_chain(
        db,
        story=story,
        episode=episode,
        script=script,
        tts_model=tts_model,
        timing_model=timing_model,
        overwrite_audio=True,
        overwrite_timeline=True,
        min_pause_duration_ms=min_pause_duration_ms,
        use_duration_control=True,
        user_id=owner_user_id,
        progress_callback=_progress,
    )
    timeline = main_chain.audio_timeline
    import_result = main_chain.import_result
    timeline_with_shot_plan = main_chain.timeline

    if progress_callback:
        progress_callback("生产级链路：生成分镜占位")
    storyboard = generate_storyboard_support_from_timeline_spec(
        db,
        script=script,
        episode=episode,
        timeline=timeline_with_shot_plan,
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
        user_id=owner_user_id,
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
            "id": timeline_with_shot_plan.id,
            "version": timeline_with_shot_plan.version,
            "source_audio_timeline_version": (
                timeline_with_shot_plan.source_audio_timeline_version
            ),
            "action": import_result.action,
        },
        "storyboard_version": script.storyboard_version,
        "hook_annotation_count": changed,
        "storyboard_image_generation": image_result.to_metadata(),
    }
