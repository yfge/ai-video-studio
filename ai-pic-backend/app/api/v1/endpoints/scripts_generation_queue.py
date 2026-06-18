"""Script generation task queue endpoints."""

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.services.script.generation_queue import queue_script_generation_task
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/generate-async")
async def generate_script_async(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    task = queue_script_generation_task(db, current_user, request)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
