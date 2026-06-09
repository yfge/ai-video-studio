from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StoryCharacterBase(BaseModel):
    virtual_ip_id: int
    character_name: Optional[str] = None
    role_type: Optional[str] = Field(
        None, description="角色类型：protagonist, antagonist, supporting"
    )
    importance: int = Field(1, ge=1, le=5, description="重要度：1-5")
    personality: Optional[str] = None
    background: Optional[str] = None
    motivation: Optional[str] = None
    character_arc: Optional[str] = None
    relationships: Optional[Dict[str, Any]] = None


class StoryCharacterCreate(StoryCharacterBase):
    pass


class StoryCharacterUpdate(BaseModel):
    character_name: Optional[str] = None
    role_type: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=5)
    personality: Optional[str] = None
    background: Optional[str] = None
    motivation: Optional[str] = None
    character_arc: Optional[str] = None
    relationships: Optional[Dict[str, Any]] = None


class StoryCharacterResponse(StoryCharacterBase):
    id: int
    story_id: int
    virtual_ip_business_id: Optional[str] = None
    virtual_ip_name: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
