from typing import Any, Dict, Optional

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.services.virtual_ip_voice_sample_service import VirtualIPVoiceSampleService
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter()


class VirtualIPVoiceSampleRequest(BaseModel):
    source_url: str = Field(..., description="试听音频的源URL")
    preview_text: Optional[str] = Field(None, description="用于生成试听的文本")


class VirtualIPVoiceSampleResponse(BaseModel):
    sample_url: str
    sample_source_url: str
    voice_config: Dict[str, Any]


@router.post("/{ip_id}/voice-sample")
async def save_voice_sample_by_id(
    ip_id: int,
    payload: VirtualIPVoiceSampleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """保存虚拟IP试听音频并转存 OSS（按 ID）。

    示例请求:
    {"source_url": "https://example.com/audio.mp3", "preview_text": "你好，我是小雅。"}

    示例响应:
    {"success": true, "data": {"sample_url": "https://oss/...", "sample_source_url": "..."}}
    """
    service = VirtualIPVoiceSampleService(VirtualIPRepository(db))
    result = await service.save_sample_by_id(
        ip_id=ip_id,
        current_user=current_user,
        source_url=payload.source_url,
        preview_text=payload.preview_text,
    )
    return {"success": True, "data": result}


@router.post("/business/{ip_business_id}/voice-sample")
async def save_voice_sample_by_business_id(
    ip_business_id: str,
    payload: VirtualIPVoiceSampleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """保存虚拟IP试听音频并转存 OSS（按 business_id）。

    示例请求:
    {"source_url": "https://example.com/audio.mp3", "preview_text": "你好，我是小雅。"}

    示例响应:
    {"success": true, "data": {"sample_url": "https://oss/...", "sample_source_url": "..."}}
    """
    service = VirtualIPVoiceSampleService(VirtualIPRepository(db))
    result = await service.save_sample_by_business_id(
        business_id=ip_business_id,
        current_user=current_user,
        source_url=payload.source_url,
        preview_text=payload.preview_text,
    )
    return {"success": True, "data": result}
