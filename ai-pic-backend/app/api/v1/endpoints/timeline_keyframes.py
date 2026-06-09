from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.timeline_clip_keyframes import (
    TimelineClipKeyframeGenerateRequest,
    TimelineClipKeyframeGenerateResponse,
)
from app.services.timeline_clip_keyframe_service import TimelineClipKeyframeService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/timelines/{timeline_id}/clips/{clip_id}/keyframes/generate",
    response_model=TimelineClipKeyframeGenerateResponse,
    summary="Queue start/end keyframe generation for one Timeline video clip",
)
def queue_timeline_clip_keyframes(
    timeline_id: int,
    clip_id: str,
    payload: TimelineClipKeyframeGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineClipKeyframeGenerateResponse:
    service = TimelineClipKeyframeService(db)
    return service.queue_keyframes(timeline_id, clip_id, payload, current_user)
