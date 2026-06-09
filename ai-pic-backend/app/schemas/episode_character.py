from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EpisodeCharacterBase(BaseModel):
    """Base schema for Episode character."""

    character_name: Optional[str] = Field(
        None, max_length=100, description="Character name (overrides VirtualIP.name)"
    )
    role_type: Optional[str] = Field(
        "temporary", max_length=50, description="Role type: temporary/guest/extra"
    )
    importance: Optional[int] = Field(1, ge=1, le=5, description="Importance level 1-5")
    personality: Optional[str] = Field(
        None, description="Personality (overrides VirtualIP)"
    )
    background: Optional[str] = Field(
        None, description="Background (overrides VirtualIP)"
    )
    appearance_override: Optional[str] = Field(
        None, description="Appearance supplement to VirtualIP.style_prompt"
    )
    voice_config_override: Optional[Dict[str, Any]] = Field(
        None, description="Voice config override"
    )
    scene_appearances: Optional[List[Dict[str, Any]]] = Field(
        None, description="Scene appearances"
    )
    first_appearance_scene: Optional[int] = Field(
        None, description="First appearance scene number"
    )
    last_appearance_scene: Optional[int] = Field(
        None, description="Last appearance scene number"
    )
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class EpisodeCharacterCreate(EpisodeCharacterBase):
    """Schema for creating an Episode character."""

    virtual_ip_id: int = Field(
        ..., description="VirtualIP ID (required for resource binding)"
    )


class EpisodeCharacterUpdate(EpisodeCharacterBase):
    """Schema for updating an Episode character."""

    pass


class EpisodeCharacterResponse(EpisodeCharacterBase):
    """Schema for Episode character response."""

    id: int
    business_id: str
    episode_id: int
    episode_business_id: Optional[str]
    virtual_ip_id: int
    virtual_ip_business_id: Optional[str]
    virtual_ip_name: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    is_deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[int]
    deleted_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EpisodeCharacterWithResources(EpisodeCharacterResponse):
    """Extended response with resolved resources."""

    resolved_voice_config: Optional[Dict[str, Any]] = Field(
        None, description="Resolved voice config (override or VirtualIP default)"
    )
    resolved_images: Optional[List[Dict[str, Any]]] = Field(
        None, description="VirtualIP images sorted by priority"
    )
    resolved_appearance_prompt: Optional[str] = Field(
        None, description="Merged appearance description"
    )
    display_name: str = Field(
        ..., description="Display name (character_name or VirtualIP.name)"
    )


class EpisodeCharacterListResponse(BaseModel):
    """Paginated list response."""

    items: List[EpisodeCharacterResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
