"""
Episode async generation endpoints and background task exports.
"""

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.episode.episode_generation_service import EpisodeGenerationService
from app.services.episode.novel_workflow_guard import (
    ensure_direct_episode_generation_allowed,
)
from app.services.task_worker import episode_generate_task
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/generate-async")
async def generate_episodes_async(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate episodes asynchronously via Celery worker."""
    story = EpisodeGenerationService(db, current_user)._get_story(request.story_id)
    ensure_direct_episode_generation_allowed(story)
    payload = request.model_dump()
    payload["generation_mode"] = "production"
    payload["production_mode"] = True
    task = Task(
        title=f"生成剧集 - 故事{request.story_id}",
        description="异步剧集生成",
        task_type=TaskType.EPISODE_GENERATION,
        prompt=f"Episode plan for story {request.story_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    episode_generate_task.delay(task.id, payload, current_user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
