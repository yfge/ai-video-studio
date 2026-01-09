"""
Story Structure environment image variant endpoints.

Image-to-image variant generation for environments (sync and async).
"""

from __future__ import annotations

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.story_structure.environment_image_generation import (
    generate_environment_image_variants as generate_environment_image_variants_service,
)
from app.services.story_structure.environment_image_prompts import (
    compose_environment_prompt,
)
from app.services.story_structure.environment_image_requests import (
    build_environment_variant_task_payload,
    resolve_environment_image_variant_request,
)
from app.services.task_worker import environment_image_variant_task
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .environment_image_helpers import get_owned_environment_or_404, read_json_payload

router = APIRouter()


class EnvironmentImageVariantParams:
    def __init__(
        self,
        base_image: str | None = Query(None, description="基准图 URL 或相对路径"),
        prompt: str | None = Query(None, description="变体提示词"),
        model: str | None = Query(None, description="模型，形如 provider:model_id"),
        count: int = Query(1, ge=1, le=4, description="生成数量"),
        size: str | None = Query(None, description="分辨率/尺寸"),
        aspect_ratio: str | None = Query(None, description="画幅比例，如 16:9、1:1"),
    ) -> None:
        self.base_image = base_image
        self.prompt = prompt
        self.model = model
        self.count = count
        self.size = size
        self.aspect_ratio = aspect_ratio


@router.post("/environments/{env_id}/images/variants")
async def generate_environment_image_variants(
    env_id: str,
    request: Request,
    params: EnvironmentImageVariantParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = get_owned_environment_or_404(db, env_id, current_user)
    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法生成变体")

    payload = await read_json_payload(request)

    try:
        base_fallback = env.reference_images[0] if env.reference_images else None
        req = resolve_environment_image_variant_request(
            payload,
            base_image=params.base_image,
            fallback_base_image=base_fallback,
            prompt=params.prompt,
            model=params.model,
            count=params.count,
            size=params.size,
            aspect_ratio=params.aspect_ratio,
        )
        if not req.base_image:
            raise HTTPException(status_code=400, detail="缺少基准图像")
        saved = await generate_environment_image_variants_service(
            db=db,
            env=env,
            request=req,
            ai_service=ai_service,
            require_upload=bool(oss_service),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"success": True, "data": {"images": saved, "count": len(saved)}}


@router.post("/environments/{env_id}/images/variants-async")
async def generate_environment_image_variants_async(
    env_id: str,
    request: Request,
    params: EnvironmentImageVariantParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Async environment image-to-image: create Task and delegate to Celery."""
    env = get_owned_environment_or_404(db, env_id, current_user)
    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法生成变体")

    body = await read_json_payload(request)

    base_fallback = env.reference_images[0] if env.reference_images else None
    req = resolve_environment_image_variant_request(
        body,
        base_image=params.base_image,
        fallback_base_image=base_fallback,
        prompt=params.prompt,
        model=params.model,
        count=params.count,
        size=params.size,
        aspect_ratio=params.aspect_ratio,
    )
    if not req.base_image:
        raise HTTPException(status_code=400, detail="缺少基准图像")

    payload = build_environment_variant_task_payload(env_id=env.id, request=req)

    task = Task(
        title=f"环境图生图 - 环境{env_id}",
        description="异步生成环境图像变体",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=compose_environment_prompt(env, req.prompt),
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    environment_image_variant_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
