import os
import uuid
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.image import Image
from app.models.user import User
from app.schemas.image import ImageList, ImageResponse
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

router = APIRouter()


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def _get_image_by_identifier(
    db: Session,
    image_id: Optional[int],
    image_business_id: Optional[str],
    user_id: int,
) -> Image:
    query = _not_deleted(db.query(Image), Image).filter(Image.user_id == user_id)
    if image_business_id:
        query = query.filter(Image.business_id == image_business_id)
    elif image_id is not None:
        query = query.filter(Image.id == image_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="image identifier missing"
        )
    image = query.first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    return image


def save_upload_file(upload_file: UploadFile, user_id: int) -> tuple[str, str, int]:
    """保存上传的文件"""
    # 生成唯一文件名
    file_extension = os.path.splitext(upload_file.filename)[1]
    if file_extension.lower() not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}",
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
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
            )
        buffer.write(content)

    return unique_filename, file_path, len(content)


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传图片"""
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="没有选择文件"
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
        user_id=current_user.id,
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
    current_user: User = Depends(get_current_active_user),
):
    """获取用户的图片列表"""
    query = _not_deleted(db.query(Image), Image).filter(
        Image.user_id == current_user.id
    )
    total = query.count()
    images = query.offset(skip).limit(limit).all()

    return ImageList(images=images, total=total, page=skip // limit + 1, size=limit)


@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: int,
    image_business_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取特定图片信息（支持 business_id）"""
    image = _get_image_by_identifier(db, image_id, image_business_id, current_user.id)
    return image


@router.get("/business/{image_business_id}", response_model=ImageResponse)
def get_image_by_business_id(
    image_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """按 business_id 获取图片信息"""
    return get_image(0, image_business_id, db, current_user)  # type: ignore[arg-type]


@router.get("/{image_id}/download")
def download_image(
    image_id: int,
    image_business_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """下载图片文件"""
    image = _get_image_by_identifier(db, image_id, image_business_id, current_user.id)

    if not os.path.exists(image.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="图片文件不存在"
        )

    return FileResponse(
        image.file_path, filename=image.original_filename, media_type=image.mime_type
    )


@router.get("/business/{image_business_id}/download")
def download_image_by_business_id(
    image_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """按 business_id 下载图片文件"""
    return download_image(0, image_business_id, db, current_user)  # type: ignore[arg-type]


@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    image_business_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除图片"""
    image = _get_image_by_identifier(db, image_id, image_business_id, current_user.id)
    image.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "图片已删除"}


@router.delete("/business/{image_business_id}")
def delete_image_by_business_id(
    image_business_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """按 business_id 删除图片"""
    return delete_image(0, image_business_id, db, current_user)  # type: ignore[arg-type]
