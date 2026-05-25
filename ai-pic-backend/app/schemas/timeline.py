from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

TimelineStatus = Literal["draft", "ready", "locked", "archived"]
RenderJobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
RenderType = Literal["proxy", "final", "export"]


class TimelineCreate(BaseModel):
    script_id: int
    title: Optional[str] = Field(None, max_length=255)
    status: TimelineStatus = "draft"
    spec: Dict[str, Any]
    source_audio_timeline_version: Optional[int] = None


class TimelineUpdate(BaseModel):
    expected_version: int = Field(..., ge=1)
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[TimelineStatus] = None
    spec: Optional[Dict[str, Any]] = None
    source_audio_timeline_version: Optional[int] = None


class TimelineVersionRequest(BaseModel):
    expected_version: int = Field(..., ge=1)


class TimelineDeleteRequest(TimelineVersionRequest):
    reason: Optional[str] = Field(None, max_length=255)


class TimelineRollbackRequest(TimelineVersionRequest):
    target_version: int = Field(..., ge=1)


class TimelineRollbackState(BaseModel):
    source_version: int
    target_version: int
    rolled_back_at: datetime
    rolled_back_by: Optional[int] = None


class TimelineResponse(BaseModel):
    id: int
    business_id: str
    episode_id: int
    episode_business_id: Optional[str] = None
    script_id: int
    script_business_id: Optional[str] = None
    title: str
    status: str
    spec: Dict[str, Any]
    version: int
    source_audio_timeline_version: Optional[int] = None
    rollback: Optional[TimelineRollbackState] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    deleted_reason: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimelineListResponse(BaseModel):
    items: List[TimelineResponse]


class MediaAssetResponse(BaseModel):
    id: int
    business_id: str
    asset_type: str
    origin: str
    file_url: Optional[str] = None
    object_key: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    hash: Optional[str] = None
    duration_ms: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RenderJobCreate(BaseModel):
    timeline_version: int = Field(..., ge=1)
    render_type: RenderType
    preset: Dict[str, Any] = Field(default_factory=dict)
    force_new_attempt: bool = False


class RenderJobResponse(BaseModel):
    id: int
    business_id: str
    timeline_id: int
    timeline_version: int
    render_type: str
    preset_hash: str
    preset: Dict[str, Any]
    status: str
    progress: int
    output_asset_id: Optional[int] = None
    output_asset: Optional[MediaAssetResponse] = None
    log: Optional[Dict[str, Any]] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    deleted_reason: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RenderJobListResponse(BaseModel):
    items: List[RenderJobResponse]
