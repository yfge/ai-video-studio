from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.story_structure import Environment
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.task_worker import (
    environment_image_generate_task,
    environment_image_variant_task,
)
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.story_structure import (
    EnvironmentCreate,
    EnvironmentImageResponse,
    EnvironmentImagesResponse,
    EnvironmentResponse,
    EnvironmentSummaryResponse,
    EnvironmentUpdate,
    SceneBeatCreate,
    SceneBeatResponse,
    SceneBeatUpdate,
    SceneCreate,
    SceneResponse,
    SceneUpdate,
    SceneWithChildren,
    ScriptStructureResponse,
    ShotCreate,
    ShotResponse,
    ShotUpdate,
    StoryStepOutlineCreate,
    StoryStepOutlineResponse,
    StoryTreatmentCreate,
    StoryTreatmentResponse,
)
from app.core.config import settings
from app.utils.model_utils import parse_model_and_provider, normalize_openai_image_style


router = APIRouter()
logger = logging.getLogger(__name__)


def _sanitize_environment_style_spec(_: Optional[dict]) -> Optional[dict]:
    """环境生成不再透传 style_spec，避免角色/镜头风格干扰环境结果。"""
    return None


def _sanitize_environment_style(
    style: Optional[str], style_preset_id: Optional[str], style_spec: Optional[dict]
) -> tuple[str, None, None]:
    """
    环境图不使用 style_preset/style_spec，防止角色风格干扰。
    仅保留 style 作为轻量提示，缺省回落 realistic。
    """
    style_clean = style or "realistic"
    return style_clean, None, None


def _normalize_reference_images(refs: list[str], backend_base: str) -> list[str]:
    """过滤有效参考图 URL，避免将描述性字符串当作图片路径。"""
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")
    normalized: list[str] = []
    for raw in refs:
        if not isinstance(raw, str):
            continue
        ref_url = raw.strip()
        if not ref_url:
            continue
        lower = ref_url.lower()
        base_path = lower.split("?", 1)[0]
        if lower.startswith(("http://", "https://", "data:image/")):
            normalized.append(ref_url)
        elif base_path.endswith(allowed_ext):
            path = ref_url if ref_url.startswith("/") else f"/{ref_url}"
            normalized.append(f"{backend_base}{path}")
    return normalized


@router.get("/scripts/{script_id}/scenes", response_model=List[SceneResponse])
async def list_scenes_for_script(
    script_id: int,
    db: Session = Depends(get_db),
):
    return [
        SceneResponse.model_validate(s)
        for s in svc.list_scenes_by_script(db, script_id)
    ]


@router.get("/scenes/{scene_id}/beats", response_model=List[SceneBeatResponse])
async def list_beats_for_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    return [
        SceneBeatResponse.model_validate(b)
        for b in svc.list_beats_by_scene(db, scene_id)
    ]


@router.post("/scenes/{scene_id}/beats", response_model=SceneBeatResponse)
async def create_beat_for_scene(
    scene_id: int,
    body: SceneBeatCreate,
    db: Session = Depends(get_db),
):
    if body.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch")
    try:
        obj = svc.create_scene_beat(db, body)
    except ValueError as exc:
        if str(exc) == "duplicate_order_index":
            raise HTTPException(
                status_code=400,
                detail="order_index already exists for scene",
            )
        raise
    return SceneBeatResponse.model_validate(obj)


@router.get("/scenes/{scene_id}/shots", response_model=List[ShotResponse])
async def list_shots_for_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    return [
        ShotResponse.model_validate(sh) for sh in svc.list_shots_by_scene(db, scene_id)
    ]


@router.get("/scripts/{script_id}/structure", response_model=ScriptStructureResponse)
async def get_script_structure(
    script_id: int,
    db: Session = Depends(get_db),
):
    aggregated = svc.get_script_structure(db, script_id)
    if aggregated is None:
        raise HTTPException(status_code=404, detail="script not found")

    scenes_payload = []
    for item in aggregated:
        scene_dict = SceneResponse.model_validate(item["scene"]).model_dump()
        scene_dict["beats"] = [
            SceneBeatResponse.model_validate(b).model_dump()
            for b in item.get("beats", [])
        ]
        scene_dict["shots"] = [
            ShotResponse.model_validate(sh).model_dump() for sh in item.get("shots", [])
        ]
        scenes_payload.append(SceneWithChildren.model_validate(scene_dict))

    return ScriptStructureResponse(script_id=script_id, scenes=scenes_payload)


@router.post("/scripts/{script_id}/scenes", response_model=SceneResponse)
async def create_scene_for_script(
    script_id: int,
    body: SceneCreate,
    db: Session = Depends(get_db),
):
    if body.script_id != script_id:
        raise HTTPException(status_code=400, detail="script_id mismatch")
    try:
        obj = svc.create_scene(db, body)
    except ValueError as exc:
        if str(exc) == "script_not_found":
            raise HTTPException(status_code=404, detail="script not found")
        if str(exc) == "environment_not_found":
            raise HTTPException(status_code=404, detail="environment not found")
        raise
    return SceneResponse.model_validate(obj)


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: int,
    body: SceneUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = svc.update_scene(db, scene_id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        if str(exc) == "environment_not_found":
            raise HTTPException(status_code=404, detail="environment not found")
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="scene not found")
    return SceneResponse.model_validate(obj)


@router.delete("/scenes/{scene_id}", status_code=204)
async def delete_scene(scene_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_scene(db, scene_id)
    if not ok:
        raise HTTPException(status_code=404, detail="scene not found")
    return None


@router.post("/scenes/{scene_id}/shots", response_model=ShotResponse)
async def create_shot_for_scene(
    scene_id: int,
    body: ShotCreate,
    db: Session = Depends(get_db),
):
    if body.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch")
    try:
        obj = svc.create_shot(db, body)
    except ValueError as exc:
        msg = str(exc)
        if msg == "scene_not_found":
            raise HTTPException(status_code=404, detail="scene not found")
        if msg == "duplicate_shot_number":
            raise HTTPException(
                status_code=400, detail="shot_number already exists for scene"
            )
        if msg == "beat_scene_mismatch":
            raise HTTPException(status_code=400, detail="beat does not belong to scene")
        raise
    return ShotResponse.model_validate(obj)


@router.put("/shots/{shot_id}", response_model=ShotResponse)
async def update_shot(
    shot_id: int,
    body: ShotUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = svc.update_shot(db, shot_id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        msg = str(exc)
        if msg == "duplicate_shot_number":
            raise HTTPException(
                status_code=400, detail="shot_number already exists for scene"
            )
        if msg == "beat_scene_mismatch":
            raise HTTPException(status_code=400, detail="beat does not belong to scene")
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="shot not found")
    return ShotResponse.model_validate(obj)


@router.delete("/shots/{shot_id}", status_code=204)
async def delete_shot(shot_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_shot(db, shot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="shot not found")
    return None


# Environment management


@router.get("/environments", response_model=List[EnvironmentSummaryResponse])
async def list_environments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    items = svc.list_environments(
        db,
        owner_id=(
            None
            if current_user.is_admin or current_user.is_superuser
            else current_user.id
        ),
    )
    return [EnvironmentSummaryResponse.model_validate(it) for it in items]


@router.get("/environments/{env_id}", response_model=EnvironmentResponse)
async def get_environment(
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
    return EnvironmentResponse.model_validate(env)


@router.post("/environments", response_model=EnvironmentResponse)
async def create_environment(
    body: EnvironmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    payload = body.model_dump(exclude_none=True)
    payload["user_id"] = current_user.id
    env = svc.create_environment(db, payload)
    return EnvironmentResponse.model_validate(env)


@router.put("/environments/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: str,
    body: EnvironmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if not env or not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        raise HTTPException(status_code=404, detail="environment not found")
    env = svc.update_environment(db, env_id, body.model_dump(exclude_none=True))
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    return EnvironmentResponse.model_validate(env)


@router.delete("/environments/{env_id}", status_code=204)
async def delete_environment(
    env_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    env = svc.resolve_environment(db, env_id)
    if not env or not (
        current_user.is_admin
        or current_user.is_superuser
        or env.user_id == current_user.id
    ):
        ok = False
    else:
        ok = svc.delete_environment(db, env_id)
    if not ok:
        raise HTTPException(status_code=404, detail="environment not found")
    return None


# Environment images (reference-only, used as generation anchors)


def _infer_provider_from_model(model: Optional[str]) -> Optional[str]:
    if not model:
        return None
    normalized = model.lower()
    if (
        normalized.startswith(("seedream", "volcengine"))
        or "doubao" in normalized
        or "seedream" in normalized
    ):
        return "volcengine"
    if normalized.startswith("deepseek"):
        return "deepseek"
    if normalized.startswith(("keling", "kling")):
        return "keling"
    if normalized.startswith("jimeng"):
        return "jimeng"
    if normalized.startswith(("dall-e", "dalle")):
        return "openai"
    if normalized.startswith("gemini"):
        return "google"
    return None


def _strip_provider_prefix(model: Optional[str]) -> Optional[str]:
    if not model:
        return None
    return model.split(":", 1)[1] if ":" in model else model


async def _download_and_attach(db: Session, env, image_urls: List[str]) -> List[str]:
    saved: List[str] = []
    errors: List[str] = []
    for image_url in image_urls:
        try:
            stored = await ai_service._persist_generated_image(
                image_data=image_url,
                ip_name=env.name or f"environment-{env.id}",
                category="environment",
                prefix="ai-generated/environments",
                metadata={
                    "environment_id": env.id,
                    "environment_name": env.name or "",
                },
                # 若已配置 OSS/CDN，则要求上传成功；否则退回本地存储
                require_upload=bool(oss_service),
            )
        except Exception as exc:
            errors.append(f"{image_url}: {exc}")
            logger.warning(
                "环境图像持久化失败 | env_id=%s image_url=%s error=%s",
                getattr(env, "id", None),
                image_url,
                exc,
            )
            continue
        final_url = stored.get("oss_url") or stored.get("relative_path")
        if not final_url:
            errors.append(f"{image_url}: missing persisted URL")
            logger.warning(
                "环境图像未返回可用路径 | env_id=%s image_url=%s stored=%s",
                getattr(env, "id", None),
                image_url,
                stored,
            )
            continue
        saved.append(final_url)
    if not saved:
        detail = errors[0] if errors else "未找到可用的持久化结果"
        raise RuntimeError(f"环境图像持久化失败: {detail}")
    refs = env.reference_images or []
    refs.extend(saved)
    env.reference_images = refs
    # 强制持久化 JSON 列，避免未跟踪的列表修改丢失
    db.query(Environment).filter(Environment.id == env.id).update(
        {"reference_images": env.reference_images}
    )
    return saved


def _compose_environment_prompt(env, extra: Optional[str] = None) -> str:
    """Compose a richer prompt for environment generation using name/description/tags/category."""
    parts: List[str] = []
    if env.name:
        parts.append(f"Environment: {env.name}")
    if env.category:
        parts.append(f"Category: {env.category}")
    if env.tags:
        tags_str = ", ".join([t for t in env.tags if t])
        if tags_str:
            parts.append(f"Tags: {tags_str}")
    if env.description:
        parts.append(f"Description: {env.description}")
    # Default structured guidance to ensure prompt has整体->细节、室内/室外的层次
    category_hint = (
        "室内布局、光线、材质细节"
        if (env.category or "").lower() == "indoor"
        else "室外空间、天气、周边环境"
    )
    parts.append(
        f"Overall-to-detail: 开场远景交代空间 -> 中景展示主要区域 -> 近景刻画关键道具/纹理；"
        f"Environment focus: {category_hint}；保持真实光影和透视，色彩和风格统一。"
    )
    if extra:
        parts.append(extra)
    if not parts:
        return "Environment scene with clear spatial layout and lighting cues"
    return " | ".join(parts)


@router.get(
    "/environments/{env_id}/images", response_model=EnvironmentImagesResponse
)
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
    """上传环境参考图，使用统一持久化与 OSS 上传策略。"""
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
        raise HTTPException(
            status_code=500, detail=f"环境图像保存失败: {exc}"
        ) from exc

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
    style_hint, style_preset_id, style_spec = _sanitize_environment_style(
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
    prefer_provider = prefer_provider or _infer_provider_from_model(
        selected_model or ""
    )
    if (prefer_provider or "").lower() == "openai":
        style_hint = normalize_openai_image_style(style_hint)

    final_prompt = _compose_environment_prompt(env, extra_prompt)

    try:
        response = await ai_service.ai_manager.generate_image(
            prompt=final_prompt,
            model=_strip_provider_prefix(selected_model),
            n=count_int,
            size=size_value if prefer_provider == "volcengine" else None,
            prefer_provider=prefer_provider,
            style=style_hint,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
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
        saved = await _download_and_attach(db, env, images)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"环境图像保存失败: {exc}"
        ) from exc
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步环境文生图：创建 Task 并委托 Celery 处理。"""
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
    style_hint, style_preset_id, style_spec = _sanitize_environment_style(
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
        "style": style_hint,
        "style_preset_id": style_preset_id,
        "style_spec": style_spec,
    }

    task = Task(
        title=f"环境文生图 - 环境{env_id}",
        description="异步生成环境图像",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=_compose_environment_prompt(env, extra_prompt),
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    environment_image_generate_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_environment_image_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker 使用的环境文生图处理函数。"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        env = svc.get_environment(db, payload["env_id"])
        if not env:
            raise RuntimeError("environment not found")

        import anyio

        async def _run() -> list[str]:
            prefer_provider: Optional[str] = None
            selected_model_raw = (payload.get("model") or "").strip() or None
            selected_model, prefer_provider_from_model = parse_model_and_provider(
                selected_model_raw
            )
            count_int = int(payload.get("count") or 1)
            size_value = payload.get("size")
            style_hint, style_preset_id, style_spec = _sanitize_environment_style(
                payload.get("style"),
                payload.get("style_preset_id"),
                payload.get("style_spec"),
            )

            prefer_provider_local = prefer_provider or prefer_provider_from_model
            prefer_provider_local = prefer_provider_local or _infer_provider_from_model(
                selected_model or ""
            )
            if (prefer_provider_local or "").lower() == "openai":
                style_hint_local = normalize_openai_image_style(style_hint)
            else:
                style_hint_local = style_hint

            final_prompt = _compose_environment_prompt(env, payload.get("extra_prompt"))

            response = await ai_service.ai_manager.generate_image(
                prompt=final_prompt,
                model=_strip_provider_prefix(selected_model),
                n=max(1, min(count_int, 4)),
                size=size_value if prefer_provider_local == "volcengine" else None,
                prefer_provider=prefer_provider_local,
                style=style_hint_local,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
            )
            if not response.success:
                raise RuntimeError(response.error or "环境文生图生成失败")
            images = (
                response.data.get("images", [])
                if isinstance(response.data, dict)
                else []
            )
            if not images:
                raise RuntimeError("环境文生图接口未返回任何图像")

            saved_urls = await _download_and_attach(db, env, images)
            response_meta = getattr(response, "metadata", None)
            if not isinstance(response_meta, dict):
                response_meta = {}
            extra = dict(env.extra_metadata or {})
            extra["last_text_to_image_generation"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "style": style_hint_local,
                "style_preset_id": (style_preset_id or "").strip() or None,
                "style_spec": response_meta.get("style_spec"),
                "style_spec_resolution": response_meta.get("style_spec_resolution"),
                "provider": response.provider,
                "model": response.model,
                "count": len(saved_urls),
            }
            env.extra_metadata = extra
            db.commit()
            return saved_urls

        saved = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"environment_images:{payload['env_id']}:{len(saved)}"
            )
            db.commit()
    except Exception as exc:  # pragma: no cover - defensive
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.post("/environments/{env_id}/images/variants")
async def generate_environment_image_variants(
    env_id: str,
    request: Request,
    base_image: Optional[str] = Query(None, description="基准图 URL 或相对路径"),
    prompt: Optional[str] = Query(None, description="变体提示词"),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸"),
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
    if isinstance(base, str) and base.startswith("http"):
        image_url = base
    else:
        path = base if isinstance(base, str) else ""
        if path and not path.startswith("/"):
            path = "/" + path
        base = (
            getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
        ).rstrip("/")
        image_url = f"{base}{path}"

    model_raw = (payload.get("model") or model or "").strip() or None
    model_value, provider_from_model = parse_model_and_provider(model_raw)
    prefer_provider = provider_from_model or _infer_provider_from_model(
        model_value or ""
    )
    style_hint = payload.get("style") or "realistic"
    style_preset_id = payload.get("style_preset_id")
    style_spec = payload.get("style_spec")
    if (prefer_provider or "").lower() == "openai":
        style_hint = normalize_openai_image_style(style_hint)
    extra_prompt = payload.get("prompt", prompt)
    reference_images_value = payload.get("reference_images") or []
    prompt_value = _compose_environment_prompt(
        env,
        extra_prompt
        or "Generate stylistically consistent variants based on this environment reference",
    )
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
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

    backend_base = (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")
    extra_images: list[str] = _normalize_reference_images(
        reference_images_iter, backend_base
    )

    try:
        response = await ai_service.ai_manager.image_to_image(
            image_url=image_url,
            prompt=prompt_value,
            model=model_value,
            prefer_provider=prefer_provider,
            count=count_int,
            size=size_value,
            style=style_hint,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
            extra_images=extra_images,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
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
        saved = await _download_and_attach(db, env, images)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"环境图像保存失败: {exc}"
        ) from exc
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步环境图生图：创建 Task 并委托 Celery 处理。"""
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
        prompt=_compose_environment_prompt(env, extra_prompt),
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    environment_image_variant_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_environment_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """Celery worker 使用的环境图生图处理函数。"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        env = svc.get_environment(db, payload["env_id"])
        if not env:
            raise RuntimeError("environment not found")

        base = payload.get("base_image")
        if not base:
            raise RuntimeError("缺少基准图像")
        if isinstance(base, str) and base.startswith("http"):
            image_url = base
        else:
            path = base if isinstance(base, str) else ""
            if path and not path.startswith("/"):
                path = "/" + path
            backend_base = (
                getattr(settings, "INTERNAL_BACKEND_URL", None)
                or "http://localhost:8000"
            ).rstrip("/")
            image_url = f"{backend_base}{path}"

        import anyio

        async def _run() -> list[str]:
            model_raw = (payload.get("model") or "").strip() or None
            model_value, provider_from_model = parse_model_and_provider(model_raw)
            prefer_provider = provider_from_model or _infer_provider_from_model(
                model_value or ""
            )
            style_hint, style_preset_id, style_spec = _sanitize_environment_style(
                payload.get("style"),
                payload.get("style_preset_id"),
                payload.get("style_spec"),
            )
            if (prefer_provider or "").lower() == "openai":
                style_hint_local = normalize_openai_image_style(style_hint)
            else:
                style_hint_local = style_hint
            extra_prompt = payload.get("prompt")
            prompt_value = _compose_environment_prompt(
                env,
                extra_prompt
                or "Generate stylistically consistent variants based on this environment reference",
            )
            count_int = int(payload.get("count") or 1)
            size_value = payload.get("size")

            # 提取参考图并转换为绝对 URL
            reference_images = payload.get("reference_images") or []
            backend_base = (
                getattr(settings, "INTERNAL_BACKEND_URL", None)
                or "http://localhost:8000"
            ).rstrip("/")
            extra_images = _normalize_reference_images(reference_images, backend_base)

            response = await ai_service.ai_manager.image_to_image(
                image_url=image_url,
                prompt=prompt_value,
                model=model_value,
                prefer_provider=prefer_provider,
                count=max(1, min(count_int, 4)),
                size=size_value,
                style=style_hint_local,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
                extra_images=extra_images,
            )
            if not response.success:
                raise RuntimeError(response.error or "环境图生图生成失败")
            images = (
                response.data.get("images", [])
                if isinstance(response.data, dict)
                else []
            )
            if not images:
                raise RuntimeError("环境图生图接口未返回任何图像")

            saved_urls = await _download_and_attach(db, env, images)
            response_meta = getattr(response, "metadata", None)
            if not isinstance(response_meta, dict):
                response_meta = {}
            extra = dict(env.extra_metadata or {})
            extra["last_image_to_image_generation"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "style": style_hint_local,
                "style_preset_id": (style_preset_id or "").strip() or None,
                "style_spec": response_meta.get("style_spec"),
                "style_spec_resolution": response_meta.get("style_spec_resolution"),
                "provider": response.provider,
                "model": response.model,
                "count": len(saved_urls),
            }
            env.extra_metadata = extra
            db.commit()
            return saved_urls

        saved = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"environment_image_variants:{payload['env_id']}:{len(saved)}"
            )
            db.commit()
    except Exception as exc:  # pragma: no cover - defensive
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


@router.put("/scene-beats/{beat_id}", response_model=SceneBeatResponse)
async def update_scene_beat(
    beat_id: int,
    body: SceneBeatUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = svc.update_scene_beat(db, beat_id, body.model_dump(exclude_none=True))
    except ValueError as exc:
        if str(exc) == "duplicate_order_index":
            raise HTTPException(
                status_code=400, detail="order_index already exists for scene"
            )
        raise
    if not obj:
        raise HTTPException(status_code=404, detail="beat not found")
    return SceneBeatResponse.model_validate(obj)


@router.delete("/scene-beats/{beat_id}", status_code=204)
async def delete_scene_beat(beat_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_scene_beat(db, beat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="beat not found")
    return None


@router.post("/scripts/{script_id}/seed-from-json")
async def seed_scenes_from_json(
    script_id: int,
    dry_run: bool = Query(False, description="Do not write inserts when true"),
    db: Session = Depends(get_db),
):
    count = svc.seed_scenes_from_script_json(db, script_id, dry_run=dry_run)
    return {
        "script_id": script_id,
        "prepared": count,
        "inserted": 0 if dry_run else count,
    }


@router.get(
    "/stories/{story_id}/treatments", response_model=List[StoryTreatmentResponse]
)
async def list_treatments(
    story_id: int,
    latest_only: bool = Query(False, description="仅返回最新一条修订"),
    db: Session = Depends(get_db),
):
    items = svc.list_treatments_by_story(db, story_id)
    if latest_only:
        return [StoryTreatmentResponse.model_validate(items[0])] if items else []
    return [StoryTreatmentResponse.model_validate(it) for it in items]


@router.post("/stories/{story_id}/treatments", response_model=StoryTreatmentResponse)
async def create_treatment(
    story_id: int,
    body: StoryTreatmentCreate,
    db: Session = Depends(get_db),
):
    if body.story_id != story_id:
        raise HTTPException(status_code=400, detail="story_id mismatch")
    obj = svc.create_treatment(db, body)
    return StoryTreatmentResponse.model_validate(obj)


@router.get(
    "/treatments/{treatment_id}/step-outlines",
    response_model=List[StoryStepOutlineResponse],
)
async def list_step_outlines_for_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
):
    outlines = svc.list_step_outlines(db, treatment_id)
    return [StoryStepOutlineResponse.model_validate(it) for it in outlines]


@router.post(
    "/treatments/{treatment_id}/step-outlines", response_model=StoryStepOutlineResponse
)
async def create_step_outline_for_treatment(
    treatment_id: int,
    body: StoryStepOutlineCreate,
    db: Session = Depends(get_db),
):
    if body.story_treatment_id != treatment_id:
        raise HTTPException(status_code=400, detail="story_treatment_id mismatch")
    treatment = svc.get_treatment(db, treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="treatment not found")
    if body.story_id != treatment.story_id:
        raise HTTPException(status_code=400, detail="story_id does not match treatment")
    obj = svc.create_step_outline(db, body)
    return StoryStepOutlineResponse.model_validate(obj)
