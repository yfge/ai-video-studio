from typing import Literal

from app.schemas.production_canvas import ProductionCanvasResolvedContext
from pydantic import BaseModel, Field


class SingleVideoProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1, max_length=4000)
    duration_minutes: int | None = Field(None, ge=1, le=120)
    duration_seconds: int | None = Field(None, ge=1, le=7200)
    aspect_ratio: Literal["9:16", "16:9", "1:1"] | None = None
    style: str | None = Field(None, max_length=255)
    virtual_ip_id: int | None = Field(None, ge=1)
    environment_id: int | None = Field(None, ge=1)
    start_generation: bool = True


class SingleVideoProjectResponse(BaseModel):
    story_id: int
    story_business_id: str
    episode_id: int
    episode_business_id: str
    task_id: int | None = None
    task_status: str | None = None
    context: ProductionCanvasResolvedContext
