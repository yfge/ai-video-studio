"""
Virtual IP Images variant generation endpoints.

Image-to-image variant generation for virtual IP images.
"""

import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.virtual_ip import VirtualIPImageResponse
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.task_worker import virtual_ip_image_variant_task
from app.services.virtual_ip.image_variant_requests import (
    build_virtual_ip_variant_task_payload,
    resolve_virtual_ip_variant_request,
)
from app.services.virtual_ip.image_variant_service import (
    generate_virtual_ip_image_variants,
)
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from .generation_helpers import read_request_payload
from .helpers import get_owned_virtual_ip, get_virtual_ip_image

router = APIRouter()


def _get_backend_base() -> str:
    return (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")


@router.post(
    "/{virtual_ip_id}/images/{image_id}/variants",
    response_model=List[VirtualIPImageResponse],
)
async def generate_virtual_ip_image_variant(
    virtual_ip_id: str,
    image_id: int,
    request: Request,
    prompt: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    count: Optional[int] = Form(1),
    size: Optional[str] = Form(None),
    aspect_ratio: Optional[str] = Form(None),
    generation_profile: Optional[str] = Form(None),
    seed: Optional[int] = Form(None),
    steps: Optional[int] = Form(None),
    cfg_scale: Optional[float] = Form(None),
    negative_prompt: Optional[str] = Form(None),
    strength: Optional[float] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate variant from existing virtual IP image (sync path)."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    base_image = get_virtual_ip_image(db, virtual_ip, image_id, None)

    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法执行图生图")

    try:
        payload = await read_request_payload(request)
        variant_request = resolve_virtual_ip_variant_request(
            payload,
            prompt=prompt,
            model=model,
            model_id=model_id,
            count=count,
            size=size,
            aspect_ratio=aspect_ratio,
            generation_profile=generation_profile,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale,
            negative_prompt=negative_prompt,
            strength=strength,
            base_image_model=base_image.ai_model,
        )
        created_images = await generate_virtual_ip_image_variants(
            db=db,
            virtual_ip=virtual_ip,
            base_image=base_image,
            request=variant_request,
            backend_base=_get_backend_base(),
            ai_service=ai_service,
            require_upload=bool(oss_service),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [VirtualIPImageResponse.from_orm(img) for img in created_images]


@router.post("/{virtual_ip_id}/images/{image_id}/variants-async")
async def generate_virtual_ip_image_variant_async(
    virtual_ip_id: str,
    image_id: int,
    request: Request,
    prompt: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    count: Optional[int] = Form(1),
    size: Optional[str] = Form(None),
    aspect_ratio: Optional[str] = Form(None),
    generation_profile: Optional[str] = Form(None),
    seed: Optional[int] = Form(None),
    steps: Optional[int] = Form(None),
    cfg_scale: Optional[float] = Form(None),
    negative_prompt: Optional[str] = Form(None),
    strength: Optional[float] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate variant asynchronously via Celery."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    base_image = get_virtual_ip_image(db, virtual_ip, image_id, None)

    payload_body = await read_request_payload(request)
    variant_request = resolve_virtual_ip_variant_request(
        payload_body,
        prompt=prompt,
        model=model,
        model_id=model_id,
        count=count,
        size=size,
        aspect_ratio=aspect_ratio,
        generation_profile=generation_profile,
        seed=seed,
        steps=steps,
        cfg_scale=cfg_scale,
        negative_prompt=negative_prompt,
        strength=strength,
        base_image_model=base_image.ai_model,
    )
    payload: Dict[str, Any] = build_virtual_ip_variant_task_payload(
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        image_id=image_id,
        request=variant_request,
    )

    # Create task
    task = Task(
        title=f"虚拟IP图生图 - 图像{image_id}",
        description="异步生成虚拟IP图像变体",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=f"VirtualIP img2img for image {image_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    virtual_ip_image_variant_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
