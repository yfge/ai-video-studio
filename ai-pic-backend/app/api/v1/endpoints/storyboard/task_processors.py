"""Storyboard task processors for Celery workers.

Provides synchronous entry points for storyboard generation and video
generation background tasks.
"""

from typing import Any


def _process_storyboard_generation_task(
    task_id: int,
    payload: dict,
    user_id: int,
):
    """Process storyboard structure generation task (called by Celery)."""
    import anyio
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))

        async def _run():
            from app.models.script import Script

            from .legacy_generate import generate_storyboard_logic

            script = db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise RuntimeError(f"Script {script_id} not found")

            model = payload.get("model")
            temperature = float(payload.get("temperature") or 0.7)
            frames_per_scene = int(payload.get("frames_per_scene") or 7)
            max_frames = payload.get("max_frames")
            max_frames_arg = int(max_frames) if max_frames is not None else None
            scene_numbers = payload.get("scene_numbers")
            use_plan = bool(payload.get("use_plan"))

            selected_scenes = None
            if scene_numbers:
                try:
                    selected_scenes = [
                        int(x.strip()) for x in scene_numbers.split(",") if x.strip()
                    ]
                except Exception:
                    pass

            await generate_storyboard_logic(
                script,
                db,
                model=model,
                temperature=temperature,
                frames_per_scene=frames_per_scene,
                max_frames=max_frames_arg,
                selected_scenes=selected_scenes,
                use_plan=use_plan,
            )

        anyio.run(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:storyboard"
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


def _process_storyboard_video_task(
    task_id: int,
    script_id: int,
    frame_indexes: list[int] | None,
    selections: list[dict[str, Any]] | None = None,
    options: dict[str, Any] | None = None,
):
    """Process storyboard video generation task (called by Celery)."""
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    from app.services.video.video_task_entrypoints import submit_storyboard_video_tasks

    try:
        submit_storyboard_video_tasks(
            task_id=task_id,
            script_id=script_id,
            frame_indexes=frame_indexes,
            selections=selections,
            options=options,
        )
    except Exception as e:
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                db.commit()
        finally:
            db.close()
        raise
