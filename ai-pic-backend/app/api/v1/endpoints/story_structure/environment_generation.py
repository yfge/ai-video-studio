"""
Story Structure environment image generation endpoints.

Text-to-image generation for environments (sync and async).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.story_structure import EnvironmentResponse
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.services.task_worker import environment_image_generate_task
from app.utils.model_utils import normalize_openai_image_style, parse_model_and_provider

from .helpers import (
    compose_environment_prompt,
    download_and_attach,
    infer_provider_from_model,
    resolve_image_aspect_ratio,
    sanitize_environment_style,
    strip_provider_prefix,
)

router = APIRouter()


@router.post("/environments/{env_id}/images/generate")
async def generate_environment_images(
    env_id: str,
    request: Request,
    prompt: Optional[str] = Query(
        None, description="生成提示词，不填则用环境描述/名称"
    ),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸，如 1024x1024 或 2K"),
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
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法生成环境图")

    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    prefer_provider: Optional[str] = None
    extra_prompt = payload.get("prompt", prompt)
    selected_model_raw = (payload.get("model") or model or "").strip() or None
    selected_model, prefer_provider_from_model = parse_model_and_provider(
        selected_model_raw
    )
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    aspect_ratio_value = payload.get("aspect_ratio", aspect_ratio)
    style_hint, style_preset_id, style_spec = sanitize_environment_style(
        payload.get("style"),
        payload.get("style_preset_id"),
        payload.get("style_spec"),
    )
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    count_int = max(1, min(count_int, 4))

    prefer_provider = prefer_provider or prefer_provider_from_model
    prefer_provider = prefer_provider or infer_provider_from_model(
        selected_model or ""
    )
    if (prefer_provider or "").lower() == "openai":
        style_hint = normalize_openai_image_style(style_hint)

    aspect_ratio_value = resolve_image_aspect_ratio(
        prefer_provider, strip_provider_prefix(selected_model), aspect_ratio_value
    )
    final_prompt = compose_environment_prompt(env, extra_prompt)

    try:
        response = await ai_service.ai_manager.generate_image(
            prompt=final_prompt,
            model=strip_provider_prefix(selected_model),
            n=count_int,
            size=size_value,
            aspect_ratio=aspect_ratio_value,
            prefer_provider=prefer_provider,
            style=style_hint,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"环境文生图调用失败: {exc}"
        ) from exc

    if not response.success:
        raise HTTPException(
            status_code=500, detail=response.error or "环境文生图生成失败"
        )

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise HTTPException(status_code=500, detail="环境文生图接口未返回任何图像")

    try:
        saved = await download_and_attach(db, env, images)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"环境图像保存失败: {exc}") from exc
    response_meta = getattr(response, "metadata", None)
    if not isinstance(response_meta, dict):
        response_meta = {}
    extra = dict(env.extra_metadata or {})
    extra["last_text_to_image_generation"] = {
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


@router.post("/environments/{env_id}/images/generate-async")
async def generate_environment_images_async(
    env_id: str,
    request: Request,
    prompt: Optional[str] = Query(
        None, description="生成提示词，不填则用环境描述/名称"
    ),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸，如 1024x1024 或 2K"),
    aspect_ratio: Optional[str] = Query(
        None, description="画幅比例，如 16:9、1:1"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Async environment text-to-image: create Task and delegate to Celery."""
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
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法生成环境图")

    body: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()
        except Exception:
            body = {}

    extra_prompt = body.get("prompt", prompt)
    selected_model_raw = (body.get("model") or model or "").strip() or None
    count_value = body.get("count", count)
    size_value = body.get("size", size)
    aspect_ratio_value = body.get("aspect_ratio", aspect_ratio)
    style_hint, style_preset_id, style_spec = sanitize_environment_style(
        body.get("style"),
        body.get("style_preset_id"),
        body.get("style_spec"),
    )
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    count_int = max(1, min(count_int, 4))

    payload = {
        "env_id": env.id,
        "extra_prompt": extra_prompt,
        "model": selected_model_raw,
        "count": count_int,
        "size": size_value,
        "aspect_ratio": aspect_ratio_value,
        "style": style_hint,
        "style_preset_id": style_preset_id,
        "style_spec": style_spec,
    }

    task = Task(
        title=f"环境文生图 - 环境{env_id}",
        description="异步生成环境图像",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=compose_environment_prompt(env, extra_prompt),
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    environment_image_generate_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
