"""Synchronous script generation endpoint."""

from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.script import ScriptResponse
from app.services.script.sync_generation import generate_script_sync
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """使用AI生成剧本"""
    script = await generate_script_sync(db, request, current_user)
    return ScriptResponse.from_orm(script)
