"""Build clip-scoped storyboard sheet generation payloads."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.schemas.timeline import TimelineClipStoryboardGenerateRequest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .clip_storyboard_approved_style_anchor import apply_approved_3d_style_anchor
from .clip_storyboard_context import build_clip_storyboard_context
from .clip_storyboard_panel_sanitizer import sanitize_clip_storyboard_panels
from .clip_storyboard_panel_selection import select_clip_storyboard_panel_count
from .grid_storyboard_prompt_bridge import (
    build_clip_storyboard_panels,
    build_clip_storyboard_sheet_prompt,
    grid_layout,
)
from .grid_storyboard_sheet_payload import clip_source_signature

DEFAULT_CLIP_STORYBOARD_MODEL = "codex:gpt-image-2"


def build_clip_storyboard_sheet_task_payload(
    db: Session,
    *,
    timeline: Timeline,
    clip_id: str,
    clip: dict[str, Any],
    payload: TimelineClipStoryboardGenerateRequest,
) -> dict[str, Any]:
    panel_selection = select_clip_storyboard_panel_count(clip, payload.panel_count)
    panels = build_clip_storyboard_panels(clip, panel_selection.panel_count)
    if not panels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="clip storyboard panels missing",
        )

    context = build_clip_storyboard_context(
        db,
        timeline=timeline,
        clip=clip,
        panels=panels,
        request_reference_images=payload.reference_images or [],
        request_character_virtual_ip_ids=payload.character_virtual_ip_ids or [],
        request_character_reference_images=payload.character_reference_images or [],
        request_environment_reference_images=payload.environment_reference_images or [],
    )
    context = apply_approved_3d_style_anchor(
        db,
        timeline_id=timeline.id,
        style=payload.style,
        context=context,
    )
    panels = sanitize_clip_storyboard_panels(context.panels, style=payload.style)
    layout = grid_layout(panel_selection.panel_count)
    sheet_prompt = build_clip_storyboard_sheet_prompt(panels, style=payload.style)
    return {
        "kind": "timeline_clip_storyboard",
        "timeline_id": timeline.id,
        "timeline_business_id": timeline.business_id,
        "timeline_version": timeline.version,
        "expected_version": payload.expected_version,
        "clip_id": clip_id,
        "clip_source_signature": clip_source_signature(clip),
        "panel_count": layout.panel_count,
        "panel_selection": panel_selection.as_dict(),
        "columns": layout.columns,
        "rows": layout.rows,
        "style": payload.style,
        "model": payload.model or DEFAULT_CLIP_STORYBOARD_MODEL,
        "generation_profile": payload.generation_profile,
        "size": "auto" if layout.aspect_ratio != "1:1" else payload.size,
        "aspect_ratio": layout.aspect_ratio,
        "width": payload.width,
        "height": payload.height,
        "reference_images": context.reference_images,
        "character_virtual_ip_ids": payload.character_virtual_ip_ids or [],
        "character_reference_images": payload.character_reference_images or [],
        "environment_reference_images": payload.environment_reference_images or [],
        "bound_context": context.bound_context,
        "panels": panels,
        "sheet_prompt": sheet_prompt,
    }
