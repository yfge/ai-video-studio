from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.schemas.script import (
    StoryCreate, StoryUpdate, StoryResponse, 
    StoryGenerationRequest, StoryCharacterResponse
)
from app.services.ai_service import ai_service
import json

router = APIRouter()

@router.post("/", response_model=StoryResponse)
async def create_story(
    story: StoryCreate,
    db: Session = Depends(get_db)
):
    """创建故事"""
    # 创建故事记录
    story_data = story.dict(exclude={'characters'})
    db_story = Story(**story_data)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    
    # 创建角色关联
    if story.characters:
        for char_data in story.characters:
            # 验证虚拟IP是否存在
            virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == char_data.virtual_ip_id).first()
            if not virtual_ip:
                raise HTTPException(status_code=404, detail=f"虚拟IP {char_data.virtual_ip_id} 不存在")
            
            db_char = StoryCharacter(
                story_id=db_story.id,
                **char_data.dict()
            )
            db.add(db_char)
    
    db.commit()
    db.refresh(db_story)
    
    return StoryResponse.from_orm(db_story)

@router.post("/generate", response_model=StoryResponse)
async def generate_story(
    request: StoryGenerationRequest,
    db: Session = Depends(get_db)
):
    """使用AI生成故事概要"""
    # 获取角色信息
    characters = []
    for char_id in request.character_ids:
        virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == char_id).first()
        if not virtual_ip:
            raise HTTPException(status_code=404, detail=f"虚拟IP {char_id} 不存在")
        
        characters.append({
            "id": virtual_ip.id,
            "name": virtual_ip.name,
            "description": virtual_ip.description,
            "background_story": virtual_ip.background_story,
            "style_prompt": virtual_ip.style_prompt
        })
    
    # 调用AI服务生成故事概要
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
        content_restrictions=request.content_restrictions
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI故事生成失败")
    
    # 解析AI生成的内容
    try:
        ai_content = json.loads(result["content"])
    except json.JSONDecodeError:
        # 如果不是JSON格式，作为文本处理
        ai_content = {"synopsis": result["content"]}
    
    # 创建故事记录
    story_data = {
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
            "content_restrictions": request.content_restrictions
        },
        "tags": request.tags,
        "status": "draft"
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
            role_type="protagonist" if char_id == request.character_ids[0] else "supporting",
            importance=5 if char_id == request.character_ids[0] else 3
        )
        db.add(db_char)
    
    db.commit()
    db.refresh(db_story)
    
    return StoryResponse.from_orm(db_story)

@router.get("/", response_model=List[StoryResponse])
async def get_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取故事列表"""
    query = db.query(Story)
    
    if genre:
        query = query.filter(Story.genre == genre)
    
    if status:
        query = query.filter(Story.status == status)
    
    stories = query.offset(skip).limit(limit).all()
    return [StoryResponse.from_orm(story) for story in stories]

@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    """获取故事详情"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    return StoryResponse.from_orm(story)

@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_update: StoryUpdate,
    db: Session = Depends(get_db)
):
    """更新故事"""
    story = db.query(Story).filter(Story.id == story_id).first()
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
    db: Session = Depends(get_db)
):
    """删除故事"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    db.delete(story)
    db.commit()
    
    return {"message": "故事删除成功"}

@router.get("/{story_id}/characters", response_model=List[StoryCharacterResponse])
async def get_story_characters(
    story_id: int,
    db: Session = Depends(get_db)
):
    """获取故事角色列表"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    
    characters = db.query(StoryCharacter).filter(StoryCharacter.story_id == story_id).all()
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
        {"value": "documentary", "label": "纪录片"}
    ] 