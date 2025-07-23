import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate, VirtualIPImageResponse, VirtualIPImageUpdate
from app.services.ai_service import ai_service
import shutil
from datetime import datetime

router = APIRouter()

def save_virtual_ip_image(upload_file: UploadFile, virtual_ip_id: int) -> tuple[str, str, int]:
    """保存虚拟IP图像文件"""
    # 生成唯一文件名
    file_extension = os.path.splitext(upload_file.filename)[1]
    if file_extension.lower() not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    ip_upload_dir = os.path.join(settings.UPLOAD_DIR, "virtual_ips", str(virtual_ip_id))
    os.makedirs(ip_upload_dir, exist_ok=True)
    
    file_path = os.path.join(ip_upload_dir, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        content = upload_file.file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
            )
        buffer.write(content)
    
    return unique_filename, file_path, len(content)

@router.post("/{virtual_ip_id}/images", response_model=VirtualIPImageResponse)
async def create_virtual_ip_image(
    virtual_ip_id: int,
    image: UploadFile = File(...),
    category: str = Form("portrait"),
    tags: str = Form(""),
    is_default: bool = Form(False),
    db: Session = Depends(get_db)
):
    """上传虚拟IP图像"""
    # 检查虚拟IP是否存在
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    
    # 检查文件类型
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ip_{virtual_ip_id}_{timestamp}_{image.filename}"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # 如果设置为默认图像，先取消其他默认图像
    if is_default:
        db.query(VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id,
            VirtualIPImage.is_default == True
        ).update({"is_default": False})
    
    # 创建图像记录
    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id,
        file_path=f"/uploads/{filename}",
        category=category,
        tags=tags.split(",") if tags else [],
        is_default=is_default
    )
    
    db_image = VirtualIPImage(**image_data.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return VirtualIPImageResponse.from_orm(db_image)

@router.post("/{virtual_ip_id}/images/generate", response_model=VirtualIPImageResponse)
async def generate_virtual_ip_image(
    virtual_ip_id: int,
    style: str = Form("realistic"),
    category: str = Form("portrait"),
    additional_prompts: str = Form(""),
    is_default: bool = Form(False),
    db: Session = Depends(get_db)
):
    """使用AI生成虚拟IP图像"""
    # 检查虚拟IP是否存在
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    
    # 使用AI服务生成图像
    additional_prompt_list = [p.strip() for p in additional_prompts.split(",") if p.strip()]
    
    result = await ai_service.generate_virtual_ip_image(
        ip_name=virtual_ip.name,
        description=virtual_ip.description or "",
        style=style,
        category=category,
        additional_prompts=additional_prompt_list
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI图像生成失败")
    
    # 如果设置为默认图像，先取消其他默认图像
    if is_default:
        db.query(VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id,
            VirtualIPImage.is_default == True
        ).update({"is_default": False})
    
    # 创建图像记录
    tags = [style, category, "ai_generated", result["generation_method"]]
    if additional_prompt_list:
        tags.extend(additional_prompt_list)
    
    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id,
        file_path=result["image_url"],
        category=category,
        tags=tags,
        is_default=is_default,
        metadata={
            "generation_method": result["generation_method"],
            "prompt": result["prompt"],
            "style": result["style"],
            "additional_prompts": additional_prompt_list
        }
    )
    
    db_image = VirtualIPImage(**image_data.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return VirtualIPImageResponse.from_orm(db_image)

@router.get("/{virtual_ip_id}/images", response_model=List[VirtualIPImageResponse])
async def get_virtual_ip_images(
    virtual_ip_id: int,
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取虚拟IP的所有图像"""
    # 检查虚拟IP是否存在
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    
    query = db.query(VirtualIPImage).filter(VirtualIPImage.virtual_ip_id == virtual_ip_id)
    
    if category:
        query = query.filter(VirtualIPImage.category == category)
    
    images = query.order_by(VirtualIPImage.is_default.desc(), VirtualIPImage.created_at.desc()).all()
    return [VirtualIPImageResponse.from_orm(image) for image in images]

@router.get("/{virtual_ip_id}/images/{image_id}", response_model=VirtualIPImageResponse)
async def get_virtual_ip_image(
    virtual_ip_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """获取特定虚拟IP图像"""
    image = db.query(VirtualIPImage).filter(
        VirtualIPImage.id == image_id,
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    return VirtualIPImageResponse.from_orm(image)

@router.get("/{virtual_ip_id}/images/{image_id}/download")
def download_virtual_ip_image(
    virtual_ip_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """下载虚拟IP图像文件"""
    image = db.query(VirtualIPImage).filter(
        VirtualIPImage.id == image_id,
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="图像文件不存在")
    
    return FileResponse(
        image.file_path,
        filename=image.original_filename,
        media_type=image.mime_type
    )

@router.put("/{virtual_ip_id}/images/{image_id}", response_model=VirtualIPImageResponse)
async def update_virtual_ip_image(
    virtual_ip_id: int,
    image_id: int,
    image_update: VirtualIPImageUpdate,
    db: Session = Depends(get_db)
):
    """更新虚拟IP图像信息"""
    image = db.query(VirtualIPImage).filter(
        VirtualIPImage.id == image_id,
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    # 如果设置为默认图像，先取消其他默认图像
    if image_update.is_default:
        db.query(VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id,
            VirtualIPImage.is_default == True,
            VirtualIPImage.id != image_id
        ).update({"is_default": False})
    
    # 更新图像信息
    for field, value in image_update.dict(exclude_unset=True).items():
        setattr(image, field, value)
    
    db.commit()
    db.refresh(image)
    
    return VirtualIPImageResponse.from_orm(image)

@router.delete("/{virtual_ip_id}/images/{image_id}")
async def delete_virtual_ip_image(
    virtual_ip_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """删除虚拟IP图像"""
    image = db.query(VirtualIPImage).filter(
        VirtualIPImage.id == image_id,
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    # 删除文件
    if image.file_path and os.path.exists(image.file_path.lstrip("/")):
        try:
            os.remove(image.file_path.lstrip("/"))
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    db.delete(image)
    db.commit()
    
    return {"message": "图像删除成功"}

@router.post("/{virtual_ip_id}/images/{image_id}/set-default")
async def set_default_image(
    virtual_ip_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """设置默认图像"""
    # 检查图像是否存在
    image = db.query(VirtualIPImage).filter(
        VirtualIPImage.id == image_id,
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图像不存在")
    
    # 取消其他默认图像
    db.query(VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip_id,
        VirtualIPImage.is_default == True
    ).update({"is_default": False})
    
    # 设置当前图像为默认
    image.is_default = True
    db.commit()
    
    return {"message": "默认图像设置成功"}

@router.get("/{virtual_ip_id}/images/categories")
async def get_image_categories(
    virtual_ip_id: int,
    db: Session = Depends(get_db)
):
    """获取虚拟IP图像分类列表"""
    # 检查虚拟IP是否存在
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    
    categories = db.query(VirtualIPImage.category).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip_id
    ).distinct().all()
    
    return [category[0] for category in categories] 