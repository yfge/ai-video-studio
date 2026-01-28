from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

AspectRatio = Literal["9:16", "16:9"]


class ContextPackBudget(BaseModel):
    """A lightweight, char-based budget (approximate token control)."""

    max_total_chars: int = Field(
        8000, ge=1000, le=50000, description="Approximate JSON char budget."
    )
    max_field_chars: int = Field(
        1200, ge=100, le=20000, description="Max chars per long text field."
    )
    max_character_cards: int = Field(8, ge=0, le=100)
    max_recent_episode_summaries: int = Field(3, ge=0, le=50)


class ContextPackMeta(BaseModel):
    version: str = Field("v1")
    estimated_chars: int = 0
    budget: ContextPackBudget = Field(default_factory=ContextPackBudget)
    trims: List[str] = Field(default_factory=list)


class CharacterCard(BaseModel):
    id: int
    name: str
    role_type: Optional[str] = None
    description: Optional[str] = None

    background_story: Optional[str] = None
    biography: Optional[str] = None

    style_prompt: Optional[str] = None
    voice_config: Optional[Dict[str, Any]] = None


class EpisodeSummary(BaseModel):
    episode_id: int
    episode_number: int
    title: str
    summary: Optional[str] = None


class StoryOutlineCore(BaseModel):
    premise: Optional[str] = None
    synopsis: Optional[str] = None
    main_conflict: Optional[str] = None
    resolution: Optional[str] = None


class StorySetting(BaseModel):
    setting_time: Optional[str] = None
    setting_location: Optional[str] = None
    world_building: Optional[str] = None


class StoryContextPack(BaseModel):
    meta: ContextPackMeta = Field(default_factory=ContextPackMeta)

    story_id: int
    story_title: str
    story_format: Optional[str] = None
    genre: Optional[str] = None

    default_aspect_ratio: Optional[AspectRatio] = None
    style_preferences: List[str] = Field(default_factory=list)
    content_restrictions: List[str] = Field(default_factory=list)

    marketing_meta: Dict[str, Any] = Field(default_factory=dict)
    outline: StoryOutlineCore = Field(default_factory=StoryOutlineCore)
    setting: StorySetting = Field(default_factory=StorySetting)

    character_cards: List[CharacterCard] = Field(default_factory=list)
    character_relationships: Dict[str, Any] = Field(default_factory=dict)

    continuity_ledger: Optional[Dict[str, Any]] = None
    recent_episodes: List[EpisodeSummary] = Field(default_factory=list)


class EpisodeContextPack(BaseModel):
    meta: ContextPackMeta = Field(default_factory=ContextPackMeta)

    story: StoryContextPack
    episode_number: Optional[int] = None
    episode_id: Optional[int] = None
