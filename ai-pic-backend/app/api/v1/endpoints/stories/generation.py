from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.generation_requests import StoryGenerationRequest
from app.schemas.script import StoryResponse
from app.services.story.story_generation_service import StoryGenerationService
from app.services.story.story_generation_prompt_preview import (
    build_story_outline_preview_prompt,
)

router = APIRouter()


@router.post("/generate")
async def generate_story(
    request: StoryGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """使用AI生成故事概要"""
    service = StoryGenerationService(db, current_user)
    story = await service.generate_story(request)
    return {"success": True, "data": StoryResponse.from_orm(story)}


@router.post("/prompt/preview")
async def preview_story_prompt(
    request: StoryGenerationRequest,
):
    """返回根据请求生成的最终提示词（不调用模型）"""
    prompt = build_story_outline_preview_prompt(request)
    return {"success": True, "data": {"prompt": prompt}}
