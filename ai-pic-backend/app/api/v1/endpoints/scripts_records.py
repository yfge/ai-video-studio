"""Script record CRUD and export endpoints."""

from __future__ import annotations

from app.api.v1.endpoints.scripts_route_utils import get_script_by_identifier
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Script
from app.models.user import User
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.schemas.script import ScriptResponse, ScriptUpdate
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧本详情"""
    script = get_script_by_identifier(db, script_id, None, current_user)
    return ScriptResponse.from_orm(script)


@router.get("/business/{script_business_id}", response_model=ScriptResponse)
async def get_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 获取剧本详情"""
    script = get_script_by_identifier(db, None, script_business_id, current_user)
    return ScriptResponse.from_orm(script)


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新剧本"""
    script = get_script_by_identifier(db, script_id, None, current_user)
    for field, value in script_update.dict(exclude_unset=True).items():
        setattr(script, field, value)
    if script_update.content:
        script.word_count = len(script_update.content.split())
        script.character_count = len(script_update.content)
        script.page_count = max(1, script.character_count // 2000)

    db.commit()
    db.refresh(script)
    _sync_script_scenes(db, script, "update")
    return ScriptResponse.from_orm(script)


@router.put("/business/{script_business_id}", response_model=ScriptResponse)
async def update_script_by_business_id(
    script_business_id: str,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 更新剧本"""
    script = get_script_by_identifier(db, None, script_business_id, current_user)
    for field, value in script_update.dict(exclude_unset=True).items():
        setattr(script, field, value)
    if script_update.content:
        script.word_count = len(script_update.content.split())
        script.character_count = len(script_update.content)
        script.page_count = max(1, script.character_count // 2000)

    db.commit()
    db.refresh(script)
    _sync_script_scenes(db, script, "update")
    return ScriptResponse.from_orm(script)


@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除剧本"""
    script = get_script_by_identifier(db, script_id, None, current_user)
    script.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()
    return {"message": "剧本删除成功"}


@router.delete("/business/{script_business_id}")
async def delete_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 删除剧本"""
    script = get_script_by_identifier(db, None, script_business_id, current_user)
    script.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()
    return {"message": "剧本删除成功"}


@router.post("/{script_id}/export")
async def export_script(
    script_id: int,
    format: str = Query("txt", description="导出格式：txt, pdf, docx"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """导出剧本"""
    script = ScriptsRouteRepository(db).get_export_script(
        script_id=script_id,
        current_user=current_user,
    )
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    return {
        "script_id": script_id,
        "title": script.title,
        "format": format,
        "content": script.content,
        "export_time": "2024-01-01T00:00:00Z",
    }


def _sync_script_scenes(db: Session, script: Script, action: str) -> None:
    try:
        sync_script_scenes_to_story_structure(db, script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（%s）", action, exc_info=True)
