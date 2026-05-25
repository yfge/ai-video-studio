"""Script list endpoints."""

from __future__ import annotations

from typing import List, Optional

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.schemas.script import ScriptListItemResponse
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=List[ScriptListItemResponse])
async def get_scripts(
    episode_id: Optional[int] = Query(None),
    episode_business_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    format_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧本列表"""
    scripts = ScriptsRouteRepository(db).list_scripts(
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        skip=skip,
        limit=limit,
        status=status,
        format_type=format_type,
        current_user=current_user,
    )
    return [ScriptListItemResponse.from_orm(script) for script in scripts]


@router.get("/episode/{episode_id}", response_model=List[ScriptListItemResponse])
async def get_episode_scripts(
    episode_id: int,
    episode_business_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧集的所有剧本"""
    repository = ScriptsRouteRepository(db)
    episode = repository.get_episode_for_user(
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        current_user=current_user,
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    scripts = repository.list_scripts_for_episode(episode_id)
    scripts_sorted = sorted(
        scripts,
        key=lambda script: int(getattr(script, "id", 0)),
        reverse=True,
    )
    return [ScriptListItemResponse.from_orm(script) for script in scripts_sorted]


@router.get(
    "/episode/business/{episode_business_id}",
    response_model=List[ScriptListItemResponse],
)
async def get_episode_scripts_by_business_id(
    episode_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 episode business_id 获取剧本列表"""
    repository = ScriptsRouteRepository(db)
    episode = repository.get_episode_for_user(
        episode_business_id=episode_business_id,
        current_user=current_user,
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    scripts = repository.list_scripts_for_episode(episode.id)
    scripts_sorted = sorted(
        scripts,
        key=lambda script: int(getattr(script, "id", 0)),
        reverse=True,
    )
    return [ScriptListItemResponse.from_orm(script) for script in scripts_sorted]
