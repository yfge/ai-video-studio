from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.timeline import (
    RenderJobCreate,
    RenderJobListResponse,
    RenderJobResponse,
    TimelineClipAssetListResponse,
    TimelineClipAssetResponse,
    TimelineClipReworkRequest,
    TimelineClipVideoReworkTaskRequest,
    TimelineClipVideoReworkTaskResponse,
    TimelineCreate,
    TimelineDeleteRequest,
    TimelineListResponse,
    TimelineResponse,
    TimelineRollbackRequest,
    TimelineShotPlanRequest,
    TimelineStoryboardGridGenerateRequest,
    TimelineStoryboardGridGenerateResponse,
    TimelineUpdate,
    TimelineVersionRequest,
)
from app.services.storyboard.grid_storyboard_sheet_service import (
    GridStoryboardSheetService,
)
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from app.services.timeline_clip_rework_service import TimelineClipReworkService
from app.services.timeline_clip_video_rework_queue_service import (
    TimelineClipVideoReworkQueueService,
)
from app.services.timeline_lifecycle_service import TimelineLifecycleService
from app.services.timeline_service import TimelineService
from app.services.timeline_shot_plan_service import TimelineShotPlanService
from fastapi import APIRouter, Depends, Query
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
    "/timelines/{timeline_id}/shot-plan",
    response_model=TimelineResponse,
    summary="Generate Timeline-native shot plans for video clips",
)
async def generate_timeline_shot_plan(
    timeline_id: int,
    payload: TimelineShotPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineShotPlanService(db)
    return await service.generate_shot_plan(timeline_id, payload, current_user)


@router.post(
    "/timelines/{timeline_id}/storyboard-grid/generate",
    response_model=TimelineStoryboardGridGenerateResponse,
    summary="Queue grid storyboard sheet generation from Timeline clips",
)
def queue_timeline_storyboard_grid(
    timeline_id: int,
    payload: TimelineStoryboardGridGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineStoryboardGridGenerateResponse:
    service = GridStoryboardSheetService(db)
    return service.queue_grid_sheet(timeline_id, payload, current_user)


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
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RenderJobListResponse:
    service = TimelineService(db)
    return RenderJobListResponse(
        items=service.list_render_jobs(
            timeline_id,
            current_user,
            include_deleted=include_deleted,
        )
    )


@router.get(
    "/timelines/{timeline_id}/clip-assets",
    response_model=TimelineClipAssetListResponse,
    summary="List timeline clip asset lineage",
)
def list_timeline_clip_assets(
    timeline_id: int,
    timeline_version: int | None = Query(None),
    clip_id: str | None = Query(None),
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineClipAssetListResponse:
    service = TimelineClipAssetLineageService(db)
    return TimelineClipAssetListResponse(
        items=service.list_clip_assets(
            timeline_id,
            current_user,
            timeline_version=timeline_version,
            clip_id=clip_id,
            include_deleted=include_deleted,
        )
    )


@router.post(
    "/timelines/{timeline_id}/clips/{clip_id}/rework",
    response_model=TimelineClipAssetResponse,
    summary="Record a clip rework asset without changing the stable clip id",
)
def rework_timeline_clip(
    timeline_id: int,
    clip_id: str,
    payload: TimelineClipReworkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineClipAssetResponse:
    service = TimelineClipReworkService(db)
    return service.rework_clip(timeline_id, clip_id, payload, current_user)


@router.post(
    "/timelines/{timeline_id}/clips/{clip_id}/rework/video",
    response_model=TimelineClipVideoReworkTaskResponse,
    summary="Queue provider-backed video rework for a timeline clip",
)
def queue_timeline_clip_video_rework(
    timeline_id: int,
    clip_id: str,
    payload: TimelineClipVideoReworkTaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineClipVideoReworkTaskResponse:
    service = TimelineClipVideoReworkQueueService(db)
    return service.queue_video_rework(timeline_id, clip_id, payload, current_user)


@router.delete(
    "/timelines/{timeline_id}",
    response_model=TimelineResponse,
    summary="Soft delete a timeline with version lock",
)
def delete_timeline(
    timeline_id: int,
    payload: TimelineDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineLifecycleService(db)
    return service.delete_timeline(timeline_id, payload, current_user)


@router.post(
    "/timelines/{timeline_id}/restore",
    response_model=TimelineResponse,
    summary="Restore a soft-deleted timeline with version lock",
)
def restore_timeline(
    timeline_id: int,
    payload: TimelineVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineLifecycleService(db)
    return service.restore_timeline(timeline_id, payload, current_user)


@router.post(
    "/timelines/{timeline_id}/rollback",
    response_model=TimelineResponse,
    summary="Rollback a timeline to a prior version snapshot",
)
def rollback_timeline(
    timeline_id: int,
    payload: TimelineRollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimelineResponse:
    service = TimelineLifecycleService(db)
    return service.rollback_timeline(timeline_id, payload, current_user)


@router.delete(
    "/timelines/{timeline_id}/render-jobs/{render_job_id}",
    response_model=RenderJobResponse,
    summary="Soft delete a render attempt with timeline version lock",
)
def delete_timeline_render_job(
    timeline_id: int,
    render_job_id: int,
    payload: TimelineDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RenderJobResponse:
    service = TimelineLifecycleService(db)
    return service.delete_render_job(timeline_id, render_job_id, payload, current_user)


@router.post(
    "/timelines/{timeline_id}/render-jobs/{render_job_id}/restore",
    response_model=RenderJobResponse,
    summary="Restore a soft-deleted render attempt with timeline version lock",
)
def restore_timeline_render_job(
    timeline_id: int,
    render_job_id: int,
    payload: TimelineVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RenderJobResponse:
    service = TimelineLifecycleService(db)
    return service.restore_render_job(timeline_id, render_job_id, payload, current_user)
