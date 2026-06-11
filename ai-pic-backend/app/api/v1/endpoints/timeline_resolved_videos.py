from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.timeline_resolved_videos import TimelineResolvedVideoListResponse
from app.services.timeline_resolved_video_service import TimelineResolvedVideoService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/timelines/{timeline_id}/resolved-videos",
    response_model=TimelineResolvedVideoListResponse,
    summary="Resolve playable video sources for one Timeline",
)
def list_timeline_resolved_videos(
    timeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResolvedVideoListResponse:
    service = TimelineResolvedVideoService(db)
    return service.list_resolved_videos(timeline_id, current_user)
