"""
Script CRUD endpoints.

Provides basic Create, Read, Update, Delete operations for scripts.
Uses ScriptService for business logic.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.script import ScriptCreate, ScriptResponse, ScriptUpdate
from app.services.script import ScriptService, get_script_service


router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> ScriptService:
    """Dependency to get ScriptService instance."""
    return get_script_service(db)


@router.get("/formats")
async def get_script_formats():
    """获取支持的剧本格式列表"""
    return {
        "formats": [
            {"id": "screenplay", "name": "电影剧本", "description": "标准电影剧本格式"},
            {"id": "teleplay", "name": "电视剧本", "description": "电视剧本格式"},
            {"id": "stage_play", "name": "舞台剧本", "description": "舞台剧本格式"},
            {"id": "audio_drama", "name": "广播剧本", "description": "广播/有声剧格式"},
        ]
    }


@router.get("/languages")
async def get_script_languages():
    """获取支持的语言列表"""
    return {
        "languages": [
            {"id": "zh-CN", "name": "简体中文"},
            {"id": "zh-TW", "name": "繁體中文"},
            {"id": "en-US", "name": "English"},
            {"id": "ja-JP", "name": "日本語"},
        ]
    }


@router.post("/", response_model=ScriptResponse)
async def create_script(
    script: ScriptCreate,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """创建剧本"""
    db_script = service.create_script(script_data=script, user=current_user)
    return ScriptResponse.from_orm(db_script)


@router.get("/", response_model=List[ScriptResponse])
async def get_scripts(
    episode_id: Optional[int] = Query(None, description="剧集ID"),
    episode_business_id: Optional[str] = Query(None, description="剧集业务ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    format_type: Optional[str] = Query(None, description="格式类型筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """获取剧本列表"""
    scripts = service.list_scripts(
        user=current_user,
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        status=status,
        format_type=format_type,
        skip=skip,
        limit=limit,
    )
    return [ScriptResponse.from_orm(s) for s in scripts]


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """获取剧本详情"""
    script = service.get_script(script_id=script_id, user=current_user)
    return ScriptResponse.from_orm(script)


@router.get("/business/{script_business_id}", response_model=ScriptResponse)
async def get_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """按 business_id 获取剧本详情"""
    script = service.get_script(business_id=script_business_id, user=current_user)
    return ScriptResponse.from_orm(script)


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """更新剧本"""
    script = service.update_script(
        script_id=script_id, update_data=script_update, user=current_user
    )
    return ScriptResponse.from_orm(script)


@router.put("/business/{script_business_id}", response_model=ScriptResponse)
async def update_script_by_business_id(
    script_business_id: str,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """按 business_id 更新剧本"""
    script = service.update_script(
        business_id=script_business_id, update_data=script_update, user=current_user
    )
    return ScriptResponse.from_orm(script)


@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """删除剧本"""
    service.delete_script(script_id=script_id, user=current_user)
    return {"message": "剧本删除成功"}


@router.delete("/business/{script_business_id}")
async def delete_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """按 business_id 删除剧本"""
    service.delete_script(business_id=script_business_id, user=current_user)
    return {"message": "剧本删除成功"}


@router.get("/episode/{episode_id}", response_model=List[ScriptResponse])
async def get_episode_scripts(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """获取剧集的所有剧本"""
    scripts = service.get_episode_scripts(
        episode_id=episode_id, user=current_user, limit=50
    )
    return [ScriptResponse.from_orm(s) for s in scripts]


@router.get("/episode/business/{episode_business_id}", response_model=List[ScriptResponse])
async def get_episode_scripts_by_business_id(
    episode_business_id: str,
    current_user: User = Depends(get_current_active_user),
    service: ScriptService = Depends(get_service),
):
    """按 business_id 获取剧集的所有剧本"""
    scripts = service.list_scripts(
        user=current_user,
        episode_business_id=episode_business_id,
        limit=50,
    )
    return [ScriptResponse.from_orm(s) for s in scripts]
