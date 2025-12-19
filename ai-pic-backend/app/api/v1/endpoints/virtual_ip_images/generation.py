"""
Virtual IP Images AI generation endpoints.

Text-to-image generation for virtual IP images.
"""

import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate, VirtualIPImageResponse
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.task_worker import virtual_ip_image_generate_task
from .helpers import not_deleted, get_owned_virtual_ip, set_ip_default_avatar

router = APIRouter()


def build_virtual_ip_image_payload(
    virtual_ip_id: int,
    style: Optional[str],
    style_preset_id: Optional[str],
    style_spec: Optional[Dict[str, Any]],
    category: Optional[str],
    model: Optional[str],
    count: Optional[int],
    size: Optional[str],
    aspect_ratio: Optional[str],
    additional_prompts: Optional[str],
    is_default: Optional[str] | Optional[bool],
    current_user: User,
    db: Session,
) -> Dict[str, Any]:
    """Build task payload from frontend parameters for Celery worker."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)

    style_value = style or "realistic"
    category_value = category or "portrait"
    raw_model = model
    selected_model = (raw_model or "dalle-3").strip()
    if not selected_model:
        selected_model = "dalle-3"

    try:
        count_int = int(count) if count is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    additional_prompt_list = [
        p.strip() for p in (additional_prompts or "").split(",") if p.strip()
    ]

    is_default_bool = False
    if isinstance(is_default, bool):
        is_default_bool = is_default
    elif isinstance(is_default, str):
        is_default_bool = is_default.lower() in {"true", "1", "yes", "on"}

    # Aggregate character descriptions from virtual IP fields
    description_parts = []
    if virtual_ip.description:
        description_parts.append(f"角色简介：{virtual_ip.description}")
    if getattr(virtual_ip, "background_story", None):
        description_parts.append(f"背景故事：{virtual_ip.background_story}")
    if getattr(virtual_ip, "biography", None):
        description_parts.append(f"人物小传：{virtual_ip.biography}")
    if getattr(virtual_ip, "style_prompt", None):
        description_parts.append(f"风格设定：{virtual_ip.style_prompt}")
    aggregated_description = "；".join(description_parts) or (
        virtual_ip.description or ""
    )

    return {
        "virtual_ip_id": virtual_ip_id,
        "virtual_ip_business_id": getattr(virtual_ip, "business_id", None),
        "virtual_ip_name": virtual_ip.name,
        "aggregated_description": aggregated_description,
        "style": style_value,
        "style_preset_id": (style_preset_id or "").strip() or None,
        "style_spec": style_spec,
        "category": category_value,
        "model": selected_model,
        "count": count_int,
        "size": size,
        "aspect_ratio": aspect_ratio,
        "additional_prompts": additional_prompt_list,
        "is_default": is_default_bool,
    }


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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate virtual IP image using AI (sync path, kept for compatibility)."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    virtual_ip_id_int = virtual_ip.id

    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    style = payload.get("style", style) or "realistic"
    style_preset_id = payload.get("style_preset_id")
    style_spec = payload.get("style_spec")
    category = payload.get("category", category) or "portrait"
    raw_model = payload.get("model", model)
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    aspect_ratio_value = payload.get("aspect_ratio", aspect_ratio)
    additional_prompts_value = (
        payload.get("additional_prompts", additional_prompts) or ""
    )
    is_default_value = payload.get("is_default", is_default)
    selected_model = (
        payload.get("model_id") or model_id or raw_model or "dalle-3"
    ).strip()
    if not selected_model:
        selected_model = "dalle-3"

    additional_prompt_list = [
        p.strip() for p in additional_prompts_value.split(",") if p.strip()
    ]

    is_default_bool = False
    if isinstance(is_default_value, bool):
        is_default_bool = is_default_value
    elif isinstance(is_default_value, str):
        is_default_bool = is_default_value.lower() in {"true", "1", "yes", "on"}

    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    # Log parameters for debugging
    try:
        from app.core.logging import get_logger
        get_logger().info(
            "VirtualIP image gen | ip=%s model=%s style=%s category=%s prompts=%s",
            virtual_ip_id,
            selected_model,
            style,
            category,
            additional_prompts_value,
        )
    except Exception:
        pass

    # Aggregate character descriptions
    description_parts = []
    if virtual_ip.description:
        description_parts.append(f"角色简介：{virtual_ip.description}")
    if getattr(virtual_ip, "background_story", None):
        description_parts.append(f"背景故事：{virtual_ip.background_story}")
    if getattr(virtual_ip, "biography", None):
        description_parts.append(f"人物小传：{virtual_ip.biography}")
    if getattr(virtual_ip, "style_prompt", None):
        description_parts.append(f"风格设定：{virtual_ip.style_prompt}")
    aggregated_description = "；".join(description_parts) or (
        virtual_ip.description or ""
    )

    result = await ai_service.generate_virtual_ip_image(
        ip_name=virtual_ip.name,
        description=aggregated_description,
        style=style,
        style_preset_id=style_preset_id,
        style_spec=style_spec,
        category=category,
        model=selected_model,
        additional_prompts=additional_prompt_list,
        background_story=getattr(virtual_ip, "background_story", None),
        count=count_int,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI图像生成失败")

    # Clear other default images if setting as default
    if is_default_bool:
        not_deleted(db.query(VirtualIPImage), VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id_int,
            VirtualIPImage.is_default.is_(True),
        ).update({"is_default": False})

    # Build tags
    tags = [style, category, "ai_generated", result["generation_method"]]
    if additional_prompt_list:
        tags.extend(additional_prompt_list)

    # Verify local file
    local_file_path = result.get("local_file_path")
    if not local_file_path or not os.path.exists(local_file_path):
        raise HTTPException(status_code=500, detail="图像文件生成失败")

    file_size = os.path.getsize(local_file_path)
    filename = os.path.basename(local_file_path)
    relative_path = result.get("relative_path") or f"/uploads/{filename}"
    oss_url = result.get("oss_url") or result.get("oss_upload", {}).get("file_url")

    generation_params = dict(result.get("usage") or {})
    if result.get("style_preset_id") is not None:
        generation_params["style_preset_id"] = result.get("style_preset_id")
    if result.get("style_spec") is not None:
        generation_params["style_spec"] = result.get("style_spec")
    if result.get("style_spec_resolution") is not None:
        generation_params["style_spec_resolution"] = result.get("style_spec_resolution")
    if size_value is not None:
        generation_params["size"] = size_value
    if aspect_ratio_value is not None:
        generation_params["aspect_ratio"] = aspect_ratio_value

    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id_int,
        file_path=relative_path,
        oss_url=oss_url,
        filename=filename,
        original_filename=f"{virtual_ip.name}_{category}_generated.png",
        file_size=file_size,
        mime_type="image/png",
        category=category,
        tags=tags,
        prompt=result["prompt"],
        ai_model=result["model_used"],
        generation_params=generation_params,
        is_default=is_default_bool,
        metadata={
            "generation_method": result["generation_method"],
            "prompt": result["prompt"],
            "style": result["style"],
            "additional_prompts": additional_prompt_list,
            "original_openai_url": result.get("original_image_url", ""),
            "local_file_path": local_file_path,
            "oss_upload": result.get("oss_upload"),
        },
    )

    db_image = VirtualIPImage(
        **image_data.dict(), virtual_ip_business_id=virtual_ip.business_id
    )
    db.add(db_image)
    if is_default_bool:
        set_ip_default_avatar(db, virtual_ip.id, db_image)
    db.commit()
    db.refresh(db_image)

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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate virtual IP image asynchronously via Celery."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    virtual_ip_id_int = virtual_ip.id

    payload_body: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload_body = await request.json()
        except Exception:
            payload_body = {}

    style = payload_body.get("style", style)
    style_preset_id = payload_body.get("style_preset_id")
    style_spec = payload_body.get("style_spec")
    category = payload_body.get("category", category)
    raw_model = payload_body.get("model", model)
    count_value = payload_body.get("count", count)
    size_value = payload_body.get("size", size)
    aspect_ratio_value = payload_body.get("aspect_ratio", aspect_ratio)
    additional_prompts_value = (
        payload_body.get("additional_prompts", additional_prompts) or ""
    )
    is_default_value = payload_body.get("is_default", is_default)
    selected_model = (
        payload_body.get("model_id") or model_id or raw_model or "dalle-3"
    ).strip()

    # Build payload for worker
    payload = build_virtual_ip_image_payload(
        virtual_ip_id=virtual_ip_id_int,
        style=style,
        style_preset_id=style_preset_id,
        style_spec=style_spec,
        category=category,
        model=selected_model,
        count=count_value,
        size=size_value,
        aspect_ratio=aspect_ratio_value,
        additional_prompts=additional_prompts_value,
        is_default=is_default_value,
        current_user=current_user,
        db=db,
    )

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
