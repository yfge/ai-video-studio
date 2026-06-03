"""Timeline Spec mutation helpers for grid storyboard sheets."""

from __future__ import annotations

import copy
from typing import Any

from app.models.timeline import MediaAsset


def apply_grid_storyboard_sheet_to_spec(
    spec: dict[str, Any],
    *,
    panels: list[dict[str, Any]],
    sheet_media_asset: MediaAsset,
    panel_count: int,
    columns: int,
    rows: int,
    prompt_sha256: str,
    source_timeline_version: int,
    generated_at: str,
) -> dict[str, Any]:
    updated = copy.deepcopy(spec)
    sheet_file_url = sheet_media_asset.file_url or sheet_media_asset.file_path
    normalized_panels = [
        _panel_with_sheet_ref(panel, sheet_media_asset.id, source_timeline_version)
        for panel in panels
        if isinstance(panel, dict)
    ]
    support_views = updated.setdefault("support_views", {})
    support_views["storyboard_grid"] = {
        "mode": "grid_storyboard.v1",
        "sheet": {
            "media_asset_id": sheet_media_asset.id,
            "file_url": sheet_file_url,
            "file_path": sheet_media_asset.file_path,
            "asset_role": "storyboard_grid_sheet",
            "panel_count": panel_count,
            "columns": columns,
            "rows": rows,
            "prompt_sha256": prompt_sha256,
        },
        "panels": normalized_panels,
        "generated_at": generated_at,
        "source": "timeline_spec",
        "source_timeline_version": source_timeline_version,
    }
    _attach_grid_refs_to_clips(
        updated,
        normalized_panels,
        sheet_media_asset=sheet_media_asset,
        source_timeline_version=source_timeline_version,
    )
    return updated


def _attach_grid_refs_to_clips(
    spec: dict[str, Any],
    panels: list[dict[str, Any]],
    *,
    sheet_media_asset: MediaAsset,
    source_timeline_version: int,
) -> None:
    sheet_file_url = sheet_media_asset.file_url or sheet_media_asset.file_path
    panels_by_clip_id = {
        panel.get("clip_id"): panel for panel in panels if panel.get("clip_id")
    }
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = track.get("track_type") or track.get("type")
        if track_type != "video":
            continue
        for clip in track.get("clips") or []:
            if not isinstance(clip, dict):
                continue
            panel = panels_by_clip_id.get(clip.get("clip_id") or clip.get("id"))
            if not panel:
                continue
            refs = clip.setdefault("source_refs", {})
            refs["grid_storyboard_panel"] = {
                "panel_id": panel.get("panel_id"),
                "panel_index": panel.get("panel_index"),
                "sheet_media_asset_id": sheet_media_asset.id,
                "source_timeline_version": source_timeline_version,
            }
            clip["storyboard_grid_sheet_asset_ref"] = {
                "kind": "storyboard_grid_sheet",
                "role": "storyboard_grid_sheet",
                "media_asset_id": sheet_media_asset.id,
                "file_url": sheet_file_url,
                "file_path": sheet_media_asset.file_path,
                "panel_id": panel.get("panel_id"),
                "panel_index": panel.get("panel_index"),
            }


def _panel_with_sheet_ref(
    panel: dict[str, Any],
    sheet_media_asset_id: int,
    source_timeline_version: int,
) -> dict[str, Any]:
    normalized = dict(panel)
    panel_index = _maybe_int(normalized.get("panel_index")) or 0
    normalized.setdefault("panel_id", f"grid_panel_{panel_index:03d}")
    normalized["sheet_media_asset_id"] = sheet_media_asset_id
    normalized["source_timeline_version"] = source_timeline_version
    return normalized


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
