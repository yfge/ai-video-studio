from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
import re
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode, Script
from app.schemas.script import (
    ScriptCreate, ScriptUpdate, ScriptResponse, 
    ScriptGenerationRequest
)
from app.services.ai_service import ai_service
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryboardModel, StoryboardPlanModel, StoryboardPlanScene
from app.core.logging import get_logger
from app.utils.script_parser import extract_script_structure
import json


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_uuid(value: Any) -> str:
    if not value:
        return str(uuid4())
    try:
        return str(UUID(str(value)))
    except Exception:
        return str(uuid4())


def _ensure_iso_datetime(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value)).isoformat()
    except Exception:
        return fallback


def _serialize_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {}
    for key, val in frame.items():
        if isinstance(val, UUID):
            serialized[key] = str(val)
        elif isinstance(val, datetime):
            serialized[key] = val.isoformat()
        else:
            serialized[key] = val
    return serialized


def _load_existing_frames(script: Script) -> List[Dict[str, Any]]:
    storyboard = (script.extra_metadata or {}).get("storyboard") if script.extra_metadata else None
    frames = storyboard.get("frames") if isinstance(storyboard, dict) else None
    if not isinstance(frames, list):
        return []
    return [deepcopy(frame) for frame in frames if isinstance(frame, dict)]


def _augment_frames(
    frames: List[Dict[str, Any]],
    *,
    scene_map: Dict[int, Dict[str, Any]],
    generation_source: str,
    generation_method: str,
    generation_model: Optional[str],
) -> List[Dict[str, Any]]:
    now_iso = _now_iso()
    augmented: List[Dict[str, Any]] = []
    for raw in frames:
        frame = dict(raw or {})
        frame_id = _coerce_uuid(frame.get("frame_id"))
        frame["frame_id"] = frame_id
        scene_number = _to_int(frame.get("scene_number"))
        if scene_number is None:
            scene_number = _to_int(frame.get("scene_index"))
        if scene_number is not None:
            frame["scene_number"] = scene_number
            if scene_number in scene_map:
                frame.setdefault("scene_index", scene_number)
            elif scene_map:
                # 若超出范围，使用最接近的键
                closest = min(scene_map.keys(), key=lambda k: abs(k - scene_number))
                frame.setdefault("scene_index", closest)
        else:
            frame_index = frame.get("scene_index")
            if frame_index is None and scene_map:
                first_key = next(iter(scene_map.keys()), None)
                if first_key is not None:
                    frame["scene_number"] = first_key
                    frame["scene_index"] = first_key
            else:
                frame["scene_index"] = frame_index
        frame["generation_source"] = frame.get("generation_source") or generation_source
        frame["generation_method"] = frame.get("generation_method") or generation_method
        if generation_model:
            frame["generation_model"] = frame.get("generation_model") or generation_model
        frame["generated_at"] = _ensure_iso_datetime(frame.get("generated_at"), now_iso)
        frame["updated_at"] = now_iso
        if not isinstance(frame.get("reference_images"), list):
            frame["reference_images"] = []
        augmented.append(frame)
    return augmented


def _merge_frames(
    existing_frames: List[Dict[str, Any]],
    new_frames: List[Dict[str, Any]],
    selected_scenes: Optional[List[int]],
) -> List[Dict[str, Any]]:
    has_selection = selected_scenes is not None
    selected_set = {s for s in (selected_scenes or []) if s is not None} if has_selection else None
    merged: List[Dict[str, Any]] = []
    if existing_frames and selected_set:
        for frame in existing_frames:
            scene_number = _to_int(frame.get("scene_number"))
            if scene_number in selected_set:
                continue
            merged.append(deepcopy(frame))
    elif not has_selection:
        # 全量生成，旧分镜不保留
        merged = []
    else:
        merged = [deepcopy(frame) for frame in existing_frames]

    merged.extend(new_frames)
    merged.sort(key=lambda fr: (_to_int(fr.get("scene_number")) or 0, fr.get("frame_number") or 0))
    for idx, frame in enumerate(merged, start=1):
        frame["frame_number"] = idx
        if frame.get("scene_number") is not None and frame.get("scene_index") is None:
            frame["scene_index"] = _to_int(frame.get("scene_number"))
    return merged


def _enforce_storyboard_variety(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    shot_cycle = ["远景", "中景", "近景", "特写"]
    movement_cycle = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
    composition_cycle = ["三分法", "对称", "前后景", "对角线", "中心对称"]
    seen: Dict[tuple[Any, str], int] = {}
    for frame in frames:
        desc = (frame.get("description") or "").strip()
        scene_no = _to_int(frame.get("scene_number"))
        key = (scene_no, desc)
        count = seen.get(key, -1) + 1
        seen[key] = count
        if count > 0:
            frame["shot_type"] = shot_cycle[(count + (scene_no or 0)) % len(shot_cycle)]
            frame["camera_movement"] = movement_cycle[(count + (scene_no or 0)) % len(movement_cycle)]
            frame["composition"] = composition_cycle[(count + (scene_no or 0)) % len(composition_cycle)]
            base_desc = desc or f"场景{scene_no or ''}"
            frame["description"] = f"{base_desc}（变体{count + 1}，强调{frame['camera_movement']}）"
            frame["duration_seconds"] = max(2, min(12, (frame.get("duration_seconds") or 3) + ((count % 3) - 1)))
            prompt_parts = [frame["description"], f"景别:{frame['shot_type']}", f"运镜:{frame['camera_movement']}", f"构图:{frame['composition']}"]
            frame["ai_prompt"] = "；".join(prompt_parts)[:500]
    return frames


router = APIRouter()

@router.post("/", response_model=ScriptResponse)
async def create_script(
    script: ScriptCreate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """创建剧本"""
    # 检查剧集是否存在
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    # 计算字数和字符数
    word_count = len(script.content.split()) if script.content else 0
    character_count = len(script.content) if script.content else 0
    
    db_script = Script(
        **script.dict(),
        word_count=word_count,
        character_count=character_count
    )
    db.add(db_script)
    db.commit()
    db.refresh(db_script)
    
    return ScriptResponse.from_orm(db_script)

@router.post("/generate", response_model=ScriptResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """使用AI生成剧本"""
    # 获取剧集信息
    episode = db.query(Episode).filter(Episode.id == request.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    # 获取故事信息
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    # 构建剧集数据
    episode_data = {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "summary": episode.summary,
        "plot_points": episode.plot_points,
        "character_arcs": episode.character_arcs,
        "conflicts": episode.conflicts,
        "duration_minutes": episode.duration_minutes,
        "scene_count": episode.scene_count
    }
    
    # 构建故事数据
    story_data = {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location
    }
    
    # 调用AI服务生成剧本
    # 解析模型与提供商
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=request.format_type,
        language=request.language,
        dialogue_style=request.dialogue_style,
        scene_detail_level=request.scene_detail_level,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.7
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI剧本生成失败")
    
    # 解析AI生成的内容
    try:
        ai_content = json.loads(result["content"])
    except json.JSONDecodeError:
        # 如果不是JSON格式，尝试从纯文本中抽取结构化信息
        extracted = extract_script_structure(result["content"])
        ai_content = {
            "content": extracted.get("content", result["content"]),
            "scenes": extracted.get("scenes", []),
            "dialogues": extracted.get("dialogues", []),
            "stage_directions": extracted.get("stage_directions", []),
            "metadata": extracted.get("metadata", {})
        }
    
    # 提取剧本内容
    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues = ai_content.get("dialogues", [])
    stage_directions = ai_content.get("stage_directions", [])
    
    # 计算统计信息
    word_count = len(script_content.split()) if script_content else 0
    character_count = len(script_content) if script_content else 0
    page_count = max(1, character_count // 2000)  # 估算页数
    
    # 创建剧本记录
    # 额外元数据
    extra_meta = {k: v for k, v in ai_content.items() if k not in {"content","scenes","dialogues","stage_directions","metadata"}}

    db_script = Script(
        episode_id=request.episode_id,
        title=f"{episode.title} - 剧本",
        content=script_content,
        scenes=scenes,
        dialogues=dialogues,
        stage_directions=stage_directions,
        format_type=request.format_type,
        language=request.language,
        page_count=page_count,
        word_count=word_count,
        character_count=character_count,
        generation_prompt=result["prompt"],
        ai_model=result["generation_method"],
        generation_params={
            "dialogue_style": request.dialogue_style,
            "scene_detail_level": request.scene_detail_level,
            "additional_requirements": request.additional_requirements,
            "style_preferences": request.style_preferences,
            "model": request.model,
            "temperature": request.temperature or 0.7
        },
        extra_metadata=extra_meta or None,
        status="draft"
    )
    
    db.add(db_script)
    db.commit()
    db.refresh(db_script)
    
    return ScriptResponse.from_orm(db_script)


@router.post("/prompt/preview")
async def preview_script_prompt(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    episode = db.query(Episode).filter(Episode.id == request.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    episode_data = {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "summary": episode.summary,
        "plot_points": episode.plot_points,
        "character_arcs": episode.character_arcs,
        "conflicts": episode.conflicts,
        "duration_minutes": episode.duration_minutes,
        "scene_count": episode.scene_count
    }
    story_data = {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location
    }
    variables = {
        "story": story_data,
        "episode": episode_data,
        "format_type": request.format_type,
        "language": request.language,
        "dialogue_style": request.dialogue_style,
        "scene_detail_level": request.scene_detail_level,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or []
    }
    prompt = PromptManager().render_prompt(PromptTemplate.SCRIPT_GENERATION.value, variables)
    return {"success": True, "data": {"prompt": prompt}}


def _process_script_generation_task(task_id: int, request_dict: dict, user_id: int):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        episode = db.query(Episode).filter(Episode.id == request_dict.get("episode_id")).first()
        if not episode:
            raise RuntimeError("剧集不存在")
        story = db.query(Story).filter(Story.id == episode.story_id).first()
        if not story:
            raise RuntimeError("故事不存在")

        episode_data = {
            "episode_number": episode.episode_number,
            "title": episode.title,
            "summary": episode.summary,
            "plot_points": episode.plot_points,
            "character_arcs": episode.character_arcs,
            "conflicts": episode.conflicts,
            "duration_minutes": episode.duration_minutes,
            "scene_count": episode.scene_count
        }
        story_data = {
            "title": story.title,
            "genre": story.genre,
            "theme": story.theme,
            "synopsis": story.synopsis,
            "main_conflict": story.main_conflict,
            "resolution": story.resolution,
            "main_characters": story.main_characters,
            "character_relationships": story.character_relationships,
            "world_building": story.world_building,
            "setting_time": story.setting_time,
            "setting_location": story.setting_location
        }

        import anyio, json as _json

        async def _run():
            prefer_provider = None
            model_id = request_dict.get("model")
            if model_id and ":" in model_id:
                prefer_provider, model_id = model_id.split(":", 1)
            return await ai_service.generate_script(
                episode=episode_data,
                story=story_data,
                format_type=request_dict.get("format_type", "screenplay"),
                language=request_dict.get("language", "zh-CN"),
                dialogue_style=request_dict.get("dialogue_style", "natural"),
                scene_detail_level=request_dict.get("scene_detail_level", "medium"),
                additional_requirements=request_dict.get("additional_requirements"),
                style_preferences=request_dict.get("style_preferences"),
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7)
            )

        result = anyio.run(_run)
        if not result:
            raise RuntimeError("AI剧本生成失败")

        try:
            ai_content = _json.loads(result["content"]) if isinstance(result["content"], str) else result["content"]
        except Exception:
            ai_content = {"content": result.get("content")}

        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues = ai_content.get("dialogues", [])
        stage_directions = ai_content.get("stage_directions", [])
        extra_meta = {k: v for k, v in ai_content.items() if k not in {"content","scenes","dialogues","stage_directions","metadata"}}

        word_count = len(script_content.split()) if script_content else 0
        character_count = len(script_content) if script_content else 0
        page_count = max(1, character_count // 2000)

        sc = Script(
            episode_id=request_dict.get("episode_id"),
            title=f"{episode.title} - 剧本",
            content=script_content,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            format_type=request_dict.get("format_type", "screenplay"),
            language=request_dict.get("language", "zh-CN"),
            page_count=page_count,
            word_count=word_count,
            character_count=character_count,
            generation_prompt=result.get("prompt"),
            ai_model=result.get("generation_method"),
            generation_params={k: request_dict.get(k) for k in ["dialogue_style","scene_detail_level","additional_requirements","style_preferences","model","temperature"]},
            extra_metadata=extra_meta or None,
            status="draft"
        )
        db.add(sc)
        db.commit()
        db.refresh(sc)

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{sc.id}"
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/generate-async")
async def generate_script_async(
    request: ScriptGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    from app.models.task import Task
    t = Task(
        title=f"生成剧本 - 剧集{request.episode_id}",
        description="异步剧本生成",
        task_type="image_generation",
        prompt=f"Script for episode {request.episode_id}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    background_tasks.add_task(_process_script_generation_task, t.id, request.dict(), current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


# 分镜（Storyboard）相关
@router.get("/{script_id}/storyboard")
async def get_storyboard(
    script_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    from app.core.logging import get_logger
    logger = get_logger()
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    storyboard = (script.extra_metadata or {}).get("storyboard") if script.extra_metadata else None
    try:
        frames = (storyboard or {}).get("frames") or []
        logger.info(f"Storyboard GET | script_id={script_id} frames={len(frames)}")
    except Exception:
        pass
    data = dict(storyboard or {"frames": []})
    meta = dict(data.get("meta") or {})
    if script.storyboard_version is not None:
        meta.setdefault("version", script.storyboard_version)
    if script.storyboard_updated_at:
        meta.setdefault("updated_at", script.storyboard_updated_at.isoformat())
    data["meta"] = meta
    if script.storyboard_plan:
        data["plan"] = script.storyboard_plan
    return {"success": True, "data": data}


@router.post("/{script_id}/storyboard/preview")
async def preview_storyboard_prompt(
    script_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    # 简化版提示词
    prompt = (
        "你是专业分镜师，基于剧本的场景生成分镜列表。每个分镜包含："
        "frame_number, scene_number, shot_type, camera_movement, composition, description, duration_seconds, ai_prompt。"
    )
    return {"success": True, "data": {"prompt": prompt}}


@router.post("/{script_id}/storyboard/generate")
async def generate_storyboard(
    script_id: int,
    model: str | None = None,
    temperature: float = Query(0.7, ge=0.0, le=1.5, description="创造性温度"),
    frames_per_scene: int = Query(7, ge=1, le=10, description="每场景建议分镜数"),
    max_frames: int | None = Query(None, ge=1, le=500, description="最大分镜帧数上限"),
    scene_numbers: str | None = Query(None, description="逗号分隔的场景编号列表，如 1,3,4"),
    use_plan: bool = Query(False, description="是否先使用分镜规划，再逐场景生成"),
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    logger = get_logger()
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    # 解析选择的场景
    selected_scenes: list[int] | None = None
    if scene_numbers:
        try:
            selected_scenes = [int(x.strip()) for x in scene_numbers.split(',') if x.strip()]
        except Exception:
            raise HTTPException(status_code=400, detail="scene_numbers 格式不正确")

    # 以剧本结构为输入（可按选择的场景过滤），并补充故事/剧集上下文
    all_scenes = script.scenes or []
    scenes_filtered: List[Dict[str, Any]] = []
    scene_order: List[int] = []
    if selected_scenes:
        selected_set = {s for s in selected_scenes}
        for idx, sc in enumerate(all_scenes, start=1):
            if idx in selected_set:
                scenes_filtered.append(sc)
                scene_order.append(idx)
    else:
        scenes_filtered = all_scenes
        scene_order = list(range(1, len(all_scenes) + 1))

    # 获取剧集与故事元信息
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    story = db.query(Story).filter(Story.id == episode.story_id).first() if episode else None

    script_data = {
        "content": script.content,
        "scenes": scenes_filtered,
        "dialogues": script.dialogues,
        "stage_directions": script.stage_directions,
        "episode": {
            "episode_number": episode.episode_number if episode else None,
            "title": episode.title if episode else None,
            "duration_minutes": episode.duration_minutes if episode else None,
            "scene_count": episode.scene_count if episode else None,
        } if episode else None,
        "story": {
            "title": story.title if story else None,
            "genre": story.genre if story else None,
            "theme": story.theme if story else None,
            "setting_time": story.setting_time if story else None,
            "setting_location": story.setting_location if story else None,
            "world_building": story.world_building if story else None,
            "main_characters": story.main_characters if story else None,
        } if story else None,
    }
    # 默认优先使用 OpenAI（其支持 json_schema 更可靠）
    prefer_provider = "openai"
    model_id = model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    # 记录请求参数
    try:
        logger.info(
            f"StoryboardGen Request | script_id={script_id} model={model or 'auto'} prefer_provider={prefer_provider or 'openai'} temp={temperature} fps={frames_per_scene} max_frames={max_frames} scenes={selected_scenes or 'all'}"
        )
    except Exception:
        pass

    scene_map = {idx: sc for idx, sc in enumerate(all_scenes, start=1)}
    existing_frames = _load_existing_frames(script)

    reasoner_result = None
    if getattr(ai_service, "storyboard_reasoner", None) and use_plan:
        try:
            reasoner_result = await ai_service.storyboard_reasoner.generate(
                script=script_data,
                frames_per_scene=frames_per_scene,
                max_frames=max_frames,
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=temperature,
                selected_scenes=selected_scenes,
            )
            if reasoner_result and reasoner_result.get("reasoning_trace"):
                try:
                    logger.info(f"Storyboard Reasoner trace: {reasoner_result['reasoning_trace']}")
                except Exception:
                    pass
        except Exception as exc:
            logger.warning(f"Storyboard LangGraph reasoner failed: {exc}")

    frames_generated: List[Dict[str, Any]] = []
    generation_method = "direct"
    generation_source = f"ai:{prefer_provider or 'auto'}"
    generation_model = model_id
    provider_used: Optional[str] = prefer_provider

    if reasoner_result and reasoner_result.get("content"):
        try:
            reasoned_payload = json.loads(reasoner_result["content"]) if isinstance(reasoner_result["content"], str) else reasoner_result["content"]
            StoryboardModel.model_validate(reasoned_payload)
            frames_generated = reasoned_payload.get("frames") or []
            provider_used = reasoner_result.get("provider_used") or prefer_provider
            generation_model = reasoner_result.get("model_used") or model_id
            generation_method = reasoner_result.get("generation_method") or "langgraph_plan"
            generation_source = f"langgraph:{provider_used or 'auto'}"
        except Exception as exc:
            logger.warning(f"Storyboard reasoner response invalid, fallback to standard pipeline: {exc}")
            frames_generated = []

    # 先走规划流程（可选）
    if not frames_generated and use_plan:
        plan_resp = await ai_service.generate_storyboard_plan(
            script=script_data,
            frames_per_scene=frames_per_scene,
            selected_scenes=selected_scenes,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=0.3,
        )
        if plan_resp and plan_resp.get("normalized"):
            try:
                StoryboardPlanModel.model_validate(plan_resp["normalized"])
                script.storyboard_plan = plan_resp["normalized"]
                extra_meta = dict(script.extra_metadata or {})
                extra_meta["storyboard_plan"] = plan_resp["normalized"]
                script.extra_metadata = extra_meta
                generation_method = "plan"
                provider_used = plan_resp.get("provider_used") or prefer_provider
                generation_source = f"ai_plan:{provider_used or 'auto'}"
                generation_model = plan_resp.get("model_used") or model_id

                plan_scenes = plan_resp["normalized"].get("scenes", [])
                frames_all: List[Dict[str, Any]] = []
                for sp in plan_scenes:
                    try:
                        sp_model = StoryboardPlanScene.model_validate(sp)
                    except Exception:
                        continue
                    frames_scene = await ai_service.generate_storyboard_from_plan_for_scene(
                        script=script_data,
                        scene_plan=sp_model,
                        model=model_id,
                        prefer_provider=prefer_provider,
                        temperature=temperature,
                        max_frames=max_frames,
                    )
                    if frames_scene:
                        frames_all.extend(frames_scene)
                if frames_all:
                    frames_generated = frames_all
            except Exception as e:
                logger.warning(f"Storyboard plan validate/apply failed: {e}")

    # 若规划流程未生成结果，则直接调用AI接口
    if not frames_generated:
        result = await ai_service.generate_storyboard(
            script=script_data,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
            frames_per_scene=frames_per_scene,
            max_frames=max_frames
        )
        if result:
            try:
                raw_text = result.get("content") if isinstance(result, dict) else None
                if isinstance(raw_text, str):
                    logger.info(
                        f"StoryboardGen Raw Response Preview (len={len(raw_text)}): {raw_text[:2000]}"
                        f"{'...<truncated>' if len(raw_text) > 2000 else ''}"
                    )
                logger.info(
                    f"StoryboardGen Provider: {result.get('provider_used')} Model: {result.get('model_used')} Usage: {result.get('usage')}"
                )
            except Exception:
                pass
            try:
                sb_raw = json.loads(result["content"]) if isinstance(result.get("content"), str) else result.get("content")
            except Exception as exc:
                logger.warning(f"StoryboardGen JSON parse failed: {exc}")
                sb_raw = None
            if sb_raw:
                try:
                    sb_obj = StoryboardModel.model_validate(sb_raw)
                    sb_data = sb_obj.model_dump(mode="python")
                    frames_generated = sb_data.get("frames") or []
                    provider_used = result.get("provider_used") or prefer_provider
                    generation_source = f"ai:{provider_used or 'auto'}"
                    generation_model = result.get("model_used") or model_id
                except Exception as exc:
                    logger.warning(f"StoryboardGen validation failed: {exc}")

    # Fallback: 基于剧本快速生成简易分镜
    if not frames_generated:
        generation_method = "fallback"
        generation_source = "fallback"
        generation_model = None
        provider_used = "fallback"
        frames_fallback: List[Dict[str, Any]] = []
        shot_cycle = ["远景", "中景", "近景", "特写"]
        movement_cycle = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
        composition_cycle = ["三分法", "对称", "前后景", "对角线", "中心对称"]
        scenes = scenes_filtered
        frame_no = 1
        if scenes:
            for sidx, sc in enumerate(scenes, start=1):
                real_scene_number = scene_order[sidx - 1] if (sidx - 1) < len(scene_order) else sidx
                if max_frames and len(frames_fallback) >= max_frames:
                    break
                desc = sc.get("description") if isinstance(sc, dict) else (str(sc) if sc else "")
                segments = [seg for seg in re.split(r'[。.!?！？]', desc or '') if seg.strip()]
                count = max(1, frames_per_scene)
                for i in range(count):
                    if max_frames and len(frames_fallback) >= max_frames:
                        break
                    text = (segments[i] if i < len(segments) else (desc or f"场景 {sidx}"))
                    variant = (frame_no - 1)
                    shot = shot_cycle[variant % len(shot_cycle)]
                    movement = movement_cycle[variant % len(movement_cycle)]
                    composition = composition_cycle[variant % len(composition_cycle)]
                    prompt_parts = [text.strip()[:200], f"景别:{shot}", f"运镜:{movement}", f"构图:{composition}"]
                    frames_fallback.append({
                        "frame_number": frame_no,
                        "scene_number": real_scene_number,
                        "shot_type": shot,
                        "camera_movement": movement,
                        "composition": composition,
                        "description": text.strip()[:200],
                        "duration_seconds": 3 + (variant % 3) - 1,
                        "ai_prompt": "；".join(prompt_parts)[:500],
                        "reference_images": [],
                    })
                    frame_no += 1
        else:
            paragraphs = (script.content or "").split("\n\n")
            for para in paragraphs:
                if max_frames and len(frames_fallback) >= max_frames:
                    break
                text = para.strip().replace("\n", " ")[:200]
                if not text:
                    continue
                variant = (frame_no - 1)
                shot = shot_cycle[variant % len(shot_cycle)]
                movement = movement_cycle[variant % len(movement_cycle)]
                composition = composition_cycle[variant % len(composition_cycle)]
                prompt_parts = [text, f"景别:{shot}", f"运镜:{movement}", f"构图:{composition}"]
                frames_fallback.append({
                    "frame_number": frame_no,
                    "scene_number": None,
                    "shot_type": shot,
                    "camera_movement": movement,
                    "composition": composition,
                    "description": text,
                    "duration_seconds": 3 + (variant % 3) - 1,
                    "ai_prompt": "；".join(prompt_parts)[:500],
                    "reference_images": [],
                })
                frame_no += 1
        frames_generated = frames_fallback

    if not frames_generated:
        raise HTTPException(status_code=500, detail="分镜生成失败")

    frames_augmented = _augment_frames(
        frames_generated,
        scene_map=scene_map,
        generation_source=generation_source,
        generation_method=generation_method,
        generation_model=generation_model,
    )

    frames_list = list(frames_augmented)

    if selected_scenes:
        selected_set = {s for s in scene_order if s is not None}
        frames_list = [fr for fr in frames_list if _to_int(fr.get("scene_number")) in selected_set]
        try:
            logger.info(f"StoryboardGen Frames after scene filter {selected_scenes}: {len(frames_list)}")
        except Exception:
            pass

    if max_frames:
        frames_list = frames_list[:max_frames]
        try:
            logger.info(f"StoryboardGen Frames after max_frames({max_frames}) slice: {len(frames_list)}")
        except Exception:
            pass

    # 若有帧，但每个场景的帧数少于 frames_per_scene，则补齐
    try:
        supplementary_raw: List[Dict[str, Any]] = []
        if scene_order:
            target_scenes = scene_order
        else:
            target_scenes = list(range(1, (len(all_scenes) or 0) + 1))
        for s in target_scenes:
            if s is None:
                continue
            existing_count = len([fr for fr in frames_list if _to_int(fr.get("scene_number")) == s])
            deficit = max(0, frames_per_scene - existing_count)
            if deficit <= 0:
                continue
            src = all_scenes[s - 1] if 0 <= (s - 1) < len(all_scenes) else None
            desc = (src.get("description") if isinstance(src, dict) else (str(src) if src else ""))
            segs = [seg for seg in re.split(r'[。.!?！？]', desc or '') if seg.strip()]
            for i in range(deficit):
                text = (segs[i] if i < len(segs) else (desc or f"场景 {s}"))
                supplementary_raw.append({
                    "scene_number": s,
                    "description": (text or '').strip()[:200],
                    "shot_type": "中景",
                    "camera_movement": "固定",
                    "composition": "三分法",
                    "duration_seconds": 3,
                    "ai_prompt": (text or '').strip()[:200],
                    "reference_images": [],
                })
        if supplementary_raw:
            supplementary = _augment_frames(
                supplementary_raw,
                scene_map=scene_map,
                generation_source="supplement",
                generation_method="fallback",
                generation_model=generation_model,
            )
            frames_list.extend(supplementary)
        try:
            stats: Dict[Any, int] = {}
            for fr in frames_list:
                sn = _to_int(fr.get("scene_number"))
                stats[sn] = stats.get(sn, 0) + 1
            logger.info(f"StoryboardGen Frames after supplement (per scene): {stats}")
        except Exception:
            pass
    except Exception:
        pass

    # 规范化字段，填充缺省，并增强 ai_prompt
    try:
        allowed_shots = {"远景", "中景", "近景", "特写"}
        shot_map = {
            "wide": "远景", "long": "远景", "establishing": "远景", "ws": "远景",
            "medium": "中景", "ms": "中景",
            "close": "近景", "cs": "近景",
            "close-up": "特写", "cu": "特写", "extreme close-up": "特写", "ecu": "特写",
        }
        for fr in frames_list:
            shot = (fr.get("shot_type") or "").strip()
            shot_norm = shot_map.get(shot.lower()) if isinstance(shot, str) else None
            if shot_norm:
                fr["shot_type"] = shot_norm
            elif shot in allowed_shots:
                fr["shot_type"] = shot
            else:
                fr["shot_type"] = "中景"
            fr["camera_movement"] = fr.get("camera_movement") or "固定"
            fr["composition"] = fr.get("composition") or "三分法"
            fr["duration_seconds"] = fr.get("duration_seconds") or 3
            scene_no = _to_int(fr.get("scene_number"))
            chars: List[str] = []
            if scene_no and 0 < scene_no <= len(all_scenes):
                sc = all_scenes[scene_no - 1]
                if isinstance(sc, dict) and sc.get("characters"):
                    try:
                        chars = list(sc.get("characters") or [])
                    except Exception:
                        chars = []
            if not chars and story and story.main_characters:
                try:
                    chars = [c.get("name") for c in (story.main_characters or []) if isinstance(c, dict) and c.get("name")]
                except Exception:
                    pass
            base_desc = (fr.get("description") or "").strip()
            prompt_parts = [base_desc]
            if scene_no:
                prompt_parts.append(f"场景 {scene_no}")
            prompt_parts.append(f"景别: {fr.get('shot_type')}")
            prompt_parts.append(f"运镜: {fr.get('camera_movement')}")
            prompt_parts.append(f"构图: {fr.get('composition')}")
            if chars:
                prompt_parts.append(f"人物: {', '.join(chars[:5])}")
            fr["ai_prompt"] = "；".join([p for p in prompt_parts if p])[:500]
    except Exception:
        pass

    merge_targets = scene_order if selected_scenes else None
    merged_frames = _merge_frames(existing_frames, frames_list, merge_targets)
    diversified_frames = _enforce_storyboard_variety(merged_frames)

    frames_serialized = [_serialize_frame(fr) for fr in diversified_frames]
    try:
        StoryboardModel.model_validate({"frames": frames_serialized})
    except Exception as exc:
        logger.error(f"Storyboard validation failed before save: {exc}")
        raise HTTPException(status_code=500, detail="分镜结构不合法")

    sb_meta = {
        "version": script.storyboard_version,
        "updated_at": script.storyboard_updated_at.isoformat() if script.storyboard_updated_at else None,
        "generation_source": generation_source,
        "generation_method": generation_method,
        "generation_model": generation_model,
        "provider": provider_used,
        "scene_scope": scene_order if selected_scenes else None,
    }
    sb = {"frames": frames_serialized, "meta": sb_meta}
    if script.storyboard_plan:
        sb["plan"] = script.storyboard_plan
    extra = dict(script.extra_metadata or {})
    extra["storyboard"] = sb
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.utcnow()
    script.storyboard_version = (script.storyboard_version or 0) + 1

    db.commit()
    db.refresh(script)

    return {"success": True, "data": sb}


class StoryboardUpdateRequest(BaseModel):
    frames: list[dict]


@router.post("/{script_id}/storyboard/update")
async def update_storyboard(
    script_id: int,
    body: StoryboardUpdateRequest,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """保存分镜编辑后的结果（整量更新）"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    # 校验结构
    try:
        validated = StoryboardModel.model_validate({"frames": body.frames})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"分镜结构不合法: {e}")
    frames_python = validated.model_dump(mode="python").get("frames", [])
    now_iso = _now_iso()
    for idx, fr in enumerate(frames_python, start=1):
        fr["frame_id"] = _coerce_uuid(fr.get("frame_id"))
        fr["frame_number"] = idx
        scene_number = _to_int(fr.get("scene_number"))
        if scene_number is not None:
            fr["scene_number"] = scene_number
            fr.setdefault("scene_index", scene_number)
        fr["generated_at"] = _ensure_iso_datetime(fr.get("generated_at"), now_iso)
        fr["updated_at"] = now_iso
    frames_serialized = [_serialize_frame(fr) for fr in frames_python]
    extra = dict(script.extra_metadata or {})
    updated_at_dt = datetime.utcnow()
    script.storyboard_updated_at = updated_at_dt
    script.storyboard_version = (script.storyboard_version or 0) + 1
    existing_meta = {}
    if isinstance(extra.get("storyboard"), dict):
        existing_meta = dict(extra["storyboard"].get("meta") or {})
    existing_meta.update(
        {
            "version": script.storyboard_version,
            "updated_at": updated_at_dt.isoformat(),
            "generation_source": existing_meta.get("generation_source") or "manual",
            "generation_method": "manual_edit",
        }
    )
    extra["storyboard"] = {"frames": frames_serialized, "meta": existing_meta}
    script.extra_metadata = extra
    db.commit()
    db.refresh(script)
    return {"success": True}


def _process_storyboard_image_task(task_id: int, script_id: int, frame_indexes: list[int] | None, *, model: str | None = None, width: int = 1024, height: int = 1024, style: str = "realistic"):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise RuntimeError("剧本不存在")
        sb = (script.extra_metadata or {}).get("storyboard") if script.extra_metadata else None
        if not sb or not sb.get("frames"):
            raise RuntimeError("未找到分镜数据")

        frames = sb["frames"]
        target_indexes = frame_indexes or list(range(len(frames)))

        import anyio

        async def _gen_image(prompt: str) -> dict | None:
            try:
                prefer_provider = None
                model_id = model
                if model_id and ":" in model_id:
                    prefer_provider, model_id = model_id.split(":", 1)
                resp = await ai_service.ai_manager.generate_image(
                    prompt=prompt,
                    model=model_id,
                    prefer_provider=prefer_provider,
                    width=width,
                    height=height,
                    style=style,
                )
                if resp.success:
                    data = resp.data if isinstance(resp.data, dict) else {}
                    return {"url": data.get("image_url") or data.get("url"), "provider": resp.provider, "model": resp.model}
            except Exception as e:
                print(f"图像生成失败: {e}")
            return None

        # 逐帧生成图像URL
        for idx in target_indexes:
            fr = frames[idx]
            prompt = fr.get("ai_prompt") or fr.get("description") or ""
            if not prompt:
                continue
            result = anyio.run(_gen_image, prompt)
            if result and result.get("url"):
                fr["image_url"] = result["url"]

        # 保存
        extra = script.extra_metadata or {}
        extra["storyboard"] = sb
        script.extra_metadata = extra
        db.commit()

        if task:
            task.status = TaskStatus.COMPLETED
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


class StoryboardImageRequest(BaseModel):
    frames: list[int] = Field(default_factory=list, description="要生成图像的分镜索引列表（基于0的索引）")
    model: Optional[str] = Field(default=None, description="模型ID，可选 'provider:model' 形式")
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)
    style: str = Field(default="realistic")


@router.post("/{script_id}/storyboard/generate-images")
async def generate_storyboard_images(
    script_id: int,
    body: StoryboardImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    from app.models.task import Task
    t = Task(
        title=f"分镜图像生成 - 剧本{script_id}",
        description="根据分镜生成图像",
        task_type="image_generation",
        prompt=f"Storyboard image generation for script {script_id}",
        parameters=json.dumps({
            "script_id": script_id,
            "frames": body.frames or [],
            "model": body.model,
            "width": body.width,
            "height": body.height,
            "style": body.style,
        }, ensure_ascii=False),
        user_id=current_user.id
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    background_tasks.add_task(
        _process_storyboard_image_task,
        t.id,
        script_id,
        body.frames,
        model=body.model,
        width=body.width,
        height=body.height,
        style=body.style,
    )
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_storyboard_video_task(task_id: int, script_id: int, frame_indexes: list[int] | None):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise RuntimeError("剧本不存在")
        sb = (script.extra_metadata or {}).get("storyboard") if script.extra_metadata else None
        if not sb or not sb.get("frames"):
            raise RuntimeError("未找到分镜数据")

        frames = sb["frames"]
        target_indexes = frame_indexes or list(range(len(frames)))

        import anyio

        async def _gen_video(prompt: str) -> dict | None:
            try:
                resp = await ai_service.ai_manager.generate_video(prompt=prompt)
                if resp.success:
                    return {"url": (resp.data.get("video_url") if isinstance(resp.data, dict) else None) or None, "provider": resp.provider, "model": resp.model}
            except Exception as e:
                print(f"视频生成失败: {e}")
            return None

        # 逐帧生成视频URL（示意）
        for idx in target_indexes:
            fr = frames[idx]
            prompt = fr.get("ai_prompt") or fr.get("description") or ""
            if not prompt:
                continue
            result = anyio.run(_gen_video, prompt)
            if result and result.get("url"):
                fr["video_url"] = result["url"]

        # 保存
        extra = script.extra_metadata or {}
        extra["storyboard"] = sb
        script.extra_metadata = extra
        db.commit()

        if task:
            task.status = TaskStatus.COMPLETED
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/{script_id}/storyboard/generate-video")
class StoryboardVideoRequest(BaseModel):
    frames: list[int] = Field(default_factory=list, description="要生成视频的分镜索引列表（基于0的索引）")


@router.post("/{script_id}/storyboard/generate-video")
async def generate_storyboard_video(
    script_id: int,
    body: StoryboardVideoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    from app.models.task import Task
    t = Task(
        title=f"分镜视频生成 - 剧本{script_id}",
        description="根据分镜生成视频",
        task_type="image_generation",
        prompt=f"Storyboard video generation for script {script_id}",
        parameters=json.dumps({"script_id": script_id, "frames": body.frames or []}, ensure_ascii=False),
        user_id=current_user.id
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    background_tasks.add_task(_process_storyboard_video_task, t.id, script_id, body.frames)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}

@router.get("/", response_model=List[ScriptResponse])
async def get_scripts(
    episode_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    format_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取剧本列表"""
    query = db.query(Script)
    
    if episode_id:
        query = query.filter(Script.episode_id == episode_id)
    
    if status:
        query = query.filter(Script.status == status)
    
    if format_type:
        query = query.filter(Script.format_type == format_type)
    
    scripts = query.order_by(Script.created_at.desc()).offset(skip).limit(limit).all()
    return [ScriptResponse.from_orm(script) for script in scripts]

@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取剧本详情"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    
    return ScriptResponse.from_orm(script)

@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """更新剧本"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    
    # 更新剧本信息
    for field, value in script_update.dict(exclude_unset=True).items():
        setattr(script, field, value)
    
    # 重新计算统计信息
    if script_update.content:
        script.word_count = len(script_update.content.split())
        script.character_count = len(script_update.content)
        script.page_count = max(1, script.character_count // 2000)
    
    db.commit()
    db.refresh(script)
    
    return ScriptResponse.from_orm(script)

@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """删除剧本"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    
    db.delete(script)
    db.commit()
    
    return {"message": "剧本删除成功"}

@router.get("/episode/{episode_id}", response_model=List[ScriptResponse])
async def get_episode_scripts(
    episode_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取剧集的所有剧本"""
    # 检查剧集是否存在
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    scripts = db.query(Script).filter(Script.episode_id == episode_id).order_by(Script.created_at.desc()).all()
    return [ScriptResponse.from_orm(script) for script in scripts]

@router.post("/{script_id}/regenerate", response_model=ScriptResponse)
async def regenerate_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """重新生成剧本内容"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    # 构建剧集数据
    episode_data = {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "summary": episode.summary,
        "plot_points": episode.plot_points,
        "character_arcs": episode.character_arcs,
        "conflicts": episode.conflicts,
        "duration_minutes": episode.duration_minutes,
        "scene_count": episode.scene_count
    }
    
    # 构建故事数据
    story_data = {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location
    }
    
    # 使用原有的生成参数
    original_params = script.generation_params or {}
    
    # 调用AI服务重新生成剧本
    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=script.format_type,
        language=script.language,
        dialogue_style=original_params.get("dialogue_style", "natural"),
        scene_detail_level=original_params.get("scene_detail_level", "medium"),
        additional_requirements=f"重新生成第{episode.episode_number}集的剧本内容",
        style_preferences=original_params.get("style_preferences")
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI剧本重新生成失败")
    
    # 解析AI生成的内容
    try:
        ai_content = json.loads(result["content"])
    except json.JSONDecodeError:
        extracted = extract_script_structure(result["content"])
        ai_content = {
            "content": extracted.get("content", result["content"]),
            "scenes": extracted.get("scenes", []),
            "dialogues": extracted.get("dialogues", []),
            "stage_directions": extracted.get("stage_directions", []),
            "metadata": extracted.get("metadata", {})
        }
    
    # 更新剧本内容
    script_content = ai_content.get("content", "")
    script.content = script_content
    script.scenes = ai_content.get("scenes", [])
    script.dialogues = ai_content.get("dialogues", [])
    script.stage_directions = ai_content.get("stage_directions", [])
    script.generation_prompt = result["prompt"]
    script.ai_model = result["generation_method"]
    
    # 重新计算统计信息
    script.word_count = len(script_content.split()) if script_content else 0
    script.character_count = len(script_content) if script_content else 0
    script.page_count = max(1, script.character_count // 2000)
    
    db.commit()
    db.refresh(script)
    
    return ScriptResponse.from_orm(script)

@router.get("/formats")
async def get_script_formats():
    """获取剧本格式列表"""
    return [
        {"value": "screenplay", "label": "影视剧本"},
        {"value": "stage_play", "label": "舞台剧本"},
        {"value": "radio_drama", "label": "广播剧本"},
        {"value": "short_video", "label": "短视频脚本"},
        {"value": "live_stream", "label": "直播脚本"},
        {"value": "animation", "label": "动画脚本"}
    ]

@router.get("/languages")
async def get_script_languages():
    """获取剧本语言列表"""
    return [
        {"value": "zh-CN", "label": "简体中文"},
        {"value": "zh-TW", "label": "繁体中文"},
        {"value": "en-US", "label": "英语"},
        {"value": "ja-JP", "label": "日语"},
        {"value": "ko-KR", "label": "韩语"}
    ]

@router.post("/{script_id}/export")
async def export_script(
    script_id: int,
    format: str = Query("txt", description="导出格式：txt, pdf, docx"),
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """导出剧本"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    
    # 这里可以实现不同格式的导出逻辑
    # 目前返回基本信息
    return {
        "script_id": script_id,
        "title": script.title,
        "format": format,
        "content": script.content,
        "export_time": "2024-01-01T00:00:00Z"
    } 
