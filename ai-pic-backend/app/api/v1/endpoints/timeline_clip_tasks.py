from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.timeline_clip_tasks import TimelineClipTaskListResponse
from app.services.timeline_clip_task_status_service import (
    TimelineClipTaskStatusService,
)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/timelines/{timeline_id}/clip-tasks",
    response_model=TimelineClipTaskListResponse,
    summary="List the caller's in-flight generation tasks for one timeline",
)
def list_timeline_clip_tasks(
    timeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineClipTaskListResponse:
    service = TimelineClipTaskStatusService(db)
    return service.list_active_clip_tasks(timeline_id, current_user)
