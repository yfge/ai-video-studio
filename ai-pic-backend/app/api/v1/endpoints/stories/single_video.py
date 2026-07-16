from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.single_video_project import (
    SingleVideoProjectRequest,
    SingleVideoProjectResponse,
)
from app.services.single_video_project_service import create_single_video_project
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/single-video",
    response_model=SingleVideoProjectResponse,
    status_code=201,
)
async def create_single_video(
    request: SingleVideoProjectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return create_single_video_project(db, current_user, request)
