from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
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


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def _get_owned_virtual_ip(
    db: Session,
    current_user: User,
    ip_id: int,
) -> VirtualIP:
    """获取当前用户可访问的虚拟 IP（非管理员只能访问自己的资产）。"""
    query = _not_deleted(db.query(VirtualIP), VirtualIP).filter(VirtualIP.id == ip_id)
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(VirtualIP.user_id == current_user.id)
    ip = query.first()
    if not ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return ip

@router.get("/")
def list_virtual_ips(
    skip: int = 0, 
    limit: int = 20, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = _not_deleted(db.query(VirtualIP), VirtualIP)
    # 普通用户只看到自己的虚拟 IP，管理员/超级用户可以查看全部
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(VirtualIP.user_id == current_user.id)
    virtual_ips = query.offset(skip).limit(limit).all()
    return {
        "success": True,
        "data": [VirtualIPResponse.from_orm(ip) for ip in virtual_ips]
    }


@router.get("", include_in_schema=False)
def list_virtual_ips_no_slash(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    兼容无尾斜杠的 /api/v1/virtual-ips 请求，避免 307 重定向。

    内部直接复用 list_virtual_ips 的分页与权限逻辑。
    """
    return list_virtual_ips(skip=skip, limit=limit, current_user=current_user, db=db)

@router.post("/")
def create_virtual_ip(
    ip: VirtualIPCreate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    existing_ip = (
        _not_deleted(db.query(VirtualIP), VirtualIP)
        .filter(VirtualIP.name == ip.name)
        .first()
    )
    if existing_ip:
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")

    db_ip = VirtualIP(user_id=current_user.id, **ip.dict())
    db.add(db_ip)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")
    except Exception:
        db.rollback()
        raise

    db.refresh(db_ip)
    return {"success": True, "data": VirtualIPResponse.from_orm(db_ip)}

@router.get("/{ip_id}")
def get_virtual_ip(
    ip_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ip = _get_owned_virtual_ip(db, current_user, ip_id)
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
    ip = _get_owned_virtual_ip(db, current_user, ip_id)

    updates = ip_update.dict(exclude_unset=True)
    if "name" in updates and updates["name"] != ip.name:
        existing_ip = (
            _not_deleted(db.query(VirtualIP), VirtualIP)
            .filter(VirtualIP.name == updates["name"])
            .first()
        )
        if existing_ip:
            raise HTTPException(status_code=400, detail="虚拟IP名称已存在")

    for k, v in updates.items():
        setattr(ip, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="虚拟IP名称已存在")
    except Exception:
        db.rollback()
        raise

    db.refresh(ip)
    return {"success": True, "data": VirtualIPResponse.from_orm(ip)}

@router.delete("/{ip_id}")
def delete_virtual_ip(
    ip_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    ip = _get_owned_virtual_ip(db, current_user, ip_id)
    ip.soft_delete(user_id=current_user.id, reason="user delete")
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
            user_id=current_user.id,
            name=request.name,
            description=ai_content["description"],
            background_story=ai_content["background_story"],
            biography=ai_content["biography"],
            style_prompt=style_prompt,
            tags=request.tags,
            is_active=request.is_active,
            is_public=request.is_public,
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
