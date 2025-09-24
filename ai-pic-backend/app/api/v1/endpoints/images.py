import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.image import Image
from app.schemas.image import ImageResponse, ImageList
from app.core.middleware import get_current_active_user

router = APIRouter()

def save_upload_file(upload_file: UploadFile, user_id: int) -> tuple[str, str, int]:
    """保存上传的文件"""
    # 生成唯一文件名
    file_extension = os.path.splitext(upload_file.filename)[1]
    if file_extension.lower() not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    file_path = os.path.join(user_upload_dir, unique_filename)
    
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

@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传图片"""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有选择文件"
        )
    
    filename, file_path, file_size = save_upload_file(file, current_user.id)
    
    # 保存到数据库
    db_image = Image(
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        description=description,
        prompt=prompt,
        user_id=current_user.id
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image

@router.get("/", response_model=ImageList)
def get_images(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的图片列表"""
    total = db.query(Image).filter(Image.user_id == current_user.id).count()
    images = db.query(Image).filter(Image.user_id == current_user.id).offset(skip).limit(limit).all()
    
    return ImageList(
        images=images,
        total=total,
        page=skip // limit + 1,
        size=limit
    )

@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取特定图片信息"""
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    return image

@router.get("/{image_id}/download")
def download_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """下载图片文件"""
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    if not os.path.exists(image.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片文件不存在"
        )
    
    return FileResponse(
        image.file_path,
        filename=image.original_filename,
        media_type=image.mime_type
    )

@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除图片"""
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # 删除文件
    if os.path.exists(image.file_path):
        os.remove(image.file_path)
    
    # 删除数据库记录
    db.delete(image)
    db.commit()
    
    return {"message": "图片已删除"} 