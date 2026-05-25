"""Script creation endpoints."""

from __future__ import annotations

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Script
from app.models.user import User
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.schemas.script import ScriptCreate, ScriptResponse
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", response_model=ScriptResponse)
async def create_script(
    script: ScriptCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建剧本"""
    episode = ScriptsRouteRepository(db).get_create_episode(
        episode_id=script.episode_id,
        current_user=current_user,
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    word_count = len(script.content.split()) if script.content else 0
    character_count = len(script.content) if script.content else 0
    db_script = Script(
        **script.dict(), word_count=word_count, character_count=character_count
    )
    db.add(db_script)
    db.commit()
    db.refresh(db_script)

    try:
        sync_script_scenes_to_story_structure(db, db_script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（create）", exc_info=True)

    return ScriptResponse.from_orm(db_script)
