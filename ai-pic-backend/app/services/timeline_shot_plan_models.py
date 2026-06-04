from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class MotionTimelinePoint(BaseModel):
    at_ms: int = Field(..., ge=0)
    action: str = Field(..., min_length=1)


class TimelineShot(BaseModel):
    clip_id: str
    duration_ms: int = Field(..., ge=1)
    plot: str
    dialogue_source: str
    visual_prompt: str = Field(..., min_length=1)
    video_prompt: str = Field(..., min_length=1)
    character_anchor: str = Field(..., min_length=1)
    camera: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    direction_anchor: str = Field(..., min_length=1)
    aesthetic_reference: str = Field(..., min_length=1)
    shot_type: str = Field(..., min_length=1)
    camera_movement: str = Field(..., min_length=1)
    composition_geometry: str = Field(..., min_length=1)
    motion_timeline: list[MotionTimelinePoint] = Field(..., min_length=1, max_length=4)
    emotional_landing: str = Field(..., min_length=1)
    prompt_method: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_motion_timeline_bounds(self) -> "TimelineShot":
        if any(point.at_ms > self.duration_ms for point in self.motion_timeline):
            raise ValueError("motion_timeline at_ms must not exceed duration_ms")
        return self


class TimelineShotPlan(BaseModel):
    shots: list[TimelineShot] = Field(..., min_length=1)
