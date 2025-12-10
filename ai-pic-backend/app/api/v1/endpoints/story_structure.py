from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import story_structure_service as svc
from app.services.ai_service import ai_service
from app.utils.model_utils import parse_model_and_provider, normalize_openai_image_style
from app.models.story_structure import Environment
from app.schemas.story_structure import (
    StoryTreatmentCreate,
    StoryTreatmentResponse,
    StoryStepOutlineCreate,
    StoryStepOutlineResponse,
    ScriptStructureResponse,
    SceneWithChildren,
    SceneResponse,
    SceneCreate,
    SceneUpdate,
    SceneBeatCreate,
    SceneBeatResponse,
    SceneBeatUpdate,
    ShotResponse,
    ShotCreate,
    ShotUpdate,
    EnvironmentCreate,
    EnvironmentResponse,
    EnvironmentUpdate,
)


router = APIRouter()


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
            raise HTTPException(status_code=400, detail="shot_number already exists for scene")
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
            raise HTTPException(status_code=400, detail="shot_number already exists for scene")
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

@router.get("/environments", response_model=List[EnvironmentResponse])
async def list_environments(db: Session = Depends(get_db)):
    items = svc.list_environments(db)
    return [EnvironmentResponse.model_validate(it) for it in items]


@router.get("/environments/{env_id}", response_model=EnvironmentResponse)
async def get_environment(env_id: int, db: Session = Depends(get_db)):
    env = svc.get_environment(db, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    return EnvironmentResponse.model_validate(env)


@router.post("/environments", response_model=EnvironmentResponse)
async def create_environment(body: EnvironmentCreate, db: Session = Depends(get_db)):
    env = svc.create_environment(db, body.model_dump(exclude_none=True))
    return EnvironmentResponse.model_validate(env)


@router.put("/environments/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: int,
    body: EnvironmentUpdate,
    db: Session = Depends(get_db),
):
    env = svc.update_environment(db, env_id, body.model_dump(exclude_none=True))
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    return EnvironmentResponse.model_validate(env)


@router.delete("/environments/{env_id}", status_code=204)
async def delete_environment(env_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_environment(db, env_id)
    if not ok:
        raise HTTPException(status_code=404, detail="environment not found")
    return None


# Environment images (reference-only, used as generation anchors)

def _infer_provider_from_model(model: Optional[str]) -> Optional[str]:
    if not model:
        return None
    normalized = model.lower()
    if normalized.startswith(("seedream", "volcengine")):
        return "volcengine"
    if normalized.startswith("deepseek"):
        return "deepseek"
    if normalized.startswith(("keling", "kling")):
        return "keling"
    if normalized.startswith("jimeng"):
        return "jimeng"
    if normalized.startswith(("dall-e", "dalle")):
        return "openai"
    return None


def _strip_provider_prefix(model: Optional[str]) -> Optional[str]:
    if not model:
        return None
    return model.split(":", 1)[1] if ":" in model else model


async def _download_and_attach(db: Session, env, image_urls: List[str]) -> List[str]:
    saved: List[str] = []
    for image_url in image_urls:
        try:
            local_file = await ai_service._download_image(image_url, env.name, "environment")
        except Exception:
            local_file = None
        if not local_file:
            continue
        filename = os.path.basename(local_file)
        relative_path = f"/uploads/{filename}"
        saved.append(relative_path)
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
    category_hint = "室内布局、光线、材质细节" if (env.category or "").lower() == "indoor" else "室外空间、天气、周边环境"
    parts.append(
        f"Overall-to-detail: 开场远景交代空间 -> 中景展示主要区域 -> 近景刻画关键道具/纹理；"
        f"Environment focus: {category_hint}；保持真实光影和透视，色彩和风格统一。"
    )
    if extra:
        parts.append(extra)
    if not parts:
        return "Environment scene with clear spatial layout and lighting cues"
    return " | ".join(parts)


@router.get("/environments/{env_id}/images")
async def list_environment_images(env_id: int, db: Session = Depends(get_db)):
    env = svc.get_environment(db, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    images = env.reference_images or []
    normalized: List[Dict[str, Any]] = []
    for url in images:
        if isinstance(url, str):
            normalized.append({"url": url})
    return {"success": True, "data": {"images": normalized, "count": len(normalized)}}


@router.delete("/environments/{env_id}/images")
async def delete_environment_image(env_id: int, image_url: str, db: Session = Depends(get_db)):
    env = svc.get_environment(db, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="environment not found")
    refs = env.reference_images or []
    env.reference_images = [u for u in refs if u != image_url]
    db.commit()
    return {"success": True, "data": {"images": env.reference_images, "count": len(env.reference_images or [])}}


@router.post("/environments/{env_id}/images/generate")
async def generate_environment_images(
    env_id: int,
    request: Request,
    prompt: Optional[str] = Query(None, description="生成提示词，不填则用环境描述/名称"),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸，如 1024x1024 或 2K"),
    db: Session = Depends(get_db),
):
    env = svc.get_environment(db, env_id)
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
    final_prompt = _compose_environment_prompt(env, extra_prompt)
    selected_model_raw = (payload.get("model") or model or "").strip() or None
    selected_model, prefer_provider_from_model = parse_model_and_provider(selected_model_raw)
    prefer_provider = prefer_provider or prefer_provider_from_model
    style_hint = payload.get("style") or "realistic"
    if (prefer_provider or "").lower() == "openai":
        style_hint = normalize_openai_image_style(style_hint)
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    count_int = max(1, min(count_int, 4))

    prefer_provider = prefer_provider or _infer_provider_from_model(selected_model or "")
    try:
        response = await ai_service.ai_manager.generate_image(
            prompt=final_prompt,
            model=_strip_provider_prefix(selected_model),
            n=count_int,
            size=size_value if prefer_provider == "volcengine" else None,
            prefer_provider=prefer_provider,
            style=style_hint,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=500, detail=f"环境文生图调用失败: {exc}") from exc

    if not response.success:
        raise HTTPException(status_code=500, detail=response.error or "环境文生图生成失败")

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise HTTPException(status_code=500, detail="环境文生图接口未返回任何图像")

    saved = await _download_and_attach(db, env, images)
    db.commit()
    db.refresh(env)
    return {"success": True, "data": {"images": saved, "count": len(saved)}}


@router.post("/environments/{env_id}/images/variants")
async def generate_environment_image_variants(
    env_id: int,
    request: Request,
    base_image: Optional[str] = Query(None, description="基准图 URL 或相对路径"),
    prompt: Optional[str] = Query(None, description="变体提示词"),
    model: Optional[str] = Query(None, description="模型，形如 provider:model_id"),
    count: int = Query(1, ge=1, le=4, description="生成数量"),
    size: Optional[str] = Query(None, description="分辨率/尺寸"),
    db: Session = Depends(get_db),
):
    env = svc.get_environment(db, env_id)
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

    base = payload.get("base_image", base_image) or (env.reference_images[0] if env.reference_images else None)
    if not base:
        raise HTTPException(status_code=400, detail="缺少基准图像")
    if isinstance(base, str) and base.startswith("http"):
        image_url = base
    else:
        path = base if isinstance(base, str) else ""
        if path and not path.startswith("/"):
            path = "/" + path
        image_url = f"http://localhost:8000{path}"

    model_raw = (payload.get("model") or model or "").strip() or None
    model_value, provider_from_model = parse_model_and_provider(model_raw)
    prefer_provider = provider_from_model or _infer_provider_from_model(model_value or "")
    style_hint = payload.get("style") or "realistic"
    if (prefer_provider or "").lower() == "openai":
        style_hint = normalize_openai_image_style(style_hint)
    extra_prompt = payload.get("prompt", prompt)
    prompt_value = _compose_environment_prompt(env, extra_prompt or "Generate stylistically consistent variants based on this environment reference")
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1
    count_int = max(1, min(count_int, 4))

    try:
        response = await ai_service.ai_manager.image_to_image(
            image_url=image_url,
            prompt=prompt_value,
            model=model_value,
            prefer_provider=prefer_provider,
            count=count_int,
            size=size_value,
            style=style_hint,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        raise HTTPException(status_code=500, detail=f"环境图生图调用失败: {exc}") from exc

    if not response.success:
        raise HTTPException(status_code=500, detail=response.error or "环境图生图生成失败")

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise HTTPException(status_code=500, detail="环境图生图接口未返回任何图像")

    saved = await _download_and_attach(db, env, images)
    db.commit()
    db.refresh(env)
    return {"success": True, "data": {"images": saved, "count": len(saved)}}


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
            raise HTTPException(status_code=400, detail="order_index already exists for scene")
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
