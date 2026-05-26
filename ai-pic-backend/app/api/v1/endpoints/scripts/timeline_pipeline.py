from __future__ import annotations

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.repositories.audio_timeline_repository import count_scene_beats
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services import story_structure_service as story_structure_svc
from app.services.audio.episode_audio_builder import generate_episode_audio_timeline
from app.services.audio.scene_audio_generator import generate_scene_dialogue_audio
from app.services.duration_controlled_dialogue_service import (
    generate_dialogue_with_duration_control,
)
from app.services.script.task_titles import friendly_task_title
from app.services.script.timeline_shot_plan_step import (
    generate_timeline_shot_plan_from_current_version,
)
from app.services.script.timeline_storyboard_queue import (
    generate_storyboard_placeholders_and_queue_images,
)
from app.services.storyboard.storyboard_image_autogen import (
    storyboard_image_queue_progress_message,
)
from app.services.task_worker import timeline_pipeline_generate_task
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .audio_pipeline_utils import (
    episode_has_audio_timeline,
    load_script_with_access,
    run_async_task_sync,
    scene_has_dialogue_audio,
    scene_number_sort_key,
    update_task_progress,
)

router = APIRouter()


class TimelinePipelineGenerateRequest(BaseModel):
    tts_model: str | None = Field(None, description="TTS model (default speech-2.6-hd)")
    timing_model: str | None = Field(
        None,
        description="Timeline LLM model (uses system default when empty)",
    )
    overwrite_audio: bool = Field(False, description="Overwrite existing scene audio")
    overwrite_timeline: bool = Field(False, description="Overwrite existing timeline")
    overwrite_storyboard: bool = Field(
        False,
        description="Overwrite existing storyboard frame placeholders",
    )
    min_pause_seconds: float = Field(
        1.5,
        description="Minimum pause duration for storyboard placeholders",
    )
    use_duration_control: bool = Field(
        False,
        description="Enable Duration Orchestrator for tighter duration control",
    )


@router.post("/{script_id}/timeline-pipeline/generate-async")
async def generate_timeline_pipeline_async(
    script_id: int,
    body: TimelinePipelineGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Queue one-click timeline pipeline (dialogue audio -> timeline -> storyboard)."""
    script = load_script_with_access(db, script_id, current_user)
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None
    params = body.model_dump()
    params["script_id"] = script_id

    task = Task(
        title=friendly_task_title("一键时间轴流水线", script, episode, story),
        description="一键生成对白音轨、时间轴、分镜帧占位",
        task_type=TaskType.TIMELINE_PIPELINE,
        prompt=f"Timeline pipeline for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    timeline_pipeline_generate_task.delay(task.id, params, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_timeline_pipeline_task(task_id: int, payload: dict, user_id: int) -> None:
    """Celery worker handler for the timeline pipeline."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task_repo = TaskRepository(db)
        task = task_repo.get_by_id(task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_audio = bool(payload.get("overwrite_audio"))
        overwrite_timeline = bool(payload.get("overwrite_timeline"))
        overwrite_storyboard = bool(payload.get("overwrite_storyboard"))
        tts_model = payload.get("tts_model") or "speech-2.6-hd"
        timing_model = payload.get("timing_model")
        min_pause_seconds = float(payload.get("min_pause_seconds") or 1.5)
        min_pause_ms = max(0, int(round(min_pause_seconds * 1000)))
        use_duration_control = bool(payload.get("use_duration_control", False))

        async def _run() -> None:
            user = UserRepository(db).get_by_id(user_id)
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
            scenes = sorted(scenes, key=scene_number_sort_key)
            if not scenes:
                raise RuntimeError("no_scenes_found")

            if use_duration_control:
                update_task_progress(
                    db,
                    task,
                    f"步骤 1/4：时长精控模式 - 编排 {len(scenes)} 个场景…",
                )

                def _progress_cb(message: str) -> None:
                    update_task_progress(db, task, f"步骤 1/4：{message}")

                result = await generate_dialogue_with_duration_control(
                    db,
                    story=story,
                    episode=episode,
                    script=script,
                    scenes=scenes,
                    tts_model=str(tts_model),
                    overwrite_beats=True,
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
                            f"步骤 1/4：时长验证未通过 {ratio:.1%}（允许±10%）",
                        )
                    else:
                        raise RuntimeError(
                            f"Duration Orchestrator failed: {'; '.join(errors)}"
                        )
                else:
                    ratio = result.get("statistics", {}).get("duration_ratio", 0)
                    update_task_progress(
                        db, task, f"步骤 1/4：时长精控完成 {ratio:.1%}"
                    )
            else:
                update_task_progress(db, task, "步骤 1/4：生成对白音轨…")

                episode_duration_minutes = getattr(episode, "duration_minutes", None)
                fallback_target_seconds = None
                if episode_duration_minutes and len(scenes) > 0:
                    fallback_target_seconds = (episode_duration_minutes * 60) // len(
                        scenes
                    )

                total = len(scenes)
                skipped = 0
                for idx, scene in enumerate(scenes, start=1):
                    if not overwrite_audio and scene_has_dialogue_audio(
                        scene, script_id
                    ):
                        beat_count = count_scene_beats(db, int(scene.id))
                        if beat_count > 0:
                            skipped += 1
                            update_task_progress(
                                db,
                                task,
                                f"步骤 1/4：对白音轨 {idx}/{total}（跳过 {skipped}）",
                            )
                            continue

                    update_task_progress(
                        db,
                        task,
                        f"步骤 1/4：对白音轨 {idx}/{total}（跳过 {skipped}）",
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
                        overwrite_beats=True,
                        timing_model=timing_model,
                        target_duration_seconds=scene_target,
                    )

            update_task_progress(db, task, "步骤 2/4：生成时间轴…")
            audio_timeline_payload = None
            if not overwrite_timeline and episode_has_audio_timeline(
                episode, script_id
            ):
                update_task_progress(
                    db, task, "步骤 2/4：过渡时间轴已存在，导入 Timeline Spec…"
                )
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
                user_id=user.id,
            )
            update_task_progress(
                db, task, f"步骤 2/5：Timeline Spec v1 {import_result.action}"
            )

            update_task_progress(db, task, "步骤 3/5：生成 Timeline 镜头计划…")
            timeline = await generate_timeline_shot_plan_from_current_version(
                db,
                import_result.timeline,
                user_id=user.id,
            )

            update_task_progress(db, task, "步骤 4/5：生成分镜帧占位…")
            image_result = generate_storyboard_placeholders_and_queue_images(
                db,
                parent_task=task,
                script=script,
                episode=episode,
                timeline=timeline,
                user_id=user.id,
                overwrite_storyboard=overwrite_storyboard,
                min_pause_ms=min_pause_ms,
            )
            update_task_progress(
                db,
                task,
                storyboard_image_queue_progress_message(
                    image_result,
                    prefix="步骤 5/5",
                ),
            )

        run_async_task_sync(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:timeline_pipeline"
            update_task_progress(db, task, "一键时间轴流水线完成")
    except Exception as exc:
        task = TaskRepository(db).get_by_id(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            update_task_progress(db, task, f"流水线失败：{exc}")
    finally:
        db.close()
