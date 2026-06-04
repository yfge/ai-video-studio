"""Grid-storyboard reference payloads for Timeline clip video rework."""

from __future__ import annotations

from typing import Any, Callable

from app.models.timeline import Timeline
from app.schemas.timeline import TimelineClipVideoReworkTaskRequest
from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_clip_storyboard_video_prompt,
    build_grid_storyboard_video_prompt,
)
from fastapi import HTTPException, status


def build_grid_storyboard_rework_payload(
    timeline: Timeline,
    clip_id: str,
    clip: dict[str, Any],
    payload: TimelineClipVideoReworkTaskRequest,
    *,
    asset_ref_url: Callable[[Any], str | None],
    fallback_prompt: Callable[[dict[str, Any], str | None], str | None],
) -> dict[str, Any]:
    panel_ref, sheet_ref = _grid_refs_or_400(clip)
    sheet_url = asset_ref_url(sheet_ref)
    if not sheet_url:
        _raise_missing_grid_panel()

    panel = _support_view_panel(timeline, clip_id, panel_ref)
    video_prompt = (
        _string_value(payload.prompt)
        or _string_value(panel.get("video_prompt"))
        or fallback_prompt(clip, None)
        or ""
    )
    prompt_panel = {
        **panel,
        "panel_id": panel.get("panel_id") or panel_ref.get("panel_id"),
        "panel_index": panel.get("panel_index") or panel_ref.get("panel_index"),
        "clip_id": panel.get("clip_id") or clip_id,
        "video_prompt": video_prompt,
    }
    return {
        "prompt": build_grid_storyboard_video_prompt(prompt_panel),
        "reference_images": _dedupe_strings(
            [sheet_url] + list(payload.reference_images or [])
        ),
        "storyboard_grid": {
            "panel_id": prompt_panel.get("panel_id"),
            "panel_index": prompt_panel.get("panel_index"),
            "sheet_media_asset_id": (
                panel_ref.get("sheet_media_asset_id")
                or sheet_ref.get("media_asset_id")
            ),
            "source_timeline_version": panel_ref.get("source_timeline_version"),
        },
    }


def build_clip_storyboard_rework_payload(
    timeline: Timeline,
    clip_id: str,
    clip: dict[str, Any],
    payload: TimelineClipVideoReworkTaskRequest,
    *,
    asset_ref_url: Callable[[Any], str | None],
    fallback_prompt: Callable[[dict[str, Any], str | None], str | None],
) -> dict[str, Any]:
    storyboard_ref, sheet_ref = _clip_storyboard_refs_or_400(clip)
    sheet_url = asset_ref_url(sheet_ref)
    if not sheet_url:
        _raise_missing_clip_storyboard_panel()

    panel = _clip_storyboard_support_view_panel(timeline, clip_id, storyboard_ref)
    video_prompt = (
        _string_value(payload.prompt)
        or _string_value(panel.get("video_prompt"))
        or fallback_prompt(clip, None)
        or ""
    )
    prompt_panel = {
        **panel,
        "panel_id": panel.get("panel_id") or storyboard_ref.get("panel_id"),
        "panel_index": panel.get("panel_index") or storyboard_ref.get("panel_index"),
        "clip_id": panel.get("clip_id") or clip_id,
        "video_prompt": video_prompt,
    }
    return {
        "prompt": build_clip_storyboard_video_prompt(prompt_panel),
        "reference_images": _dedupe_strings(
            [sheet_url] + list(payload.reference_images or [])
        ),
        "clip_storyboard": {
            "panel_id": prompt_panel.get("panel_id"),
            "panel_index": prompt_panel.get("panel_index"),
            "sheet_media_asset_id": (
                storyboard_ref.get("sheet_media_asset_id")
                or sheet_ref.get("media_asset_id")
            ),
            "source_timeline_version": storyboard_ref.get("source_timeline_version"),
        },
    }


def _grid_refs_or_400(
    clip: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_refs = clip.get("source_refs")
    panel_ref = (
        source_refs.get("grid_storyboard_panel")
        if isinstance(source_refs, dict)
        else None
    )
    sheet_ref = clip.get("storyboard_grid_sheet_asset_ref")
    if not isinstance(panel_ref, dict) or not isinstance(sheet_ref, dict):
        _raise_missing_grid_panel()
    return panel_ref, sheet_ref


def _clip_storyboard_refs_or_400(
    clip: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_refs = clip.get("source_refs")
    storyboard_ref = (
        source_refs.get("clip_storyboard") if isinstance(source_refs, dict) else None
    )
    sheet_ref = clip.get("clip_storyboard_sheet_asset_ref")
    if not isinstance(storyboard_ref, dict) or not isinstance(sheet_ref, dict):
        _raise_missing_clip_storyboard_panel()
    return storyboard_ref, sheet_ref


def _support_view_panel(
    timeline: Timeline,
    clip_id: str,
    panel_ref: dict[str, Any],
) -> dict[str, Any]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    support_views = spec.get("support_views")
    grid = (
        support_views.get("storyboard_grid")
        if isinstance(support_views, dict)
        else None
    )
    panels = grid.get("panels") if isinstance(grid, dict) else None
    if isinstance(panels, list):
        for panel in panels:
            if not isinstance(panel, dict):
                continue
            if panel.get("clip_id") == clip_id:
                return dict(panel)
            if panel.get("panel_id") == panel_ref.get("panel_id"):
                return dict(panel)
    return dict(panel_ref)


def _clip_storyboard_support_view_panel(
    timeline: Timeline,
    clip_id: str,
    storyboard_ref: dict[str, Any],
) -> dict[str, Any]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    support_views = spec.get("support_views")
    clip_storyboards = (
        support_views.get("clip_storyboards")
        if isinstance(support_views, dict)
        else None
    )
    storyboard = (
        clip_storyboards.get(clip_id)
        if isinstance(clip_storyboards, dict)
        else None
    )
    panels = storyboard.get("panels") if isinstance(storyboard, dict) else None
    if isinstance(panels, list):
        for panel in panels:
            if not isinstance(panel, dict):
                continue
            if panel.get("panel_id") == storyboard_ref.get("panel_id"):
                return dict(panel)
            if panel.get("panel_index") == storyboard_ref.get("panel_index"):
                return dict(panel)
        for panel in panels:
            if isinstance(panel, dict):
                return dict(panel)
    return dict(storyboard_ref)


def _dedupe_strings(values: list[Any]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip() and value.strip() not in deduped:
            deduped.append(value.strip())
    return deduped


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _raise_missing_grid_panel() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="timeline clip missing storyboard grid panel",
    )


def _raise_missing_clip_storyboard_panel() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="timeline clip missing clip storyboard panel",
    )
