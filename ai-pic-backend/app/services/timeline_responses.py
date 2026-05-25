"""Response mappers for Timeline API services."""

from app.models.timeline import MediaAsset, RenderJob, Timeline
from app.schemas.timeline import MediaAssetResponse, RenderJobResponse, TimelineResponse


def timeline_response(timeline: Timeline) -> TimelineResponse:
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
