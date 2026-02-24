"""Dialogue audio generation endpoints and async task processor."""

from __future__ import annotations

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.story_structure import SceneBeat
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services import story_structure_service as story_structure_svc
from app.services.dialogue_audio_service import generate_scene_dialogue_audio
from app.services.duration_controlled_dialogue_service import (
    generate_dialogue_with_duration_control,
)
from app.services.task_worker import script_dialogue_audio_generate_task
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .audio_pipeline_utils import (
    friendly_task_title,
    load_script_with_access,
    run_async_task_sync,
    scene_has_dialogue_audio,
    scene_number_sort_key,
    to_int,
    update_task_progress,
)

router = APIRouter()


class ScriptDialogueAudioGenerateRequest(BaseModel):
    tts_model: str | None = Field(None, description="TTS model (default speech-2.6-hd)")
    timing_model: str | None = Field(
        None,
        description="Timeline LLM model (uses system default when empty)",
    )
    scene_numbers: list[int] | None = Field(
        None,
        description="Optional scene numbers to generate; empty means all scenes",
    )
    overwrite_audio: bool = Field(False, description="Overwrite existing scene audio")
    overwrite_beats: bool = Field(True, description="Overwrite existing scene beats")
    use_duration_control: bool = Field(
        False,
        description="Enable Duration Orchestrator for tighter duration control",
    )


@router.post("/{script_id}/dialogue-audio/generate-async")
async def generate_script_dialogue_audio_async(
    script_id: int,
    body: ScriptDialogueAudioGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Queue async generation of scene dialogue audio and scene beats."""
    script = load_script_with_access(db, script_id, current_user)
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None
    params = body.model_dump()
    params["script_id"] = script_id

    task = Task(
        title=friendly_task_title("对白音轨生成", script, episode, story),
        description="生成场景对白音轨（scene）",
        task_type=TaskType.DIALOGUE_AUDIO_GENERATION,
        prompt=f"Dialogue audio generation for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    script_dialogue_audio_generate_task.delay(task.id, params, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_script_dialogue_audio_task(
    task_id: int,
    payload: dict,
    user_id: int,
) -> None:
    """Celery worker handler for script dialogue audio generation."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_audio = bool(payload.get("overwrite_audio"))
        overwrite_beats = bool(payload.get("overwrite_beats", True))
        tts_model = payload.get("tts_model") or "speech-2.6-hd"
        timing_model = payload.get("timing_model")
        use_duration_control = bool(payload.get("use_duration_control", False))

        selected_scene_numbers = payload.get("scene_numbers") or []
        selected_set = {
            int(x)
            for x in selected_scene_numbers
            if isinstance(x, (int, str)) and to_int(x) is not None
        }

        async def _run() -> None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise RuntimeError("user_not_found")

            script = load_script_with_access(db, script_id, user)
            if not script:
                raise RuntimeError("script_not_found")

            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")

            story = episode.story
            if not story:
                raise RuntimeError("story_not_found")

            scenes = story_structure_svc.list_scenes_by_script(db, script_id)
            if selected_set:
                scenes = [
                    scene
                    for scene in scenes
                    if to_int(getattr(scene, "scene_number", None)) in selected_set
                ]
            scenes = sorted(scenes, key=scene_number_sort_key)
            if not scenes:
                raise RuntimeError("no_scenes_found")

            if use_duration_control:
                update_task_progress(
                    db,
                    task,
                    f"时长精控模式：正在编排 {len(scenes)} 个场景",
                )

                def _progress_cb(message: str) -> None:
                    update_task_progress(db, task, message)

                result = await generate_dialogue_with_duration_control(
                    db,
                    story=story,
                    episode=episode,
                    script=script,
                    scenes=scenes,
                    tts_model=str(tts_model),
                    overwrite_beats=overwrite_beats,
                    timing_model=timing_model,
                    progress_callback=_progress_cb,
                )
                if not result.get("success", False):
                    errors = result.get("errors", [])
                    final_validation = result.get("final_validation", {})
                    if final_validation and not final_validation.get("passed"):
                        ratio = final_validation.get("duration_ratio", 0)
                        update_task_progress(
                            db,
                            task,
                            f"时长验证未通过：{ratio:.1%}（允许±10%）",
                        )
                    else:
                        raise RuntimeError(
                            f"Duration Orchestrator failed: {'; '.join(errors)}"
                        )
                else:
                    ratio = result.get("statistics", {}).get("duration_ratio", 0)
                    update_task_progress(db, task, f"时长精控完成：{ratio:.1%}")
                return

            episode_duration_minutes = getattr(episode, "duration_minutes", None)
            fallback_target_seconds = None
            if episode_duration_minutes and len(scenes) > 0:
                fallback_target_seconds = (episode_duration_minutes * 60) // len(scenes)

            total = len(scenes)
            skipped = 0
            for idx, scene in enumerate(scenes, start=1):
                if not overwrite_audio and scene_has_dialogue_audio(scene, script_id):
                    beat_count = (
                        db.query(SceneBeat)
                        .filter(SceneBeat.scene_id == scene.id)
                        .count()
                    )
                    if beat_count > 0:
                        skipped += 1
                        update_task_progress(
                            db,
                            task,
                            f"生成对白音轨：{idx}/{total}（跳过 {skipped}） 场景 {scene.scene_number}",
                        )
                        continue

                update_task_progress(
                    db,
                    task,
                    f"生成对白音轨：{idx}/{total}（跳过 {skipped}） 场景 {scene.scene_number}",
                )

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
                    overwrite_beats=overwrite_beats,
                    timing_model=timing_model,
                    target_duration_seconds=scene_target,
                )

        run_async_task_sync(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:dialogue_audio"
            update_task_progress(db, task, "对白音轨生成完成")
    except Exception as exc:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            update_task_progress(db, task, f"对白音轨生成失败：{exc}")
    finally:
        db.close()


__all__ = [
    "router",
    "ScriptDialogueAudioGenerateRequest",
    "generate_script_dialogue_audio_async",
    "_process_script_dialogue_audio_task",
]
