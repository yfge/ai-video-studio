"""Persist generated grid-storyboard sheets as Timeline media assets."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.models.timeline import MediaAsset
from app.repositories.timeline_repository import MediaAssetRepository

from .grid_storyboard_sheet_payload import sheet_metadata, string_value

ImagePersister = Callable[..., Awaitable[dict[str, Any]]]


async def persist_grid_storyboard_sheet_asset(
    *,
    media_assets: MediaAssetRepository,
    image_persister: ImagePersister,
    source_url: str,
    result: dict[str, Any],
    payload: dict[str, Any],
    task_id: int,
    timeline_id: int,
    timeline_version: int,
    user_id: int | None,
) -> MediaAsset:
    clip_sheet = payload.get("kind") == "timeline_clip_storyboard"
    stored = await image_persister(
        image_data=source_url,
        ip_name=f"timeline-{timeline_id}",
        category="clip-storyboard" if clip_sheet else "storyboard-grid",
        prefix=(
            "ai-generated/clip-storyboard"
            if clip_sheet
            else "ai-generated/storyboard-grid"
        ),
        metadata={
            "task_id": task_id,
            "timeline_id": timeline_id,
            "timeline_version": timeline_version,
            "clip_id": payload.get("clip_id"),
            "kind": payload.get("kind") or "timeline_storyboard_grid",
        },
        require_upload=False,
    )
    file_url = string_value(stored.get("oss_url")) or source_url
    file_path = string_value(stored.get("relative_path")) or string_value(
        stored.get("local_file_path")
    )
    existing = media_assets.find_by_location(
        asset_type="image",
        file_url=file_url,
        file_path=file_path,
    )
    if existing is not None:
        return existing
    asset = media_assets.create(
        asset_type="image",
        origin="generated",
        file_url=file_url,
        file_path=file_path,
        mime_type="image/png",
        extra_metadata=sheet_metadata(result, payload, task_id),
        created_by=user_id,
    )
    media_assets.session.flush()
    return asset
