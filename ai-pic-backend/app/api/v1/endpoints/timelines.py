from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.timeline import (
    RenderJobCreate,
    RenderJobListResponse,
    RenderJobResponse,
    TimelineCreate,
    TimelineListResponse,
    TimelineResponse,
    TimelineUpdate,
)
from app.services.timeline_service import TimelineService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/episodes/{episode_id}/timelines",
    response_model=TimelineListResponse,
    summary="List episode timelines",
)
def list_episode_timelines(
    episode_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineListResponse:
    service = TimelineService(db)
    return TimelineListResponse(items=service.list_timelines(episode_id, current_user))


@router.post(
    "/episodes/{episode_id}/timelines",
    response_model=TimelineResponse,
    summary="Create an episode timeline",
)
def create_episode_timeline(
    episode_id: int,
    payload: TimelineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineService(db)
    return service.create_timeline(episode_id, payload, current_user)


@router.get(
    "/timelines/{timeline_id}",
    response_model=TimelineResponse,
    summary="Read a timeline",
)
def get_timeline(
    timeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineService(db)
    return service.get_timeline(timeline_id, current_user)


@router.patch(
    "/timelines/{timeline_id}",
    response_model=TimelineResponse,
    summary="Update a timeline with version lock",
)
def update_timeline(
    timeline_id: int,
    payload: TimelineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineService(db)
    return service.update_timeline(timeline_id, payload, current_user)


@router.post(
    "/timelines/{timeline_id}/render",
    response_model=RenderJobResponse,
    summary="Queue an idempotent render job",
)
def queue_timeline_render(
    timeline_id: int,
    payload: RenderJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RenderJobResponse:
    service = TimelineService(db)
    return service.queue_render_job(timeline_id, payload, current_user)


@router.get(
    "/timelines/{timeline_id}/render-jobs",
    response_model=RenderJobListResponse,
    summary="List timeline render jobs",
)
def list_timeline_render_jobs(
    timeline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RenderJobListResponse:
    service = TimelineService(db)
    return RenderJobListResponse(
        items=service.list_render_jobs(timeline_id, current_user)
    )
