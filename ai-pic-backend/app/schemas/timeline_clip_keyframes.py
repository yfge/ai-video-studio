from typing import List, Optional

from app.schemas.timeline import TimelineVersionRequest
from pydantic import BaseModel, Field


class TimelineClipKeyframeGenerateRequest(TimelineVersionRequest):
    prompt: Optional[str] = Field(None, max_length=4000)
    model: Optional[str] = Field(None, max_length=128)
    generation_profile: Optional[str] = Field("clip_keyframes", max_length=128)
    size: Optional[str] = Field(None, max_length=32)
    aspect_ratio: Optional[str] = Field("9:16", max_length=32)
    width: Optional[int] = Field(None, ge=1)
    height: Optional[int] = Field(None, ge=1)
    reference_images: Optional[List[str]] = None
    character_virtual_ip_ids: Optional[List[int]] = None
    character_reference_images: Optional[List[str]] = None
    environment_reference_images: Optional[List[str]] = None


class TimelineClipKeyframeGenerateResponse(BaseModel):
    task_id: int
    status: str
