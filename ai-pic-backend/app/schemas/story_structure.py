from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    class Config:
        from_attributes = True


class StoryTreatmentCreate(BaseModel):
    story_id: int
    revision_number: int = 1
    title: str
    status: str = "draft"
    logline: Optional[str] = None
    theme_summary: Optional[str] = None
    act_structure: Optional[dict[str, Any]] = None
    target_audience_notes: Optional[str] = None
    tone_reference: Optional[dict[str, Any]] = None
    ai_prompt_snapshot: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class StoryTreatmentResponse(ORMModel):
    id: int
    story_id: int
    revision_number: int
    title: str
    status: str
    logline: Optional[str]
    theme_summary: Optional[str]
    act_structure: Optional[dict[str, Any]]
    target_audience_notes: Optional[str]
    tone_reference: Optional[dict[str, Any]]
    ai_prompt_snapshot: Optional[dict[str, Any]]
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    created_at: datetime
    updated_at: datetime


class StoryStepOutlineCreate(BaseModel):
    story_id: int
    story_treatment_id: int
    sequence_number: int
    beat_title: str
    act_label: Optional[str] = None
    beat_summary: Optional[str] = None
    dramatic_question: Optional[str] = None
    characters_involved: Optional[dict[str, Any]] = None
    location_hint: Optional[str] = None
    duration_estimate_minutes: Optional[float] = Field(None, ge=0)
    status: str = "draft"
    metadata: Optional[dict[str, Any]] = None
    episode_id: Optional[int] = None


class StoryStepOutlineResponse(ORMModel):
    id: int
    story_id: int
    story_treatment_id: int
    sequence_number: int
    act_label: Optional[str]
    beat_title: str
    beat_summary: Optional[str]
    dramatic_question: Optional[str]
    characters_involved: Optional[dict[str, Any]]
    location_hint: Optional[str]
    duration_estimate_minutes: Optional[float]
    status: str
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    created_at: datetime
    updated_at: datetime


class SceneCreate(BaseModel):
    script_id: int
    scene_number: str
    slug_line: str
    story_step_outline_id: Optional[int] = None
    environment_id: Optional[int] = None
    environment_type: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    summary: Optional[str] = None
    page_length_eighths: Optional[int] = None
    primary_characters: Optional[dict[str, Any]] = None
    conflict_notes: Optional[str] = None
    ai_prompt_snapshot: Optional[dict[str, Any]] = None
    status: str = "draft"
    metadata: Optional[dict[str, Any]] = None


class SceneResponse(ORMModel):
    id: int
    script_id: int
    scene_number: str
    slug_line: str
    environment_id: Optional[int]
    environment_type: Optional[str]
    location: Optional[str]
    time_of_day: Optional[str]
    summary: Optional[str]
    page_length_eighths: Optional[int]
    primary_characters: Optional[dict[str, Any]]
    conflict_notes: Optional[str]
    ai_prompt_snapshot: Optional[dict[str, Any]]
    status: str
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    created_at: datetime
    updated_at: datetime


class SceneUpdate(BaseModel):
    slug_line: Optional[str] = None
    scene_number: Optional[str] = None
    story_step_outline_id: Optional[int] = None
    environment_id: Optional[int] = None
    environment_type: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    summary: Optional[str] = None
    page_length_eighths: Optional[int] = None
    primary_characters: Optional[dict[str, Any]] = None
    conflict_notes: Optional[str] = None
    ai_prompt_snapshot: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class SceneBeatCreate(BaseModel):
    scene_id: int
    order_index: int
    beat_type: Optional[str] = None
    beat_summary: Optional[str] = None
    characters_involved: Optional[dict[str, Any]] = None
    dialogue_excerpt: Optional[str] = None
    camera_notes: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0)
    metadata: Optional[dict[str, Any]] = None


class SceneBeatResponse(ORMModel):
    id: int
    scene_id: int
    order_index: int
    beat_type: Optional[str]
    beat_summary: Optional[str]
    characters_involved: Optional[dict[str, Any]]
    dialogue_excerpt: Optional[str]
    camera_notes: Optional[str]
    duration_seconds: Optional[float]
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    created_at: datetime
    updated_at: datetime


class SceneBeatUpdate(BaseModel):
    beat_type: Optional[str] = None
    beat_summary: Optional[str] = None
    characters_involved: Optional[dict[str, Any]] = None
    dialogue_excerpt: Optional[str] = None
    camera_notes: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0)
    order_index: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


class ShotCreate(BaseModel):
    scene_id: int
    shot_number: str
    scene_beat_id: Optional[int] = None
    shot_type: Optional[str] = None
    camera_setup: Optional[str] = None
    camera_movement: Optional[str] = None
    framing: Optional[str] = None
    focus_subject: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0)
    storyboard_frame_asset_id: Optional[int] = None
    lighting_notes: Optional[str] = None
    audio_notes: Optional[str] = None
    status: str = "planned"
    metadata: Optional[dict[str, Any]] = None


class ShotResponse(ORMModel):
    id: int
    scene_id: int
    shot_number: str
    scene_beat_id: Optional[int]
    shot_type: Optional[str]
    camera_setup: Optional[str]
    camera_movement: Optional[str]
    framing: Optional[str]
    focus_subject: Optional[str]
    duration_seconds: Optional[float]
    storyboard_frame_asset_id: Optional[int]
    lighting_notes: Optional[str]
    audio_notes: Optional[str]
    status: str
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    created_at: datetime
    updated_at: datetime


class ShotUpdate(BaseModel):
    shot_number: Optional[str] = None
    scene_beat_id: Optional[int] = None
    shot_type: Optional[str] = None
    camera_setup: Optional[str] = None
    camera_movement: Optional[str] = None
    framing: Optional[str] = None
    focus_subject: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0)
    storyboard_frame_asset_id: Optional[int] = None
    lighting_notes: Optional[str] = None
    audio_notes: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class EnvironmentCreate(BaseModel):
    name: str
    category: Optional[str] = None  # indoor/outdoor/custom
    tags: Optional[list[str]] = None
    description: Optional[str] = None
    reference_images: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    description: Optional[str] = None
    reference_images: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class EnvironmentResponse(ORMModel):
    id: int
    name: str
    category: Optional[str]
    tags: Optional[list[str]]
    description: Optional[str]
    reference_images: Optional[list[str]]
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    created_at: datetime
    updated_at: datetime


class SceneWithChildren(SceneResponse):
    beats: List[SceneBeatResponse] = Field(default_factory=list)
    shots: List[ShotResponse] = Field(default_factory=list)


class ScriptStructureResponse(BaseModel):
    script_id: int
    scenes: List[SceneWithChildren]
