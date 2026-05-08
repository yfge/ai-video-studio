from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    class Config:
        from_attributes = True


class EnvironmentAssetSummary(ORMModel):
    id: int
    business_id: str
    name: str
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    description: Optional[str] = None
    reference_images: Optional[list[str]] = None


class VirtualIPLinkSummary(ORMModel):
    id: int
    business_id: str
    name: str


class VirtualIPEnvironmentCreate(BaseModel):
    environment_id: int
    usage_type: str = Field("scene_pool", max_length=32)
    usage_note: Optional[str] = None
    sort_order: int = 0
    is_default: bool = False


class VirtualIPEnvironmentUpdate(BaseModel):
    usage_type: Optional[str] = Field(None, max_length=32)
    usage_note: Optional[str] = None
    sort_order: Optional[int] = None
    is_default: Optional[bool] = None


class VirtualIPEnvironmentResponse(ORMModel):
    id: int
    business_id: str
    user_id: Optional[int] = None
    virtual_ip_id: int
    virtual_ip_business_id: Optional[str] = None
    environment_id: int
    environment_business_id: Optional[str] = None
    usage_type: str
    usage_note: Optional[str] = None
    sort_order: int
    is_default: bool
    environment: EnvironmentAssetSummary
    created_at: datetime
    updated_at: Optional[datetime] = None
