from __future__ import annotations

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.generation_requests import StoryGenerationRequest
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    attach_quality_gate_failure_to_task,
)
from app.services.story.story_generation_service import StoryGenerationService
from app.services.task_worker import story_generate_task
from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


def _story_generation_error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        return json.dumps(detail, ensure_ascii=False)
    error_message = str(exc)
    return error_message or repr(exc)


def _process_story_generation_task(task_id: int, request_dict: dict, user_id: int):
    """后台处理故事生成任务（供 Celery worker 调用）。"""
    from app.core.database import get_task_db

    with get_task_db() as db:
        task_repo = TaskRepository(db)
        try:
            task = task_repo.get_by_id(task_id)
            if task:
                task.status = TaskStatus.PROCESSING
                db.commit()

            import anyio

            async def _run():
                service = StoryGenerationService(db)
                return await service.generate_story_from_payload(request_dict, user_id)

            story = anyio.run(_run)

            task = task_repo.get_by_id(task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.result_file_path = f"story:{story.id}"
                db.commit()
        except Exception as exc:
            task = task_repo.get_by_id(task_id)
            if task:
                if isinstance(exc, NarrativeQualityGateError):
                    attach_quality_gate_failure_to_task(task, exc.quality_gate)
                task.status = TaskStatus.FAILED
                task.error_message = _story_generation_error_message(exc)
                db.commit()


@router.post("/generate-async")
async def generate_story_async(
    request: StoryGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成故事：创建任务并在后台生成"""
    payload = request.model_dump()
    payload["generation_mode"] = "production"
    payload["production_mode"] = True
    task = Task(
        title=f"生成故事 - {request.title}",
        description="异步故事生成",
        task_type=TaskType.STORY_GENERATION,
        prompt=f"Story outline: {request.title}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 后台处理：交给 Celery worker，而非本进程 BackgroundTasks
    story_generate_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
