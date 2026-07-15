"""Reuse a provider-approved 3D sheet as a privacy-safe visual anchor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineClipAssetRepository,
)
from sqlalchemy.orm import Session

from .clip_storyboard_context import ClipStoryboardContext


@dataclass(frozen=True, slots=True)
class ApprovedStyleAnchor:
    media_asset_id: int
    url: str
    character_names: frozenset[str]


def apply_approved_3d_style_anchor(
    db: Session,
    *,
    timeline_id: int,
    style: str | None,
    context: ClipStoryboardContext,
) -> ClipStoryboardContext:
    if str(style or "").strip().lower() != "3d_cartoon":
        return context
    current_names = _character_names(context.bound_context)
    if not current_names:
        return context
    anchor = _find_anchor(db, timeline_id=timeline_id, current_names=current_names)
    if anchor is None:
        return context
    bound_context = {
        **context.bound_context,
        "reference_bindings": [
            {
                "index": 1,
                "role": "style_reference",
                "label": (
                    "provider-approved unmistakably non-photorealistic 3D style "
                    "and identity anchor; match this rendering exactly"
                ),
                "source": "provider_approved_storyboard_sheet",
                "url": anchor.url,
            }
        ],
        "approved_style_anchor": {
            "media_asset_id": anchor.media_asset_id,
            "character_names": sorted(anchor.character_names),
        },
    }
    return ClipStoryboardContext(
        bound_context=bound_context,
        reference_images=[anchor.url],
        panels=[{**panel, "bound_context": bound_context} for panel in context.panels],
    )


def _find_anchor(
    db: Session,
    *,
    timeline_id: int,
    current_names: frozenset[str],
) -> ApprovedStyleAnchor | None:
    media_assets = MediaAssetRepository(db)
    tasks = TaskRepository(db)
    subset_match: ApprovedStyleAnchor | None = None
    links = TimelineClipAssetRepository(db).list_for_timeline(timeline_id=timeline_id)
    for link in links:
        if link.asset_role != "generated_video":
            continue
        sheet_id = _sheet_asset_id(link.source_ref)
        if not sheet_id:
            continue
        asset = media_assets.get_by_id(sheet_id)
        if asset is None or asset.is_deleted or not (asset.file_url or asset.file_path):
            continue
        task = tasks.get_by_id(_metadata_task_id(asset.extra_metadata))
        params = _task_parameters(task)
        if str(params.get("style") or "").strip().lower() != "3d_cartoon":
            continue
        anchor_names = _character_names(params.get("bound_context"))
        if not anchor_names or not current_names.issubset(anchor_names):
            continue
        anchor = ApprovedStyleAnchor(
            media_asset_id=asset.id,
            url=asset.file_url or asset.file_path,
            character_names=anchor_names,
        )
        if current_names == anchor_names:
            return anchor
        subset_match = subset_match or anchor
    return subset_match


def _sheet_asset_id(source_ref: Any) -> int | None:
    if not isinstance(source_ref, dict):
        return None
    if source_ref.get("reference_mode") != "clip_storyboard_sheet":
        return None
    storyboard = source_ref.get("clip_storyboard")
    return (
        _positive_int(storyboard.get("sheet_media_asset_id"))
        if isinstance(storyboard, dict)
        else None
    )


def _metadata_task_id(metadata: Any) -> int | None:
    return (
        _positive_int(metadata.get("task_id")) if isinstance(metadata, dict) else None
    )


def _task_parameters(task: Any) -> dict[str, Any]:
    if task is None or not isinstance(task.parameters, str):
        return {}
    try:
        value = json.loads(task.parameters)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _character_names(context: Any) -> frozenset[str]:
    if not isinstance(context, dict) or not isinstance(context.get("characters"), list):
        return frozenset()
    return frozenset(
        str(item.get("name")).strip()
        for item in context["characters"]
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    )


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None
