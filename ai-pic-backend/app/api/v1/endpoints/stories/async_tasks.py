from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.generation_requests import StoryGenerationRequest
from app.services.story.story_generation_service import StoryGenerationService
from app.services.task_worker import story_generate_task

router = APIRouter()


def _process_story_generation_task(task_id: int, request_dict: dict, user_id: int):
    """后台处理故事生成任务（同步函数供BackgroundTasks调用）"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        import anyio

        async def _run():
            service = StoryGenerationService(db)
            return await service.generate_story_from_payload(request_dict, user_id)

        story = anyio.run(_run)

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"story:{story.id}"
            db.commit()
    except Exception as exc:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.post("/generate-async")
async def generate_story_async(
    request: StoryGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成故事：创建任务并在后台生成"""
    task = Task(
        title=f"生成故事 - {request.title}",
        description="异步故事生成",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=f"Story outline: {request.title}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 后台处理：交给 Celery worker，而非本进程 BackgroundTasks
    story_generate_task.delay(task.id, request.dict(), current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
