"""
Virtual IP Images AI generation endpoints.

Text-to-image generation for virtual IP images.
"""

import json
from typing import Optional

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.virtual_ip import VirtualIPImageResponse
from app.services.ai_service import ai_service
from app.services.image_gen.coerce import coerce_str_list
from app.services.task_worker import virtual_ip_image_generate_task
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from .generation_helpers import (
    build_virtual_ip_appearance_description,
    build_virtual_ip_image_payload,
    persist_virtual_ip_image,
    read_request_payload,
    resolve_virtual_ip_image_params,
)
from .helpers import get_owned_virtual_ip

router = APIRouter()


@router.post("/{virtual_ip_id}/images/generate", response_model=VirtualIPImageResponse)
async def generate_virtual_ip_image(
    virtual_ip_id: str,
    request: Request,
    style: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    additional_prompts: Optional[str] = Form(None),
    is_default: Optional[str] = Form(None),
    count: Optional[int] = Form(None),
    size: Optional[str] = Form(None),
    aspect_ratio: Optional[str] = Form(None),
    seed: Optional[int] = Form(None),
    steps: Optional[int] = Form(None),
    cfg_scale: Optional[float] = Form(None),
    negative_prompt: Optional[str] = Form(None),
    generation_profile: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate virtual IP image using AI (sync path, kept for compatibility)."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    payload = await read_request_payload(request)
    reference_images = coerce_str_list(payload.get("reference_images") or [])
    params = resolve_virtual_ip_image_params(
        payload,
        style=style,
        category=category,
        model=model,
        model_id=model_id,
        additional_prompts=additional_prompts,
        is_default=is_default,
        count=count,
        size=size,
        aspect_ratio=aspect_ratio,
        seed=seed,
        steps=steps,
        cfg_scale=cfg_scale,
        negative_prompt=negative_prompt,
        generation_profile=generation_profile,
    )

    aggregated_description = build_virtual_ip_appearance_description(virtual_ip)
    result = await ai_service.generate_virtual_ip_image(
        ip_name=virtual_ip.name,
        description=aggregated_description,
        style=params["style"],
        style_preset_id=params.get("style_preset_id"),
        style_spec=params.get("style_spec"),
        category=params["category"],
        model=params["model"],
        additional_prompts=params.get("additional_prompts") or [],
        background_story=None,
        count=params["count"],
        size=params.get("size"),
        aspect_ratio=params.get("aspect_ratio"),
        generation_profile=params.get("generation_profile"),
        seed=params.get("seed"),
        steps=params.get("steps"),
        cfg_scale=params.get("cfg_scale"),
        negative_prompt=params.get("negative_prompt"),
        reference_images=reference_images or None,
    )
    if not result:
        raise HTTPException(status_code=500, detail="AI图像生成失败")
    db_image = persist_virtual_ip_image(db, virtual_ip, result, params)
    return VirtualIPImageResponse.from_orm(db_image)


@router.post("/{virtual_ip_id}/images/generate-async")
async def generate_virtual_ip_image_async(
    virtual_ip_id: str,
    request: Request,
    style: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    additional_prompts: Optional[str] = Form(None),
    is_default: Optional[str] = Form(None),
    count: Optional[int] = Form(None),
    size: Optional[str] = Form(None),
    aspect_ratio: Optional[str] = Form(None),
    seed: Optional[int] = Form(None),
    steps: Optional[int] = Form(None),
    cfg_scale: Optional[float] = Form(None),
    negative_prompt: Optional[str] = Form(None),
    generation_profile: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate virtual IP image asynchronously via Celery."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    payload_body = await read_request_payload(request)
    reference_images = coerce_str_list(payload_body.get("reference_images") or [])
    params = resolve_virtual_ip_image_params(
        payload_body,
        style=style,
        category=category,
        model=model,
        model_id=model_id,
        additional_prompts=additional_prompts,
        is_default=is_default,
        count=count,
        size=size,
        aspect_ratio=aspect_ratio,
        seed=seed,
        steps=steps,
        cfg_scale=cfg_scale,
        negative_prompt=negative_prompt,
        generation_profile=generation_profile,
    )
    payload = build_virtual_ip_image_payload(virtual_ip, params)
    payload["reference_images"] = reference_images or None

    # Create task
    task = Task(
        title=f"虚拟IP文生图 - {virtual_ip.name}",
        description="异步生成虚拟IP图像",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=f"VirtualIP image gen for {virtual_ip.name}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Delegate to Celery worker
    virtual_ip_image_generate_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
