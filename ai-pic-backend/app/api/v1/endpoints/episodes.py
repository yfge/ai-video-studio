from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import BackgroundTasks
from app.core.database import get_db
from app.models.user import User
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.schemas.script import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse, 
    EpisodeGenerationRequest
)
from app.services.ai_service import ai_service
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
import json

router = APIRouter()

@router.post("/", response_model=EpisodeResponse)
async def create_episode(
    episode: EpisodeCreate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """创建剧集"""
    # 检查故事是否存在
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    # 检查集数是否重复
    existing_episode = db.query(Episode).filter(
        Episode.story_id == episode.story_id,
        Episode.episode_number == episode.episode_number
    ).first()
    if existing_episode:
        raise HTTPException(status_code=400, detail="该集数已存在")
    
    db_episode = Episode(**episode.dict())
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)
    
    return EpisodeResponse.from_orm(db_episode)

@router.post("/generate", response_model=List[EpisodeResponse])
async def generate_episodes(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """使用AI生成剧集"""
    # 获取故事信息
    story = db.query(Story).filter(Story.id == request.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    # 获取重点角色信息
    focus_characters = []
    if request.focus_characters:
        for char_id in request.focus_characters:
            virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == char_id).first()
            if virtual_ip:
                focus_characters.append({
                    "id": virtual_ip.id,
                    "name": virtual_ip.name,
                    "description": virtual_ip.description
                })
    
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
    
    # 调用AI服务生成剧集
    # 解析模型与提供商
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    result = await ai_service.generate_episodes(
        story=story_data,
        episode_count=request.episode_count,
        episode_duration=request.episode_duration,
        focus_characters=focus_characters,
        plot_complexity=request.plot_complexity,
        pacing=request.pacing,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.7
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI剧集生成失败")
    
    # 解析AI生成的内容
    try:
        ai_content = json.loads(result["content"])
        episodes_data = ai_content.get("episodes", [])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI生成内容格式错误")
    
    # 创建剧集记录
    created_episodes = []
    for i, episode_data in enumerate(episodes_data[:request.episode_count]):
        # 检查集数是否重复
        episode_number = episode_data.get("episode_number", i + 1)
        existing_episode = db.query(Episode).filter(
            Episode.story_id == request.story_id,
            Episode.episode_number == episode_number
        ).first()
        
        if existing_episode:
            continue  # 跳过已存在的集数
        
        # 提取额外元数据
        known_keys = {"episode_number", "title", "summary", "plot_points", "character_arcs", "conflicts", "scene_count"}
        extra_meta = {k: v for k, v in episode_data.items() if k not in known_keys}

        db_episode = Episode(
            story_id=request.story_id,
            episode_number=episode_number,
            title=episode_data.get("title", f"第{episode_number}集"),
            summary=episode_data.get("summary"),
            plot_points=episode_data.get("plot_points"),
            character_arcs=episode_data.get("character_arcs"),
            conflicts=episode_data.get("conflicts"),
            duration_minutes=request.episode_duration,
            scene_count=episode_data.get("scene_count"),
            generation_prompt=result["prompt"],
            ai_model=result["generation_method"],
            generation_params={
                "focus_characters": request.focus_characters,
                "plot_complexity": request.plot_complexity,
                "pacing": request.pacing,
                "additional_requirements": request.additional_requirements,
                "style_preferences": request.style_preferences
            },
            extra_metadata=extra_meta or None,
            status="draft"
        )
        
        db.add(db_episode)
        created_episodes.append(db_episode)
    
    db.commit()
    
    # 刷新所有创建的剧集
    for episode in created_episodes:
        db.refresh(episode)
    
    return [EpisodeResponse.from_orm(episode) for episode in created_episodes]


@router.post("/prompt/preview")
async def preview_episode_prompt(
    request: EpisodeGenerationRequest,
    db: Session = Depends(get_db)
):
    """返回剧集生成的最终提示词（不调用模型）"""
    story = db.query(Story).filter(Story.id == request.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

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

    focus_characters = []
    if request.focus_characters:
        for cid in request.focus_characters:
            vip = db.query(VirtualIP).filter(VirtualIP.id == cid).first()
            if vip:
                focus_characters.append({
                    "id": vip.id,
                    "name": vip.name,
                    "description": vip.description
                })

    variables = {
        "story": story_data,
        "episode_count": request.episode_count,
        "episode_duration": request.episode_duration,
        "focus_characters": focus_characters,
        "plot_complexity": request.plot_complexity,
        "pacing": request.pacing,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or []
    }
    prompt = PromptManager().render_prompt(PromptTemplate.EPISODE_GENERATION.value, variables)
    return {"success": True, "data": {"prompt": prompt}}

@router.get("/", response_model=List[EpisodeResponse])
async def get_episodes(
    story_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取剧集列表"""
    query = db.query(Episode)
    
    if story_id:
        query = query.filter(Episode.story_id == story_id)
    
    if status:
        query = query.filter(Episode.status == status)
    
    episodes = query.order_by(Episode.story_id, Episode.episode_number).offset(skip).limit(limit).all()
    return [EpisodeResponse.from_orm(episode) for episode in episodes]

@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取剧集详情"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    return EpisodeResponse.from_orm(episode)

@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    episode_update: EpisodeUpdate,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """更新剧集"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    # 如果更新集数，检查是否重复
    if episode_update.episode_number and episode_update.episode_number != episode.episode_number:
        existing_episode = db.query(Episode).filter(
            Episode.story_id == episode.story_id,
            Episode.episode_number == episode_update.episode_number,
            Episode.id != episode_id
        ).first()
        if existing_episode:
            raise HTTPException(status_code=400, detail="该集数已存在")
    
    # 更新剧集信息
    for field, value in episode_update.dict(exclude_unset=True).items():
        setattr(episode, field, value)
    
    db.commit()
    db.refresh(episode)
    
    return EpisodeResponse.from_orm(episode)

@router.delete("/{episode_id}")
async def delete_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """删除剧集"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    db.delete(episode)
    db.commit()
    
    return {"message": "剧集删除成功"}

@router.get("/story/{story_id}")
async def get_story_episodes(
    story_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取故事的所有剧集"""
    # 检查故事是否存在
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    episodes = db.query(Episode).filter(Episode.story_id == story_id).order_by(Episode.episode_number).all()
    return {
        "success": True,
        "data": [EpisodeResponse.from_orm(episode) for episode in episodes] if episodes else []
    }

@router.post("/{episode_id}/regenerate", response_model=EpisodeResponse)
async def regenerate_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """重新生成剧集内容"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
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
    original_params = episode.generation_params or {}
    
    # 调用AI服务重新生成单集内容
    result = await ai_service.generate_episodes(
        story=story_data,
        episode_count=1,
        episode_duration=episode.duration_minutes,
        focus_characters=None,
        plot_complexity=original_params.get("plot_complexity", "medium"),
        pacing=original_params.get("pacing", "medium"),
        additional_requirements=f"重新生成第{episode.episode_number}集的内容",
        style_preferences=original_params.get("style_preferences")
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI剧集重新生成失败")
    
    # 解析AI生成的内容
    try:
        ai_content = json.loads(result["content"])
        episodes_data = ai_content.get("episodes", [])
        if episodes_data:
            episode_data = episodes_data[0]
            scenes, scene_count = _ensure_scenes(episode_data)

            # 更新剧集内容
            episode.summary = episode_data.get("summary")
            episode.plot_points = episode_data.get("plot_points")
            episode.character_arcs = episode_data.get("character_arcs")
            episode.conflicts = episode_data.get("conflicts")
            episode.scene_count = scene_count
            known_keys = {"episode_number", "title", "summary", "plot_points", "character_arcs", "conflicts", "scene_count"}
            extra_meta = {k: v for k, v in episode_data.items() if k not in known_keys} or {}
            if scenes and "scenes" not in extra_meta:
                extra_meta["scenes"] = scenes
            episode.extra_metadata = extra_meta or None
            episode.generation_prompt = result["prompt"]
            episode.ai_model = result["generation_method"]
            
            db.commit()
            db.refresh(episode)
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI生成内容格式错误")
    
    return EpisodeResponse.from_orm(episode)


def _process_episode_generation_task(task_id: int, request_dict: dict, user_id: int):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        story = db.query(Story).filter(Story.id == request_dict.get("story_id")).first()
        if not story:
            raise RuntimeError("故事不存在")

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

        focus_characters = []
        for cid in request_dict.get("focus_characters") or []:
            vip = db.query(VirtualIP).filter(VirtualIP.id == cid).first()
            if vip:
                focus_characters.append({"id": vip.id, "name": vip.name, "description": vip.description})

        import anyio

        async def _run():
            prefer_provider = None
            model_id = request_dict.get("model")
            if model_id and ":" in model_id:
                prefer_provider, model_id = model_id.split(":", 1)
            return await ai_service.generate_episodes(
                story=story_data,
                episode_count=request_dict.get("episode_count"),
                episode_duration=request_dict.get("episode_duration"),
                focus_characters=focus_characters,
                plot_complexity=request_dict.get("plot_complexity", "medium"),
                pacing=request_dict.get("pacing", "medium"),
                additional_requirements=request_dict.get("additional_requirements"),
                style_preferences=request_dict.get("style_preferences"),
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7)
            )

        result = anyio.run(_run)
        if not result:
            raise RuntimeError("AI剧集生成失败")

        import json as _json
        try:
            content = _json.loads(result["content"]) if isinstance(result["content"], str) else result["content"]
            episodes_data = content.get("episodes", [])
        except Exception:
            raise RuntimeError("AI生成内容格式错误")

        created_ids = []
        for i, ep_data in enumerate(episodes_data[: request_dict.get("episode_count", 1)]):
            episode_number = ep_data.get("episode_number", i + 1)
            exists = db.query(Episode).filter(Episode.story_id == story.id, Episode.episode_number == episode_number).first()
            if exists:
                continue
            scenes, scene_count = _ensure_scenes(ep_data)
            known_keys = {"episode_number", "title", "summary", "plot_points", "character_arcs", "conflicts", "scene_count"}
            extra_meta = {k: v for k, v in ep_data.items() if k not in known_keys}
            if scenes and "scenes" not in extra_meta:
                extra_meta["scenes"] = scenes
            ep = Episode(
                story_id=story.id,
                episode_number=episode_number,
                title=ep_data.get("title", f"第{episode_number}集"),
                summary=ep_data.get("summary"),
                plot_points=ep_data.get("plot_points"),
                character_arcs=ep_data.get("character_arcs"),
                conflicts=ep_data.get("conflicts"),
                duration_minutes=request_dict.get("episode_duration"),
                scene_count=scene_count,
                generation_prompt=result.get("prompt"),
                ai_model=result.get("generation_method"),
                generation_params={k: request_dict.get(k) for k in ["focus_characters","plot_complexity","pacing","additional_requirements","style_preferences","model","temperature"]},
                extra_metadata=extra_meta or None,
                status="draft"
            )
            db.add(ep)
            db.commit()
            db.refresh(ep)
            created_ids.append(ep.id)

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"episodes:{','.join(map(str, created_ids))}"
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
async def generate_episodes_async(
    request: EpisodeGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    from app.models.task import Task
    t = Task(
        title=f"生成剧集 - 故事{request.story_id}",
        description="异步剧集生成",
        task_type="image_generation",
        prompt=f"Episode plan for story {request.story_id}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    background_tasks.add_task(_process_episode_generation_task, t.id, request.dict(), current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}
def _ensure_scenes(ep_data: dict) -> tuple[list[dict], int | None]:
    """确保剧集数据包含 scenes，若缺失则基于 plot_points 生成占位."""
    scenes = ep_data.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    if not scenes:
        plot_points = ep_data.get("plot_points") or []
        if isinstance(plot_points, list) and plot_points:
            for idx, pp in enumerate(plot_points, start=1):
                desc = None
                timing = None
                if isinstance(pp, dict):
                    desc = pp.get("description")
                    timing = pp.get("timing")
                scenes.append(
                    {
                        "scene_number": idx,
                        "slug_line": f"SCENE {idx} - {timing or 'beat'}",
                        "summary": desc or "本场景推进剧情。",
                        "time_of_day": "unspecified",
                        "location": "unspecified",
                    }
                )
        else:
            scenes.append(
                {
                    "scene_number": 1,
                    "slug_line": "SCENE 1 - beat",
                    "summary": ep_data.get("summary") or "本集开篇场景。",
                    "time_of_day": "unspecified",
                    "location": "unspecified",
                }
            )
    scene_count = ep_data.get("scene_count")
    if not scene_count and scenes:
        scene_count = len(scenes)
    return scenes, scene_count
