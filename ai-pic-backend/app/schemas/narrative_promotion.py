"""Manual shared-memory promotion contracts."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PromotionCandidateCreate(BaseModel):
    source_memory_ids: list[str] = Field(..., min_length=1)
    candidate_content: str = Field(..., min_length=1)


class PromotionUpdate(BaseModel):
    expected_version: int = Field(..., ge=1)
    candidate_content: Optional[str] = Field(None, min_length=1)
    decision_reason: Optional[str] = None


class PromotionReviewRequest(BaseModel):
    expected_version: int = Field(..., ge=1)
    reason: Optional[str] = None


class SharedMemoryCloneRequest(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    reason: Optional[str] = None


class SharedMemorySupersedeRequest(BaseModel):
    expected_version: int = Field(..., ge=1)
    content: str = Field(..., min_length=1)
    reason: Optional[str] = None


class CharacterMemoryPromotionResponse(BaseModel):
    business_id: str
    source_story_business_id: str
    source_memory_ids: list[str]
    target_virtual_ip_business_id: str
    canon_branch_id: str
    candidate_content: str
    status: str
    decision_reason: Optional[str] = None
    result_shared_memory_business_id: Optional[str] = None
    version: int
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
