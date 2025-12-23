"""
Story Structure environment image variant endpoints.

Image-to-image variant generation for environments (sync and async).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.services.task_worker import environment_image_variant_task
from app.utils.model_utils import normalize_openai_image_style, parse_model_and_provider

from .helpers import (
    compose_environment_prompt,
    download_and_attach,
    infer_provider_from_model,
    normalize_reference_images,
    resolve_image_aspect_ratio,
    resolve_environment_url,
)

router = APIRouter()


@router.post("/environments/{env_id}/images/variants")
async def generate_environment_image_variants(
    env_id: str,
    request: Request,
    base_image: Optional[str] = Query(None, description="基准图 URL 或相对路径"),
    prompt: Optional[str] = Query(None, description="变体提示词"),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸"),
    aspect_ratio: Optional[str] = Query(
        None, description="画幅比例，如 16:9、1:1"
    ),
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
    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法生成变体")

    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    base = payload.get("base_image", base_image) or (
        env.reference_images[0] if env.reference_images else None
    )
    if not base:
        raise HTTPException(status_code=400, detail="缺少基准图像")

    backend_base = (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")
    image_url = resolve_environment_url(base, backend_base)

    model_raw = (payload.get("model") or model or "").strip() or None
    model_value, provider_from_model = parse_model_and_provider(model_raw)
    prefer_provider = provider_from_model or infer_provider_from_model(
        model_value or ""
    )
    style_hint = payload.get("style") or "realistic"
    style_preset_id = payload.get("style_preset_id")
    style_spec = payload.get("style_spec")
    if (prefer_provider or "").lower() == "openai":
        style_hint = normalize_openai_image_style(style_hint)
    extra_prompt = payload.get("prompt", prompt)
    reference_images_value = payload.get("reference_images") or []
    prompt_value = compose_environment_prompt(
        env,
        extra_prompt
        or "Generate stylistically consistent variants based on this environment reference",
    )
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    aspect_ratio_value = payload.get("aspect_ratio", aspect_ratio)
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    count_int = max(1, min(count_int, 4))

    reference_images_iter: list[str]
    if isinstance(reference_images_value, str):
        reference_images_iter = [reference_images_value]
    elif isinstance(reference_images_value, list):
        reference_images_iter = [
            u for u in reference_images_value if isinstance(u, str)
        ]
    else:
        reference_images_iter = []

    extra_images: list[str] = normalize_reference_images(
        reference_images_iter, backend_base
    )

    aspect_ratio_value = resolve_image_aspect_ratio(
        prefer_provider, model_value, aspect_ratio_value
    )
    try:
        response = await ai_service.ai_manager.image_to_image(
            image_url=image_url,
            prompt=prompt_value,
            model=model_value,
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
        raise HTTPException(
            status_code=500, detail=f"环境图生图调用失败: {exc}"
        ) from exc

    if not response.success:
        raise HTTPException(
            status_code=500, detail=response.error or "环境图生图生成失败"
        )

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise HTTPException(status_code=500, detail="环境图生图接口未返回任何图像")

    try:
        saved = await download_and_attach(db, env, images)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"环境图像保存失败: {exc}") from exc
    response_meta = getattr(response, "metadata", None)
    if not isinstance(response_meta, dict):
        response_meta = {}
    extra = dict(env.extra_metadata or {})
    extra["last_image_to_image_generation"] = {
        "generated_at": datetime.utcnow().isoformat(),
        "style": style_hint,
        "style_preset_id": (style_preset_id or "").strip() or None,
        "style_spec": response_meta.get("style_spec"),
        "style_spec_resolution": response_meta.get("style_spec_resolution"),
        "provider": response.provider,
        "model": response.model,
        "count": len(saved),
    }
    env.extra_metadata = extra
    db.commit()
    db.refresh(env)
    return {"success": True, "data": {"images": saved, "count": len(saved)}}


@router.post("/environments/{env_id}/images/variants-async")
async def generate_environment_image_variants_async(
    env_id: str,
    request: Request,
    base_image: Optional[str] = Query(None, description="基准图 URL 或相对路径"),
    prompt: Optional[str] = Query(None, description="变体提示词"),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸"),
    aspect_ratio: Optional[str] = Query(
        None, description="画幅比例，如 16:9、1:1"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Async environment image-to-image: create Task and delegate to Celery."""
    env = svc.resolve_environment(db, env_id)
    if env and not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        env = None
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法生成变体")

    body: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()
        except Exception:
            body = {}

    base = body.get("base_image", base_image) or (
        env.reference_images[0] if env.reference_images else None
    )
    if not base:
        raise HTTPException(status_code=400, detail="缺少基准图像")

    model_raw = (body.get("model") or model or "").strip() or None
    count_value = body.get("count", count)
    size_value = body.get("size", size)
    aspect_ratio_value = body.get("aspect_ratio", aspect_ratio)
    style_hint = body.get("style") or "realistic"
    style_preset_id = body.get("style_preset_id")
    style_spec = body.get("style_spec")
    extra_prompt = body.get("prompt", prompt)
    reference_images_value = body.get("reference_images") or []
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    count_int = max(1, min(count_int, 4))

    payload = {
        "env_id": env_id,
        "base_image": base,
        "model": model_raw,
        "count": count_int,
        "size": size_value,
        "aspect_ratio": aspect_ratio_value,
        "style": style_hint,
        "style_preset_id": style_preset_id,
        "style_spec": style_spec,
        "prompt": extra_prompt,
        "reference_images": reference_images_value,
    }

    task = Task(
        title=f"环境图生图 - 环境{env_id}",
        description="异步生成环境图像变体",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=compose_environment_prompt(env, extra_prompt),
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    environment_image_variant_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
