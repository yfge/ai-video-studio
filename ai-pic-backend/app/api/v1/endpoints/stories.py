from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.core.middleware import get_current_active_user
from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.schemas.script import (
    StoryCreate,
    StoryUpdate,
    StoryResponse,
    StoryGenerationRequest,
    StoryCharacterResponse,
)
from app.services.ai_service import ai_service
from app.utils.story_parser import (
    normalize_story_json_keys,
    extract_outline_from_text,
)
from app.utils.json_utils import extract_json_block
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
import json
from app.models.task import Task, TaskType, TaskStatus
from app.services.task_worker import story_generate_task

router = APIRouter()

_EXTRA_METADATA_EXCLUDE = {
    "premise",
    "synopsis",
    "main_conflict",
    "resolution",
    "main_characters",
    "character_relationships",
}


def _build_extra_metadata(ai_content):
    if not isinstance(ai_content, dict):
        return {}
    return {k: v for k, v in ai_content.items() if k not in _EXTRA_METADATA_EXCLUDE}


@router.post("/", response_model=StoryResponse)
async def create_story(
    story: StoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建故事"""
    # 创建故事记录
    story_data = story.dict(exclude={"characters"})
    db_story = Story(user_id=current_user.id, **story_data)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)

    # 创建角色关联
    if story.characters:
        for char_data in story.characters:
            # 验证虚拟IP是否存在
            virtual_ip = (
                db.query(VirtualIP)
                .filter(VirtualIP.id == char_data.virtual_ip_id)
                .first()
            )
            if not virtual_ip:
                raise HTTPException(
                    status_code=404, detail=f"虚拟IP {char_data.virtual_ip_id} 不存在"
                )

            db_char = StoryCharacter(story_id=db_story.id, **char_data.dict())
            db.add(db_char)

    db.commit()
    db.refresh(db_story)

    return StoryResponse.from_orm(db_story)


@router.post("/generate")
async def generate_story(
    request: StoryGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """使用AI生成故事概要"""
    # 获取角色信息
    characters = []
    for char_id in request.character_ids:
        vip_query = db.query(VirtualIP).filter(VirtualIP.id == char_id)
        if not current_user.is_admin and not current_user.is_superuser:
            vip_query = vip_query.filter(VirtualIP.user_id == current_user.id)
        virtual_ip = vip_query.first()
        if not virtual_ip:
            raise HTTPException(status_code=404, detail=f"虚拟IP {char_id} 不存在")

        characters.append(
            {
                "id": virtual_ip.id,
                "name": virtual_ip.name,
                "description": virtual_ip.description,
                "background_story": virtual_ip.background_story,
                "style_prompt": virtual_ip.style_prompt,
            }
        )

    # 调用AI服务生成故事概要
    # 解析统一模型ID（provider:model）
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    result = await ai_service.generate_story_outline(
        title=request.title,
        genre=request.genre,
        characters=characters,
        theme=request.theme,
        target_audience=request.target_audience,
        duration_minutes=request.duration_minutes,
        setting_time=request.setting_time,
        setting_location=request.setting_location,
        world_building=request.world_building,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        content_restrictions=request.content_restrictions,
        model=model_id,
        temperature=request.temperature or 0.7,
        prefer_provider=prefer_provider,
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI故事生成失败")

    # 解析AI生成的内容（优先JSON，兜底文本抽取）
    normalized = result.get("normalized") if isinstance(result, dict) else None
    raw = normalized or extract_json_block(
        result.get("content") if isinstance(result, dict) else None
    )
    if raw:
        ai_content = normalize_story_json_keys(raw)
    else:
        ai_content = extract_outline_from_text(
            result.get("content") if isinstance(result, dict) else ""
        )

    # 结构化 agent 运行信息，便于排查与审计
    agent_run = {}
    if isinstance(result, dict):
        agent_run = {
            "generation_method": result.get("generation_method"),
            "template_used": result.get("template_used"),
            "provider_used": result.get("provider_used"),
            "model_used": result.get("model_used"),
            "usage": result.get("usage"),
            "reasoning": result.get("reasoning"),
        }

    extra_metadata = _build_extra_metadata(ai_content)
    if agent_run:
        extra_metadata = {**extra_metadata, "agent_run": agent_run}

    # 创建故事记录
    story_data = {
        "user_id": current_user.id,
        "title": request.title,
        "genre": request.genre,
        "theme": request.theme,
        "target_audience": request.target_audience,
        "duration_minutes": request.duration_minutes,
        "setting_time": request.setting_time,
        "setting_location": request.setting_location,
        "world_building": request.world_building,
        "premise": ai_content.get("premise"),
        "synopsis": ai_content.get("synopsis"),
        "main_conflict": ai_content.get("main_conflict"),
        "resolution": ai_content.get("resolution"),
        "main_characters": ai_content.get("main_characters"),
        "character_relationships": ai_content.get("character_relationships"),
        "generation_prompt": result["prompt"],
        "ai_model": result["generation_method"],
        "generation_params": {
            "character_ids": request.character_ids,
            "additional_requirements": request.additional_requirements,
            "style_preferences": request.style_preferences,
            "content_restrictions": request.content_restrictions,
            "model": request.model,
            "temperature": request.temperature or 0.7,
        },
        "tags": request.tags,
        "extra_metadata": extra_metadata,
        "status": "draft",
    }

    db_story = Story(**story_data)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)

    # 创建角色关联
    for char_id in request.character_ids:
        db_char = StoryCharacter(
            story_id=db_story.id,
            virtual_ip_id=char_id,
            role_type=(
                "protagonist" if char_id == request.character_ids[0] else "supporting"
            ),
            importance=5 if char_id == request.character_ids[0] else 3,
        )
        db.add(db_char)

    db.commit()
    db.refresh(db_story)

    return {"success": True, "data": StoryResponse.from_orm(db_story)}


@router.post("/prompt/preview")
async def preview_story_prompt(
    request: StoryGenerationRequest,
):
    """返回根据请求生成的最终提示词（不调用模型）"""
    # 构造用于模板的角色结构
    characters = []
    # 仅包含ID，不查库提升性能；前端仅用于预览结构，实际查库在生成接口
    for char_id in request.character_ids:
        characters.append({"id": char_id, "name": f"角色#{char_id}", "description": ""})

    variables = {
        "title": request.title,
        "genre": request.genre,
        "characters": characters,
        "theme": request.theme,
        "target_audience": request.target_audience,
        "duration_minutes": request.duration_minutes,
        "setting_time": request.setting_time,
        "setting_location": request.setting_location,
        "world_building": request.world_building,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
        "content_restrictions": request.content_restrictions or [],
    }
    prompt = PromptManager().render_prompt(
        PromptTemplate.STORY_OUTLINE.value, variables
    )
    return {"success": True, "data": {"prompt": prompt}}


def _process_story_generation_task(task_id: int, request_dict: dict, user_id: int):
    """后台处理故事生成任务（同步函数供BackgroundTasks调用）"""
    db = SessionLocal()
    try:
        # 更新任务为 processing
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        # 补充角色详细信息
        characters = []
        for char_id in request_dict.get("character_ids", []):
            vip = (
                db.query(VirtualIP)
                .filter(VirtualIP.id == char_id, VirtualIP.user_id == user_id)
                .first()
            )
            if vip:
                characters.append(
                    {
                        "id": vip.id,
                        "name": vip.name,
                        "description": vip.description,
                        "background_story": vip.background_story,
                        "style_prompt": vip.style_prompt,
                    }
                )

        import anyio

        # 调用AI服务（需要运行异步函数）
        async def _run():
            prefer_provider = None
            model_id = request_dict.get("model")
            if model_id and ":" in model_id:
                prefer_provider, model_id = model_id.split(":", 1)
            return await ai_service.generate_story_outline(
                title=request_dict.get("title"),
                genre=request_dict.get("genre"),
                characters=characters,
                theme=request_dict.get("theme"),
                target_audience=request_dict.get("target_audience"),
                duration_minutes=request_dict.get("duration_minutes"),
                setting_time=request_dict.get("setting_time"),
                setting_location=request_dict.get("setting_location"),
                world_building=request_dict.get("world_building"),
                additional_requirements=request_dict.get("additional_requirements"),
                style_preferences=request_dict.get("style_preferences"),
                content_restrictions=request_dict.get("content_restrictions"),
                model=model_id,
                temperature=request_dict.get("temperature", 0.7),
                prefer_provider=prefer_provider,
            )

        result = anyio.run(_run)
        if not result:
            raise RuntimeError("AI故事生成失败")

        # 解析内容并创建故事
        normalized = result.get("normalized") if isinstance(result, dict) else None
        raw = normalized or extract_json_block(
            result.get("content") if isinstance(result, dict) else None
        )
        if raw:
            ai_content = normalize_story_json_keys(raw)
        else:
            ai_content = extract_outline_from_text(result.get("content") or "")

        # 结构化 agent 运行信息，方便落库与排查
        agent_run = {}
        if isinstance(result, dict):
            agent_run = {
                "generation_method": result.get("generation_method"),
                "template_used": result.get("template_used"),
                "provider_used": result.get("provider_used"),
                "model_used": result.get("model_used"),
                "usage": result.get("usage"),
                "reasoning": result.get("reasoning"),
            }

        story_data = {
            "user_id": user_id,
            "title": request_dict.get("title"),
            "genre": request_dict.get("genre"),
            "theme": request_dict.get("theme"),
            "target_audience": request_dict.get("target_audience"),
            "duration_minutes": request_dict.get("duration_minutes"),
            "setting_time": request_dict.get("setting_time"),
            "setting_location": request_dict.get("setting_location"),
            "world_building": request_dict.get("world_building"),
            "premise": ai_content.get("premise"),
            "synopsis": ai_content.get("synopsis"),
            "main_conflict": ai_content.get("main_conflict"),
            "resolution": ai_content.get("resolution"),
            "main_characters": ai_content.get("main_characters"),
            "character_relationships": ai_content.get("character_relationships"),
            "generation_prompt": result.get("prompt"),
            "ai_model": result.get("generation_method"),
            "generation_params": {
                **{
                    k: request_dict.get(k)
                    for k in [
                        "character_ids",
                        "additional_requirements",
                        "style_preferences",
                        "content_restrictions",
                        "model",
                        "temperature",
                    ]
                }
            },
            "tags": request_dict.get("tags"),
            "extra_metadata": {
                **_build_extra_metadata(ai_content),
                "agent_run": agent_run,
            },
            "status": "draft",
        }

        story = Story(**story_data)
        db.add(story)
        db.commit()
        db.refresh(story)

        # 角色关联
        for cid in request_dict.get("character_ids", []):
            char = StoryCharacter(
                story_id=story.id,
                virtual_ip_id=cid,
                role_type=(
                    "protagonist"
                    if cid == request_dict.get("character_ids", [cid])[0]
                    else "supporting"
                ),
                importance=(
                    5 if cid == request_dict.get("character_ids", [cid])[0] else 3
                ),
            )
            db.add(char)
        db.commit()

        # 完成任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"story:{story.id}"
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
async def generate_story_async(
    request: StoryGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成故事：创建任务并在后台生成"""
    # 创建任务
    task = Task(
        title=f"生成故事 - {request.title}",
        description="异步故事生成",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=f"Story outline: {request.title}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 后台处理：交给 Celery worker，而非本进程 BackgroundTasks
    story_generate_task.delay(task.id, request.dict(), current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


@router.get("/")
async def get_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事列表"""
    query = db.query(Story)

    # 普通用户只查看自己的故事，管理员/超级用户可查看全部
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)

    if genre:
        query = query.filter(Story.genre == genre)

    if status:
        query = query.filter(Story.status == status)

    stories = query.offset(skip).limit(limit).all()
    return {
        "success": True,
        "data": [StoryResponse.from_orm(story) for story in stories],
    }


@router.get("", include_in_schema=False)
async def get_stories_no_slash(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    兼容无尾斜杠的 /api/v1/stories 请求，避免 307 重定向。

    内部直接复用 get_stories 的过滤与分页逻辑。
    """
    return await get_stories(
        skip=skip,
        limit=limit,
        genre=genre,
        status=status,
        current_user=current_user,
        db=db,
    )


@router.get("/{story_id}")
async def get_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事详情"""
    query = db.query(Story).filter(Story.id == story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    story = query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    return {"success": True, "data": StoryResponse.from_orm(story)}


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_update: StoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新故事"""
    query = db.query(Story).filter(Story.id == story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    story = query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    # 更新故事信息
    for field, value in story_update.dict(exclude_unset=True).items():
        setattr(story, field, value)

    db.commit()
    db.refresh(story)

    return StoryResponse.from_orm(story)


@router.delete("/{story_id}")
async def delete_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除故事"""
    query = db.query(Story).filter(Story.id == story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    story = query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    db.delete(story)
    db.commit()

    return {"message": "故事删除成功"}


@router.get("/{story_id}/characters", response_model=List[StoryCharacterResponse])
async def get_story_characters(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事角色列表"""
    query = db.query(Story).filter(Story.id == story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    story = query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    characters = (
        db.query(StoryCharacter).filter(StoryCharacter.story_id == story_id).all()
    )
    return [StoryCharacterResponse.from_orm(char) for char in characters]


@router.get("/genres")
async def get_story_genres():
    """获取故事类型列表"""
    return [
        {"value": "drama", "label": "剧情"},
        {"value": "comedy", "label": "喜剧"},
        {"value": "romance", "label": "爱情"},
        {"value": "thriller", "label": "惊悚"},
        {"value": "action", "label": "动作"},
        {"value": "fantasy", "label": "奇幻"},
        {"value": "sci-fi", "label": "科幻"},
        {"value": "horror", "label": "恐怖"},
        {"value": "mystery", "label": "悬疑"},
        {"value": "historical", "label": "历史"},
        {"value": "biographical", "label": "传记"},
        {"value": "documentary", "label": "纪录片"},
    ]
