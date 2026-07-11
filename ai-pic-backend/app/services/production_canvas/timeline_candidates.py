from __future__ import annotations

from typing import Any

from app.repositories.timeline_repository import TimelineClipAssetRepository
from app.schemas.production_canvas import ProductionCanvasSavedNode
from app.schemas.production_canvas_review import ProductionCanvasMediaCandidate
from sqlalchemy.orm import Session


def _string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _frame_clip_id(frame: dict[str, Any]) -> str | None:
    source = frame.get("source")
    return _string(frame.get("timeline_clip_id")) or _string(
        source.get("clip_id") if isinstance(source, dict) else None
    )


def list_timeline_video_candidates(
    db: Session,
    node: ProductionCanvasSavedNode,
    frames: list[dict[str, Any]],
    requested_indexes: set[int] | None,
    seen: set[tuple[int, int]],
) -> list[ProductionCanvasMediaCandidate]:
    timeline_id = node.outputs.get("timeline_id")
    timeline_version = node.outputs.get("timeline_version")
    if not isinstance(timeline_id, int) or not isinstance(timeline_version, int):
        return []

    frame_by_clip = {
        clip_id: (index, frame)
        for index, frame in enumerate(frames)
        if (requested_indexes is None or index in requested_indexes)
        and (clip_id := _frame_clip_id(frame))
    }
    if not frame_by_clip:
        return []

    candidates: list[ProductionCanvasMediaCandidate] = []
    links = TimelineClipAssetRepository(db).list_for_timeline(
        timeline_id=timeline_id,
        timeline_version=timeline_version,
    )
    for link in links:
        if link.asset_role != "generated_video" or link.clip_id not in frame_by_clip:
            continue
        asset = link.media_asset
        url = _string(asset.file_url if asset else None)
        if asset is None or not url:
            continue
        frame_index, frame = frame_by_clip[link.clip_id]
        key = (asset.id, frame_index)
        if key in seen:
            continue
        seen.add(key)
        metadata = (
            asset.extra_metadata if isinstance(asset.extra_metadata, dict) else {}
        )
        candidates.append(
            ProductionCanvasMediaCandidate(
                asset_id=asset.id,
                asset_business_id=asset.business_id,
                media_type="video",
                url=url,
                frame_index=frame_index,
                clip_id=link.clip_id,
                prompt=_string(metadata.get("prompt")),
                model=_string(metadata.get("model")),
                duration_seconds=(
                    asset.duration_ms / 1000 if asset.duration_ms else None
                ),
                selected=asset.id == node.selected_output_id,
            )
        )
    return candidates
