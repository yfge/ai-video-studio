from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.models.timeline import Timeline
from app.repositories.audio_timeline_repository import count_scene_beats
from app.services import story_structure_service as story_structure_svc
from app.services.audio.episode_audio_builder import generate_episode_audio_timeline
from app.services.audio.scene_audio_generator import generate_scene_dialogue_audio
from app.services.duration_controlled_dialogue_service import (
    generate_dialogue_with_duration_control,
)
from app.services.script.timeline_shot_plan_step import (
    generate_timeline_shot_plan_from_current_version,
)
from app.services.timeline_import_service import (
    TimelineImportResult,
    import_audio_timeline_to_timeline_spec,
)

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class TimelineMainChainResult:
    audio_timeline: dict[str, Any] | None
    import_result: TimelineImportResult
    timeline: Timeline


async def run_timeline_main_chain(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    tts_model: str = "speech-2.6-hd",
    timing_model: str | None = None,
    overwrite_audio: bool = False,
    overwrite_timeline: bool = False,
    use_duration_control: bool = False,
    user_id: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> TimelineMainChainResult:
    """Run the shared dialogue audio -> Timeline Spec -> shot plan chain."""

    scenes = story_structure_svc.list_scenes_by_script(db, script.id)
    scenes = sorted(scenes, key=scene_number_sort_key)
    if not scenes:
        raise RuntimeError("no_scenes_found")

    if use_duration_control:
        await _run_duration_controlled_dialogue(
            db,
            story=story,
            episode=episode,
            script=script,
            scenes=scenes,
            tts_model=tts_model,
            timing_model=timing_model,
            progress_callback=progress_callback,
        )
    else:
        await _run_legacy_scene_dialogue_audio(
            db,
            story=story,
            episode=episode,
            script=script,
            scenes=scenes,
            tts_model=tts_model,
            timing_model=timing_model,
            overwrite_audio=overwrite_audio,
            progress_callback=progress_callback,
        )

    if progress_callback:
        progress_callback("生成时间轴…")
    audio_timeline_payload = None
    if not overwrite_timeline and episode_has_audio_timeline(episode, script.id):
        if progress_callback:
            progress_callback("过渡时间轴已存在，导入 Timeline Spec…")
    else:
        audio_timeline_payload = await generate_episode_audio_timeline(
            db,
            story=story,
            episode=episode,
            script=script,
        )

    import_result = import_audio_timeline_to_timeline_spec(
        db,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline_payload,
        overwrite=overwrite_timeline,
        user_id=user_id,
    )
    if progress_callback:
        progress_callback(f"Timeline Spec v1 {import_result.action}")
        progress_callback("生成 Timeline 镜头计划…")

    timeline = await generate_timeline_shot_plan_from_current_version(
        db,
        import_result.timeline,
        user_id=user_id,
    )
    return TimelineMainChainResult(
        audio_timeline=audio_timeline_payload,
        import_result=import_result,
        timeline=timeline,
    )


async def _run_duration_controlled_dialogue(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scenes: list[Scene],
    tts_model: str,
    timing_model: str | None,
    progress_callback: ProgressCallback | None,
) -> None:
    if progress_callback:
        progress_callback(f"时长精控模式 - 编排 {len(scenes)} 个场景…")

    result = await generate_dialogue_with_duration_control(
        db,
        story=story,
        episode=episode,
        script=script,
        scenes=scenes,
        tts_model=str(tts_model),
        overwrite_beats=True,
        timing_model=timing_model,
        progress_callback=progress_callback,
    )
    if not result.get("success", False):
        errors = result.get("errors", [])
        final_validation = result.get("final_validation", {})
        if final_validation and not final_validation.get("passed"):
            ratio = final_validation.get("duration_ratio", 0)
            if progress_callback:
                progress_callback(f"时长验证未通过 {ratio:.1%}（允许±10%）")
            return
        raise RuntimeError(f"Duration Orchestrator failed: {'; '.join(errors)}")

    ratio = result.get("statistics", {}).get("duration_ratio", 0)
    if progress_callback:
        progress_callback(f"时长精控完成 {ratio:.1%}")


async def _run_legacy_scene_dialogue_audio(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scenes: list[Scene],
    tts_model: str,
    timing_model: str | None,
    overwrite_audio: bool,
    progress_callback: ProgressCallback | None,
) -> None:
    if progress_callback:
        progress_callback("生成对白音轨…")

    episode_duration_minutes = getattr(episode, "duration_minutes", None)
    fallback_target_seconds = None
    if episode_duration_minutes and len(scenes) > 0:
        fallback_target_seconds = (episode_duration_minutes * 60) // len(scenes)

    total = len(scenes)
    skipped = 0
    for idx, scene in enumerate(scenes, start=1):
        if not overwrite_audio and scene_has_dialogue_audio(scene, script.id):
            beat_count = count_scene_beats(db, int(scene.id))
            if beat_count > 0:
                skipped += 1
                if progress_callback:
                    progress_callback(f"对白音轨 {idx}/{total}（跳过 {skipped}）")
                continue

        if progress_callback:
            progress_callback(f"对白音轨 {idx}/{total}（跳过 {skipped}）")

        scene_target = getattr(scene, "estimated_duration_seconds", None)
        if scene_target is None:
            scene_target = fallback_target_seconds

        await generate_scene_dialogue_audio(
            db,
            story=story,
            episode=episode,
            script=script,
            scene=scene,
            tts_model=str(tts_model),
            overwrite_beats=True,
            timing_model=timing_model,
            target_duration_seconds=scene_target,
        )


def scene_has_dialogue_audio(scene: Scene, script_id: int) -> bool:
    meta = scene.extra_metadata
    if not isinstance(meta, dict):
        return False
    payload = meta.get("dialogue_audio")
    if not isinstance(payload, dict):
        return False
    if payload.get("script_id") != script_id:
        return False
    return bool(payload.get("oss_url"))


def scene_number_sort_key(scene: Scene) -> tuple[int, int, str]:
    raw = getattr(scene, "scene_number", None)
    num = _to_int(raw)
    if num is None:
        return (1, 0, str(raw or ""))
    return (0, num, str(raw or ""))


def episode_has_audio_timeline(episode: Episode, script_id: int) -> bool:
    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    timeline = meta.get("audio_timeline") if isinstance(meta, dict) else None
    if not isinstance(timeline, dict):
        return False
    if timeline.get("script_id") != script_id:
        return False
    ep_audio = timeline.get("episode_audio")
    if not isinstance(ep_audio, dict) or not ep_audio.get("oss_url"):
        return False
    beats = timeline.get("beats")
    return isinstance(beats, list) and len(beats) > 0


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
