"""Shared route helpers for script endpoints."""

from __future__ import annotations

from typing import Optional

from app.models.script import Script
from app.models.user import User
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from fastapi import HTTPException
from sqlalchemy.orm import Session


def not_deleted(query, model):
    return ScriptsRouteRepository.not_deleted(query, model)


def get_script_by_identifier(
    db: Session,
    script_id: Optional[int],
    script_business_id: Optional[str],
    current_user: User,
) -> Script:
    """按主键或 business_id 获取剧本，校验归属与软删状态。"""
    if not script_business_id and not script_id:
        raise HTTPException(status_code=400, detail="script identifier missing")
    script = ScriptsRouteRepository(db).get_script_by_identifier(
        script_id=script_id,
        script_business_id=script_business_id,
        current_user=current_user,
    )
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    return script
