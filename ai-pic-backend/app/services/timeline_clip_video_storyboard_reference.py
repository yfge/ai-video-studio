"""Clip storyboard sheet and legacy panel references for video rework."""

from __future__ import annotations

from typing import Any, Callable

from app.models.timeline import Timeline
from app.schemas.timeline import TimelineClipVideoReworkTaskRequest
from app.services.storyboard.clip_storyboard_video_sequence_prompt import (
    build_clip_storyboard_sequence_video_prompt,
)
from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_clip_storyboard_video_prompt,
)
from fastapi import HTTPException, status


def build_clip_storyboard_rework_payload(
    timeline: Timeline,
    clip_id: str,
    clip: dict[str, Any],
    payload: TimelineClipVideoReworkTaskRequest,
    *,
    duration_seconds: float,
    asset_ref_url: Callable[[Any], str | None],
    fallback_prompt: Callable[[dict[str, Any], str | None], str | None],
) -> dict[str, Any]:
    storyboard_ref, sheet_ref = _clip_storyboard_refs_or_400(clip)
    sheet_url = asset_ref_url(sheet_ref)
    if not sheet_url:
        _raise_missing_clip_storyboard()
    storyboard = _clip_storyboard_support_view(timeline, clip_id)
    panels = _ordered_panels(storyboard)
    if payload.reference_mode == "clip_storyboard_panel":
        return _legacy_panel_payload(
            panels,
            storyboard_ref,
            sheet_ref,
            sheet_url,
            clip_id,
            clip,
            payload,
            fallback_prompt,
        )
    return _sheet_sequence_payload(
        panels,
        storyboard_ref,
        sheet_ref,
        sheet_url,
        clip_id,
        duration_seconds,
        payload,
    )


def _sheet_sequence_payload(
    panels: list[dict[str, Any]],
    storyboard_ref: dict[str, Any],
    sheet_ref: dict[str, Any],
    sheet_url: str,
    clip_id: str,
    duration_seconds: float,
    payload: TimelineClipVideoReworkTaskRequest,
) -> dict[str, Any]:
    if not panels:
        _raise_missing_clip_storyboard()
    return {
        "prompt": build_clip_storyboard_sequence_video_prompt(
            panels,
            clip_id=clip_id,
            duration_seconds=duration_seconds,
            prompt_override=payload.prompt,
        ),
        "reference_images": _dedupe_strings(
            [sheet_url] + list(payload.reference_images or [])
        ),
        "clip_storyboard": {
            "mode": "sheet_sequence",
            "panel_count": len(panels),
            "panel_ids": [panel.get("panel_id") for panel in panels],
            "sheet_media_asset_id": _sheet_asset_id(storyboard_ref, sheet_ref),
            "source_timeline_version": storyboard_ref.get("source_timeline_version"),
            "reading_order": "left_to_right_top_to_bottom",
            "duration_seconds": round(float(duration_seconds), 3),
        },
    }


def _legacy_panel_payload(
    panels: list[dict[str, Any]],
    storyboard_ref: dict[str, Any],
    sheet_ref: dict[str, Any],
    sheet_url: str,
    clip_id: str,
    clip: dict[str, Any],
    payload: TimelineClipVideoReworkTaskRequest,
    fallback_prompt: Callable[[dict[str, Any], str | None], str | None],
) -> dict[str, Any]:
    panel = _selected_panel(panels, {**sheet_ref, **storyboard_ref})
    video_prompt = (
        payload.prompt or panel.get("video_prompt") or fallback_prompt(clip, None) or ""
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
            "mode": "panel_legacy",
            "panel_id": prompt_panel.get("panel_id"),
            "panel_index": prompt_panel.get("panel_index"),
            "sheet_media_asset_id": _sheet_asset_id(storyboard_ref, sheet_ref),
            "source_timeline_version": storyboard_ref.get("source_timeline_version"),
        },
    }


def _clip_storyboard_refs_or_400(
    clip: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_refs = clip.get("source_refs")
    storyboard_ref = (
        source_refs.get("clip_storyboard") if isinstance(source_refs, dict) else None
    )
    sheet_ref = clip.get("clip_storyboard_sheet_asset_ref")
    if not isinstance(storyboard_ref, dict) or not isinstance(sheet_ref, dict):
        _raise_missing_clip_storyboard()
    return storyboard_ref, sheet_ref


def _clip_storyboard_support_view(timeline: Timeline, clip_id: str) -> dict[str, Any]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    support_views = spec.get("support_views")
    clip_storyboards = (
        support_views.get("clip_storyboards")
        if isinstance(support_views, dict)
        else None
    )
    storyboard = (
        clip_storyboards.get(clip_id) if isinstance(clip_storyboards, dict) else None
    )
    return dict(storyboard) if isinstance(storyboard, dict) else {}


def _ordered_panels(storyboard: dict[str, Any]) -> list[dict[str, Any]]:
    panels = storyboard.get("panels")
    if not isinstance(panels, list):
        return []
    valid = [dict(panel) for panel in panels if isinstance(panel, dict)]
    return sorted(valid, key=lambda panel: int(panel.get("panel_index") or 0))


def _selected_panel(
    panels: list[dict[str, Any]], storyboard_ref: dict[str, Any]
) -> dict[str, Any]:
    for panel in panels:
        if panel.get("panel_id") == storyboard_ref.get("panel_id"):
            return panel
        if panel.get("panel_index") == storyboard_ref.get("panel_index"):
            return panel
    return panels[0] if panels else dict(storyboard_ref)


def _sheet_asset_id(storyboard_ref: dict[str, Any], sheet_ref: dict[str, Any]) -> Any:
    return storyboard_ref.get("sheet_media_asset_id") or sheet_ref.get("media_asset_id")


def _dedupe_strings(values: list[Any]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip() and value.strip() not in deduped:
            deduped.append(value.strip())
    return deduped


def _raise_missing_clip_storyboard() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="timeline clip missing clip storyboard sheet or panels",
    )
