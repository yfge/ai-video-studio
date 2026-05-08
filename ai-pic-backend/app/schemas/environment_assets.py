from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.schemas.user import UserSummary
from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    class Config:
        from_attributes = True


class EnvironmentCreate(BaseModel):
    name: str
    category: Optional[str] = None
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


class LinkedVirtualIPSummary(ORMModel):
    id: int
    business_id: str
    name: str


class EnvironmentResponse(ORMModel):
    id: int
    business_id: str
    name: str
    category: Optional[str]
    tags: Optional[list[str]]
    description: Optional[str]
    reference_images: Optional[list[str]]
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    creator: Optional[UserSummary] = Field(None, validation_alias="owner")
    linked_virtual_ips: list[LinkedVirtualIPSummary] = Field(default_factory=list)
    linked_virtual_ip_count: int = 0
    created_at: datetime
    updated_at: datetime


class EnvironmentSummaryResponse(ORMModel):
    """Environment list DTO: excludes heavyweight reference_images."""

    id: int
    business_id: str
    name: str
    category: Optional[str]
    tags: Optional[list[str]]
    description: Optional[str]
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    creator: Optional[UserSummary] = Field(None, validation_alias="owner")
    linked_virtual_ips: list[LinkedVirtualIPSummary] = Field(default_factory=list)
    linked_virtual_ip_count: int = 0
    created_at: datetime
    updated_at: datetime


class EnvironmentImageResponse(BaseModel):
    url: str


class EnvironmentImagesResponse(BaseModel):
    images: list[EnvironmentImageResponse] = Field(default_factory=list)
    count: int = 0
