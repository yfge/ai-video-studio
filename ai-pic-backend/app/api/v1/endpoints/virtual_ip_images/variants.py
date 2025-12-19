"""
Virtual IP Images variant generation endpoints.

Image-to-image variant generation for virtual IP images.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate, VirtualIPImageResponse
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.task_worker import virtual_ip_image_variant_task
from app.utils.model_utils import infer_provider_from_model
from .helpers import (
    get_owned_virtual_ip,
    get_virtual_ip_image,
    normalize_reference_images,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate variant from existing virtual IP image (sync path)."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    base_image = get_virtual_ip_image(db, virtual_ip, image_id, None)

    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    prompt_value = (
        payload.get("prompt", prompt)
        or "为当前角色生成不同视角/姿态的图像，如背面照或全身照"
    )
    raw_model = payload.get("model", model)
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    aspect_ratio_value = payload.get("aspect_ratio", aspect_ratio)
    style_hint = payload.get("style") or "realistic"
    style_preset_id = payload.get("style_preset_id")
    style_spec = payload.get("style_spec")
    reference_images_value = payload.get("reference_images") or []
    selected_model = (
        payload.get("model_id") or model_id or raw_model or base_image.ai_model or ""
    ).strip()

    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    # Build image URL: prefer OSS, fallback to local
    if base_image.oss_url:
        image_url = base_image.oss_url
    else:
        file_path = base_image.file_path or ""
        if file_path and not file_path.startswith("/"):
            file_path = "/" + file_path
        backend_base = (
            getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
        ).rstrip("/")
        image_url = f"{backend_base}{file_path}"

    prefer_provider = infer_provider_from_model(selected_model or "")

    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法执行图生图")

    # Normalize reference images
    reference_images_iter: list[str]
    if isinstance(reference_images_value, str):
        reference_images_iter = [reference_images_value]
    elif isinstance(reference_images_value, list):
        reference_images_iter = [
            u for u in reference_images_value if isinstance(u, str)
        ]
    else:
        reference_images_iter = []

    backend_base = (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")
    extra_images: list[str] = normalize_reference_images(
        reference_images_iter, backend_base
    )

    try:
        response = await ai_service.ai_manager.image_to_image(
            image_url=image_url,
            prompt=prompt_value,
            model=selected_model or None,
            prefer_provider=prefer_provider,
            count=count_int,
            size=size_value,
            aspect_ratio=aspect_ratio_value,
            style=style_hint,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            extra_images=extra_images,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"图生图调用失败: {exc}") from exc

    if not response.success:
        raise HTTPException(status_code=500, detail=response.error or "图生图生成失败")

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise HTTPException(status_code=500, detail="图生图接口未返回任何图像")

    generation_params = dict(response.usage or {})
    if isinstance(response.metadata, dict):
        if response.metadata.get("style_spec") is not None:
            generation_params["style_spec"] = response.metadata.get("style_spec")
        if response.metadata.get("style_spec_resolution") is not None:
            generation_params["style_spec_resolution"] = response.metadata.get(
                "style_spec_resolution"
            )
    if size_value is not None:
        generation_params["size"] = size_value
    if aspect_ratio_value is not None:
        generation_params["aspect_ratio"] = aspect_ratio_value

    created_images: list[VirtualIPImage] = []

    for idx, variant_url in enumerate(images):
        # Persist via AIService._persist_generated_image
        try:
            stored = await ai_service._persist_generated_image(
                image_data=variant_url,
                ip_name=virtual_ip.name,
                category=base_image.category or "portrait",
                prefix="ai-generated/virtual-ip",
                metadata={
                    "virtual_ip_id": virtual_ip.id,
                    "base_image_id": base_image.id,
                    "prompt": prompt_value,
                    "provider": response.provider,
                    "model": selected_model or response.model,
                },
                require_upload=bool(oss_service),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"图生图文件保存失败: {exc}"
            ) from exc

        local_file_path = stored.get("local_file_path")
        if not local_file_path or not os.path.exists(local_file_path):
            raise HTTPException(status_code=500, detail="图生图文件下载失败")

        file_size = stored.get("file_size") or os.path.getsize(local_file_path)
        filename = stored.get("filename") or os.path.basename(local_file_path)
        relative_path = stored.get("relative_path") or f"/uploads/{filename}"
        oss_result = stored.get("oss_upload")
        oss_url = stored.get("oss_url")

        tags = [
            base_image.category or "portrait",
            "ai_generated",
            "variant",
        ]

        image_data = VirtualIPImageCreate(
            virtual_ip_id=virtual_ip.id,
            file_path=relative_path,
            oss_url=oss_url,
            filename=filename,
            original_filename=(
                f"{virtual_ip.name}_{base_image.category or 'variant'}_img2img_{idx + 1}.png"
            ),
            file_size=file_size,
            mime_type="image/png",
            category=base_image.category or "portrait",
            tags=tags,
            prompt=prompt_value,
            ai_model=selected_model or response.model,
            generation_params=generation_params,
            is_default=False,
            metadata={
                "generation_method": "image_to_image",
                "provider": response.provider,
                "model": response.model,
                "base_image_id": base_image.id,
                "base_image_url": image_url,
                "variant_url": variant_url,
                "oss_upload": oss_result,
            },
        )

        db_image = VirtualIPImage(
            **image_data.dict(), virtual_ip_business_id=virtual_ip.business_id
        )
        db.add(db_image)
        created_images.append(db_image)

    db.commit()
    for img in created_images:
        db.refresh(img)

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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate variant asynchronously via Celery."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    base_image = get_virtual_ip_image(db, virtual_ip, image_id, None)

    payload_body: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload_body = await request.json()
        except Exception:
            payload_body = {}

    prompt_value = (
        payload_body.get("prompt", prompt)
        or "为当前角色生成不同视角/姿态的图像，如背面照或全身照"
    )
    raw_model = payload_body.get("model", model)
    count_value = payload_body.get("count", count)
    size_value = payload_body.get("size", size)
    aspect_ratio_value = payload_body.get("aspect_ratio", aspect_ratio)
    reference_images_value = payload_body.get("reference_images") or []
    style_hint = payload_body.get("style") or "realistic"
    style_preset_id = payload_body.get("style_preset_id")
    style_spec = payload_body.get("style_spec")

    # DEBUG logging
    logger.warning(
        f"[DEBUG] 虚拟IP图生图异步接口收到 payload_body: {payload_body.keys()}"
    )
    logger.warning(f"[DEBUG] reference_images_value: {reference_images_value}")

    selected_model = (
        payload_body.get("model_id")
        or model_id
        or raw_model
        or base_image.ai_model
        or ""
    ).strip()

    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    # Build payload
    payload: Dict[str, Any] = {
        "virtual_ip_id": virtual_ip.id,
        "virtual_ip_business_id": virtual_ip.business_id,
        "image_id": image_id,
        "prompt": prompt_value,
        "model": selected_model,
        "count": count_int,
        "size": size_value,
        "aspect_ratio": aspect_ratio_value,
        "style": style_hint,
        "style_preset_id": style_preset_id,
        "style_spec": style_spec,
        "reference_images": reference_images_value,
    }

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
