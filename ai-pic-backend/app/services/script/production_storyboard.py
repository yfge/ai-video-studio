from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.models.script import Episode, Script, Story
from app.services import story_structure_service as story_structure_svc
from app.services.audio.episode_audio_builder import generate_episode_audio_timeline
from app.services.audio.scene_audio_generator import generate_scene_dialogue_audio
from app.services.audio.storyboard_from_timeline import (
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from sqlalchemy.orm import Session

ProgressCallback = Callable[[str], None]


def annotate_storyboard_frames_with_hooks(
    frames: List[Dict[str, Any]],
    *,
    hook_schedule: Dict[str, Any],
    scoring: Optional[Dict[str, Any]] = None,
) -> int:
    """Apply hook/ad metadata to storyboard placeholder frames in-place."""

    if not frames:
        return 0

    ad_snippets = _traffic_ad_snippets(scoring or {})
    changed = 0
    candidates = [frame for frame in frames if isinstance(frame, dict)]
    non_pause = [frame for frame in candidates if frame.get("beat_type") != "pause"]
    if not non_pause:
        non_pause = candidates

    first = non_pause[0]
    changed += _set_frame_hook(
        first,
        "opening_hook",
        ad_snippets[0] if ad_snippets else _schedule_ad_snippet(hook_schedule, 0),
    )

    payoff_frame = _find_frame(non_pause, ("爽", "反击", "揭露", "证据", "逆转"))
    if payoff_frame:
        changed += _set_frame_hook(
            payoff_frame,
            "payoff",
            (
                ad_snippets[1]
                if len(ad_snippets) > 1
                else _schedule_ad_snippet(hook_schedule, 1)
            ),
        )

    last = non_pause[-1]
    if last is not first:
        changed += _set_frame_hook(
            last,
            "cliffhanger",
            ad_snippets[-1] if ad_snippets else _schedule_ad_snippet(hook_schedule, 2),
        )
    return changed


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
    storyboard = generate_storyboard_from_episode_audio_timeline(
        db,
        script=script,
        episode=episode,
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
    }


def _scene_has_dialogue_audio(scene: Any, script_id: int) -> bool:
    meta = _safe_dict(getattr(scene, "extra_metadata", None))
    payload = _safe_dict(meta.get("dialogue_audio"))
    return payload.get("script_id") == script_id and bool(payload.get("oss_url"))


def _traffic_ad_snippets(scoring: Dict[str, Any]) -> List[Dict[str, Any]]:
    traffic = _safe_dict(scoring.get("traffic_sheet"))
    snippets: List[Dict[str, Any]] = []
    for asset in _as_list(traffic.get("assets")):
        if not isinstance(asset, dict):
            continue
        hook = (
            asset.get("key_line") or asset.get("visual_hook") or asset.get("hook_type")
        )
        if not hook:
            continue
        snippets.append(
            {
                "duration_seconds": asset.get("duration_seconds"),
                "hook": hook,
                "visual_summary": asset.get("visual_hook"),
                "call_to_action": asset.get("cliff_or_cta"),
            }
        )
    return snippets


def _schedule_ad_snippet(
    hook_schedule: Dict[str, Any], index: int
) -> Optional[Dict[str, Any]]:
    candidates = _as_list(hook_schedule.get("ad_candidate_beats"))
    if index < len(candidates) and isinstance(candidates[index], dict):
        candidate = candidates[index]
        hook = candidate.get("hook")
        if hook:
            return {
                "duration_seconds": candidate.get("duration_seconds"),
                "hook": hook,
                "visual_summary": candidate.get("visual_summary"),
                "call_to_action": candidate.get("call_to_action"),
            }
    return None


def _set_frame_hook(
    frame: Dict[str, Any], hook_tag: str, ad_snippet: Optional[Dict[str, Any]]
) -> int:
    changed = 0
    if not frame.get("hook_tag"):
        frame["hook_tag"] = hook_tag
        changed += 1
    if ad_snippet and not frame.get("ad_snippet"):
        frame["ad_snippet"] = ad_snippet
        changed += 1
    return changed


def _find_frame(
    frames: List[Dict[str, Any]], keywords: tuple[str, ...]
) -> Optional[Dict[str, Any]]:
    for frame in frames:
        text = " ".join(
            str(frame.get(key) or "")
            for key in ("description", "beat_text", "prompt_description", "ai_prompt")
        )
        if any(keyword in text for keyword in keywords):
            return frame
    return None


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
