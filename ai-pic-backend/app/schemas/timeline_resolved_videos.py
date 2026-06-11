"""Resolved Timeline video source read model."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel

TimelineResolvedVideoStatus = Literal["ready", "generating", "missing"]


class TimelineResolvedVideoItem(BaseModel):
    clip_id: str
    status: TimelineResolvedVideoStatus
    url: Optional[str] = None
    source: Optional[str] = None
    reason: Optional[str] = None
    scene_id: Optional[Any] = None
    scene_number: Optional[Any] = None
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    duration_seconds: float
    task_id: Optional[int] = None
    task_type: Optional[str] = None
    task_status: Optional[str] = None
    task_title: Optional[str] = None


class TimelineResolvedVideoListResponse(BaseModel):
    timeline_id: int
    timeline_version: int
    ready: bool
    video_clip_count: int
    missing_clip_count: int
    generating_clip_count: int
    items: list[TimelineResolvedVideoItem]
