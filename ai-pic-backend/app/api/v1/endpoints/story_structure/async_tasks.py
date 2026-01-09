"""
Story Structure background task processors.

Celery worker functions for async environment image generation.
"""

from __future__ import annotations

from typing import Any, Dict

from app.models.task import Task, TaskStatus
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.story_structure.environment_image_generation import (
    generate_environment_image_variants,
    generate_environment_images,
)
from app.services.story_structure.environment_image_requests import (
    resolve_environment_image_variant_request,
    resolve_environment_text_to_image_request,
)


def process_environment_image_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for environment text-to-image generation."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        env = svc.resolve_environment(db, payload["env_id"])
        if not env:
            raise RuntimeError("environment not found")

        import anyio

        async def _run() -> list[str]:
            req = resolve_environment_text_to_image_request(
                payload,
                prompt=payload.get("extra_prompt") or payload.get("prompt"),
                model=payload.get("model"),
                count=payload.get("count"),
                size=payload.get("size"),
                aspect_ratio=payload.get("aspect_ratio"),
            )
            return await generate_environment_images(
                db=db,
                env=env,
                request=req,
                ai_service=ai_service,
                require_upload=bool(oss_service),
            )

        saved = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"environment_images:{payload['env_id']}:{len(saved)}"
            )
            db.commit()
    except Exception as exc:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


def process_environment_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker function for environment image-to-image generation."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        env = svc.resolve_environment(db, payload["env_id"])
        if not env:
            raise RuntimeError("environment not found")

        import anyio

        async def _run() -> list[str]:
            base_fallback = env.reference_images[0] if env.reference_images else None
            req = resolve_environment_image_variant_request(
                payload,
                base_image=payload.get("base_image"),
                fallback_base_image=base_fallback,
                prompt=payload.get("prompt"),
                model=payload.get("model"),
                count=payload.get("count"),
                size=payload.get("size"),
                aspect_ratio=payload.get("aspect_ratio"),
            )
            return await generate_environment_image_variants(
                db=db,
                env=env,
                request=req,
                ai_service=ai_service,
                require_upload=bool(oss_service),
            )

        saved = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"environment_image_variants:{payload['env_id']}:{len(saved)}"
            )
            db.commit()
    except Exception as exc:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()
