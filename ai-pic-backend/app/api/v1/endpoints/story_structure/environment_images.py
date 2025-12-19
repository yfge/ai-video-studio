"""
Story Structure environment image CRUD endpoints.

Upload, list, and delete environment reference images.
"""

from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.story_structure import Environment
from app.models.user import User
from app.schemas.story_structure import (
    EnvironmentImageResponse,
    EnvironmentImagesResponse,
)
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.services.storage import oss_service

router = APIRouter()


@router.get("/environments/{env_id}/images", response_model=EnvironmentImagesResponse)
async def list_environment_images(
    env_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if env and not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        env = None
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    images = env.reference_images or []
    normalized: List[EnvironmentImageResponse] = []
    for url in images:
        if isinstance(url, str):
            normalized.append(EnvironmentImageResponse(url=url))
    return EnvironmentImagesResponse(images=normalized, count=len(normalized))


@router.delete("/environments/{env_id}/images")
async def delete_environment_image(
    env_id: str,
    image_url: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if env and not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        env = None
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    refs = env.reference_images or []
    env.reference_images = [u for u in refs if u != image_url]
    db.commit()
    images = [
        EnvironmentImageResponse(url=url)
        for url in env.reference_images or []
        if isinstance(url, str)
    ]
    return {
        "success": True,
        "data": EnvironmentImagesResponse(
            images=images,
            count=len(images),
        ),
    }


@router.post(
    "/environments/{env_id}/images/upload",
    response_model=EnvironmentImageResponse,
)
async def upload_environment_image(
    env_id: str,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload environment reference image with unified persistence and OSS upload strategy."""
    env = svc.resolve_environment(db, env_id)
    if env and not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        env = None
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")

    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    content = await image.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
        )

    try:
        stored = await ai_service.persist_uploaded_image(
            file_bytes=content,
            original_filename=image.filename or "environment.png",
            prefix="user-uploads/environments",
            metadata={
                "environment_id": env.id,
                "uploader_id": current_user.id,
                "category": env.category or "",
            },
            require_upload=bool(oss_service),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"环境图像保存失败: {exc}") from exc

    final_url = stored.get("oss_url") or stored.get("relative_path")
    if not final_url:
        raise HTTPException(status_code=500, detail="环境图像未返回可用 URL")

    refs = env.reference_images or []
    refs.insert(0, final_url)
    env.reference_images = refs
    db.query(Environment).filter(Environment.id == env.id).update(
        {"reference_images": env.reference_images}
    )
    db.commit()
    db.refresh(env)

    return EnvironmentImageResponse(url=final_url)
