from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.virtual_ip import VirtualIP
from app.models.user import User
from app.schemas.virtual_ip import (
    VirtualIPCreate, VirtualIPUpdate, VirtualIPResponse,
    VirtualIPAICreateRequest, VirtualIPAIGenerationResponse, VirtualIPAIGenerationRequest,
    VirtualIPAIGenerationDetailedResponse
)
from app.core.middleware import get_current_active_user
from app.services.virtual_ip_ai_service import virtual_ip_ai_service

router = APIRouter()

@router.get("/")
def list_virtual_ips(
    skip: int = 0, 
    limit: int = 20, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    virtual_ips = db.query(VirtualIP).offset(skip).limit(limit).all()
    return {
        "success": True,
        "data": [VirtualIPResponse.from_orm(ip) for ip in virtual_ips]
    }

@router.post("/")
def create_virtual_ip(
    ip: VirtualIPCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_ip = VirtualIP(**ip.dict())
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return {
        "success": True,
        "data": VirtualIPResponse.from_orm(db_ip)
    }

@router.get("/{ip_id}")
def get_virtual_ip(
    ip_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return {
        "success": True,
        "data": VirtualIPResponse.from_orm(ip)
    }

@router.put("/{ip_id}")
def update_virtual_ip(
    ip_id: int, 
    ip_update: VirtualIPUpdate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    for k, v in ip_update.dict(exclude_unset=True).items():
        setattr(ip, k, v)
    db.commit()
    db.refresh(ip)
    return {
        "success": True,
        "data": VirtualIPResponse.from_orm(ip)
    }

@router.delete("/{ip_id}")
def delete_virtual_ip(
    ip_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ip = db.query(VirtualIP).filter(VirtualIP.id == ip_id).first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    db.delete(ip)
    db.commit()
    return {
        "success": True,
        "message": "虚拟IP已删除"
    }

@router.post("/generate-ai-content", response_model=VirtualIPAIGenerationResponse)
async def generate_ai_content(
    request: VirtualIPAIGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成AI内容（描述、背景故事、人物小传、风格提示词）"""
    try:
        # 生成完整的AI内容
        ai_content = await virtual_ip_ai_service.generate_complete_ip(
            name=request.name,
            basic_info=request.basic_info,
            style_preference=request.style_preference
        )
        
        # 生成风格提示词
        style_prompt = await virtual_ip_ai_service.generate_style_prompt(
            name=request.name,
            description=ai_content["description"],
            biography=ai_content["biography"],
            image_category=request.image_category
        )
        
        return VirtualIPAIGenerationResponse(
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI生成失败: {str(e)}"
        )

@router.post("/generate-ai-content-detailed", response_model=VirtualIPAIGenerationDetailedResponse)
async def generate_ai_content_detailed(
    request: VirtualIPAIGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成AI内容（包含详细生成信息）"""
    try:
        # 生成完整的AI内容（包含详细信息）
        result = await virtual_ip_ai_service.generate_complete_ip_with_details(
            name=request.name,
            basic_info=request.basic_info,
            style_preference=request.style_preference
        )
        
        ai_content = result["content"]
        generation_details = result["generation_details"]
        
        # 生成风格提示词
        style_prompt = await virtual_ip_ai_service.generate_style_prompt(
            name=request.name,
            description=ai_content["description"],
            biography=ai_content["biography"],
            image_category=request.image_category
        )
        
        # 添加风格提示词生成信息
        generation_details["prompts_used"].append(f"风格提示词生成: 基于角色信息生成AI绘画提示词...")
        
        return VirtualIPAIGenerationDetailedResponse(
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt,
            generation_details=generation_details
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI生成失败: {str(e)}"
        )

@router.post("/create-with-ai")
async def create_virtual_ip_with_ai(
    request: VirtualIPAICreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """使用AI增强功能创建虚拟IP"""
    try:
        # 检查名称是否已存在
        existing_ip = db.query(VirtualIP).filter(VirtualIP.name == request.name).first()
        if existing_ip:
            raise HTTPException(status_code=400, detail="虚拟IP名称已存在")
        
        # 生成AI内容
        ai_content = await virtual_ip_ai_service.generate_complete_ip(
            name=request.name,
            basic_info=request.basic_info,
            style_preference=request.style_preference
        )
        
        # 生成风格提示词
        style_prompt = await virtual_ip_ai_service.generate_style_prompt(
            name=request.name,
            description=ai_content["description"],
            biography=ai_content["biography"],
            image_category="portrait"
        )
        
        # 创建虚拟IP
        db_ip = VirtualIP(
            name=request.name,
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt,
            tags=request.tags,
            is_active=request.is_active,
            is_public=request.is_public
        )
        
        db.add(db_ip)
        db.commit()
        db.refresh(db_ip)
        
        return {
            "success": True,
            "data": VirtualIPResponse.from_orm(db_ip),
            "message": "AI增强虚拟IP创建成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"创建失败: {str(e)}"
        ) 