from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

TimelineStatus = Literal["draft", "ready", "locked", "archived"]
RenderJobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
RenderType = Literal["proxy", "final", "export"]
TimelineClipReworkAction = Literal["re_dub", "re_cut", "re_render"]
TimelineClipVideoReworkAction = Literal["re_cut", "re_render"]


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


class TimelineClipAssetResponse(BaseModel):
    id: int
    business_id: str
    timeline_id: int
    timeline_version: int
    clip_id: str
    track_type: Optional[str] = None
    asset_role: str
    media_asset_id: int
    media_asset: Optional[MediaAssetResponse] = None
    render_job_id: Optional[int] = None
    source: Optional[str] = None
    source_ref: Optional[Dict[str, Any]] = None
    replacement_of_id: Optional[int] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
    deleted_reason: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TimelineClipAssetListResponse(BaseModel):
    items: List[TimelineClipAssetResponse]


class TimelineClipReworkRequest(TimelineVersionRequest):
    action: TimelineClipReworkAction
    media_asset_id: int = Field(..., ge=1)
    asset_role: Optional[str] = Field(None, max_length=64)
    reason: Optional[str] = Field(None, max_length=255)


class TimelineClipVideoReworkTaskRequest(TimelineVersionRequest):
    action: TimelineClipVideoReworkAction = "re_cut"
    prompt: Optional[str] = Field(None, max_length=4000)
    model: Optional[str] = Field(None, max_length=128)
    duration: Optional[float] = Field(None, gt=0)
    fps: int = Field(24, ge=1, le=120)
    resolution: str = Field("720p", max_length=64)
    ratio: Optional[str] = Field(None, max_length=32)
    asset_role: Optional[str] = Field(None, max_length=64)
    reason: Optional[str] = Field(None, max_length=255)
    use_end_frame: bool = True
    return_last_frame: bool = True


class TimelineClipVideoReworkTaskResponse(BaseModel):
    task_id: int
    status: str


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
