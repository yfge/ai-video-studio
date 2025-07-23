from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.script import Story, Episode, Script
from app.schemas.script import (
    ScriptCreate, ScriptUpdate, ScriptResponse, 
    ScriptGenerationRequest
)
from app.services.ai_service import ai_service
import json

router = APIRouter()

@router.post("/", response_model=ScriptResponse)
async def create_script(
    script: ScriptCreate,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=request.format_type,
        language=request.language,
        dialogue_style=request.dialogue_style,
        scene_detail_level=request.scene_detail_level,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI剧本生成失败")
    
    # 解析AI生成的内容
    try:
        ai_content = json.loads(result["content"])
    except json.JSONDecodeError:
        # 如果不是JSON格式，作为纯文本处理
        ai_content = {"content": result["content"]}
    
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
            "style_preferences": request.style_preferences
        },
        status="draft"
    )
    
    db.add(db_script)
    db.commit()
    db.refresh(db_script)
    
    return ScriptResponse.from_orm(db_script)

@router.get("/", response_model=List[ScriptResponse])
async def get_scripts(
    episode_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    format_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
        ai_content = {"content": result["content"]}
    
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
    db: Session = Depends(get_db)
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