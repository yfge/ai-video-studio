"""Response mappers for Timeline API services."""

from app.models.timeline import MediaAsset, RenderJob, Timeline, TimelineClipAsset
from app.schemas.timeline import (
    MediaAssetResponse,
    RenderJobResponse,
    TimelineClipAssetResponse,
    TimelineResponse,
)


def timeline_response(timeline: Timeline) -> TimelineResponse:
    rollback = None
    if (
        timeline.rollback_of_version is not None
        and timeline.rollback_target_version is not None
        and timeline.rolled_back_at is not None
    ):
        rollback = {
            "source_version": timeline.rollback_of_version,
            "target_version": timeline.rollback_target_version,
            "rolled_back_at": timeline.rolled_back_at,
            "rolled_back_by": timeline.rolled_back_by,
        }
    return TimelineResponse(
        id=timeline.id,
        business_id=timeline.business_id,
        episode_id=timeline.episode_id,
        episode_business_id=timeline.episode_business_id,
        script_id=timeline.script_id,
        script_business_id=timeline.script_business_id,
        title=timeline.title,
        status=timeline.status,
        spec=timeline.spec or {},
        version=timeline.version,
        source_audio_timeline_version=timeline.source_audio_timeline_version,
        rollback=rollback,
        is_deleted=bool(timeline.is_deleted),
        deleted_at=timeline.deleted_at,
        deleted_by=timeline.deleted_by,
        deleted_reason=timeline.deleted_reason,
        created_by=timeline.created_by,
        updated_by=timeline.updated_by,
        created_at=timeline.created_at,
        updated_at=timeline.updated_at,
    )


def render_job_response(job: RenderJob) -> RenderJobResponse:
    return RenderJobResponse(
        id=job.id,
        business_id=job.business_id,
        timeline_id=job.timeline_id,
        timeline_version=job.timeline_version,
        render_type=job.render_type,
        preset_hash=job.preset_hash,
        preset=job.preset or {},
        status=job.status,
        progress=job.progress,
        output_asset_id=job.output_asset_id,
        output_asset=(
            media_asset_response(job.output_asset)
            if job.output_asset is not None
            else None
        ),
        log=job.log,
        is_deleted=bool(job.is_deleted),
        deleted_at=job.deleted_at,
        deleted_by=job.deleted_by,
        deleted_reason=job.deleted_reason,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def media_asset_response(asset: MediaAsset) -> MediaAssetResponse:
    return MediaAssetResponse(
        id=asset.id,
        business_id=asset.business_id,
        asset_type=asset.asset_type,
        origin=asset.origin,
        file_url=asset.file_url,
        object_key=asset.object_key,
        file_path=asset.file_path,
        mime_type=asset.mime_type,
        hash=asset.hash,
        duration_ms=asset.duration_ms,
        width=asset.width,
        height=asset.height,
        metadata=asset.extra_metadata,
        created_by=asset.created_by,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def timeline_clip_asset_response(link: TimelineClipAsset) -> TimelineClipAssetResponse:
    return TimelineClipAssetResponse(
        id=link.id,
        business_id=link.business_id,
        timeline_id=link.timeline_id,
        timeline_version=link.timeline_version,
        clip_id=link.clip_id,
        track_type=link.track_type,
        asset_role=link.asset_role,
        media_asset_id=link.media_asset_id,
        media_asset=(
            media_asset_response(link.media_asset)
            if link.media_asset is not None
            else None
        ),
        render_job_id=link.render_job_id,
        source=link.source,
        source_ref=link.source_ref,
        replacement_of_id=link.replacement_of_id,
        is_deleted=bool(link.is_deleted),
        deleted_at=link.deleted_at,
        deleted_by=link.deleted_by,
        deleted_reason=link.deleted_reason,
        created_by=link.created_by,
        created_at=link.created_at,
    )
