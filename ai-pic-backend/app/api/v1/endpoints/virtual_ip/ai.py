from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.virtual_ip import (
    VirtualIPAICreateRequest,
    VirtualIPAIGenerationDetailedResponse,
    VirtualIPAIGenerationRequest,
    VirtualIPAIGenerationResponse,
)
from app.services.virtual_ip_ai_service import virtual_ip_ai_service

router = APIRouter()


@router.post("/generate-ai-content", response_model=VirtualIPAIGenerationResponse)
async def generate_ai_content(
    request: VirtualIPAIGenerationRequest,
    current_user: User = Depends(get_current_active_user),
):
    """生成AI内容（描述、背景故事、人物小传、风格提示词）"""
    try:
        ai_content = await virtual_ip_ai_service.generate_complete_ip(
            name=request.name,
            basic_info=request.basic_info,
            style_preference=request.style_preference,
        )
        style_prompt = await virtual_ip_ai_service.generate_style_prompt(
            name=request.name,
            description=ai_content["description"],
            biography=ai_content["biography"],
            image_category=request.image_category,
        )
        return VirtualIPAIGenerationResponse(
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt,
            tags=ai_content.get("tags", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@router.post("/generate-ai-content-detailed", response_model=VirtualIPAIGenerationDetailedResponse)
async def generate_ai_content_detailed(
    request: VirtualIPAIGenerationRequest,
    current_user: User = Depends(get_current_active_user),
):
    """生成AI内容（包含详细生成信息）"""
    try:
        result = await virtual_ip_ai_service.generate_complete_ip_with_details(
            name=request.name,
            basic_info=request.basic_info,
            style_preference=request.style_preference,
        )
        ai_content = result["content"]
        generation_details = result["generation_details"]
        style_prompt = await virtual_ip_ai_service.generate_style_prompt(
            name=request.name,
            description=ai_content["description"],
            biography=ai_content["biography"],
            image_category=request.image_category,
        )
        generation_details["prompts_used"].append("风格提示词生成: 基于角色信息生成AI绘画提示词...")
        return VirtualIPAIGenerationDetailedResponse(
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt,
            tags=ai_content.get("tags", []),
            generation_details=generation_details,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")


@router.post("/create-with-ai")
async def create_virtual_ip_with_ai(
    request: VirtualIPAICreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """使用AI增强功能创建虚拟IP"""
    try:
        existing_ip = db.query(VirtualIP).filter(VirtualIP.name == request.name).first()
        if existing_ip:
            raise HTTPException(status_code=400, detail="虚拟IP名称已存在")

        ai_content = await virtual_ip_ai_service.generate_complete_ip(
            name=request.name,
            basic_info=request.basic_info,
            style_preference=request.style_preference,
        )
        style_prompt = await virtual_ip_ai_service.generate_style_prompt(
            name=request.name,
            description=ai_content["description"],
            biography=ai_content["biography"],
            image_category="portrait",
        )
        tags = request.tags if request.tags else ai_content.get("tags") or []

        db_ip = VirtualIP(
            user_id=current_user.id,
            name=request.name,
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt,
            tags=tags,
            is_active=request.is_active,
            is_public=request.is_public,
        )

        db.add(db_ip)
        db.commit()
        db.refresh(db_ip)
        return {"success": True, "data": db_ip}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
