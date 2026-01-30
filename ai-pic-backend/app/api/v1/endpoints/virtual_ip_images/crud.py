"""
Virtual IP Images CRUD endpoints.

Basic create, read, update, delete operations for virtual IP images.
"""

import os
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.models.virtual_ip import VirtualIPImage
from app.schemas.virtual_ip import (
    VirtualIPImageCreate,
    VirtualIPImageResponse,
    VirtualIPImageUpdate,
)
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .helpers import (
    get_owned_virtual_ip,
    get_virtual_ip_image,
    not_deleted,
    set_ip_default_avatar,
)

router = APIRouter()


@router.post("/{virtual_ip_id}/images", response_model=VirtualIPImageResponse)
async def create_virtual_ip_image(
    virtual_ip_id: str,
    image: UploadFile = File(...),
    category: str = Form("portrait"),
    tags: str = Form(""),
    is_default: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload virtual IP image."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    virtual_ip_id_int = virtual_ip.id

    # Check file type
    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Read and validate file size
    content = await image.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
        )

    # Persist via unified abstraction: local save + optional OSS upload
    try:
        stored = await ai_service.persist_uploaded_image(
            file_bytes=content,
            original_filename=image.filename,
            prefix="user-uploads/virtual-ip",
            metadata={
                "virtual_ip_id": virtual_ip_id_int,
                "uploader_id": current_user.id,
                "category": category,
            },
            require_upload=bool(oss_service),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"虚拟IP图像保存失败: {exc}"
        ) from exc

    # Clear other default images if setting as default
    if is_default:
        not_deleted(db.query(VirtualIPImage), VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id_int,
            VirtualIPImage.is_default.is_(True),
        ).update({"is_default": False})

    # Create image record
    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id_int,
        file_path=stored.get("relative_path") or f"/uploads/{stored.get('filename')}",
        oss_url=stored.get("oss_url"),
        filename=stored.get("filename"),
        original_filename=image.filename,
        file_size=stored.get("file_size"),
        mime_type=image.content_type or "image/png",
        category=category,
        tags=tags.split(",") if tags else [],
        is_default=is_default,
    )

    db_image = VirtualIPImage(
        **image_data.dict(), virtual_ip_business_id=virtual_ip.business_id
    )
    db.add(db_image)
    if is_default:
        set_ip_default_avatar(db, virtual_ip.id, db_image)
    db.commit()
    db.refresh(db_image)

    return VirtualIPImageResponse.from_orm(db_image)


@router.get("/{virtual_ip_id}/images/categories")
async def get_image_categories(
    virtual_ip_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get virtual IP image categories."""
    vip = get_owned_virtual_ip(db, current_user, virtual_ip_id)

    categories = (
        db.query(VirtualIPImage.category)
        .filter(VirtualIPImage.virtual_ip_id == vip.id)
        .distinct()
        .all()
    )

    return [category[0] for category in categories]


@router.get("/{virtual_ip_id}/images", response_model=List[VirtualIPImageResponse])
async def get_virtual_ip_images(
    virtual_ip_id: str,
    category: Optional[str] = Query(None, description="按分类过滤"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all images for a virtual IP."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)

    query = not_deleted(db.query(VirtualIPImage), VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip.id
    )

    if category:
        query = query.filter(VirtualIPImage.category == category)

    images = query.order_by(
        VirtualIPImage.is_default.desc(), VirtualIPImage.created_at.desc()
    ).all()
    return [VirtualIPImageResponse.from_orm(image) for image in images]


@router.get("/{virtual_ip_id}/images/{image_id}", response_model=VirtualIPImageResponse)
async def get_virtual_ip_image_detail(
    virtual_ip_id: str,
    image_id: int,
    image_business_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get specific virtual IP image."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    image = get_virtual_ip_image(db, virtual_ip, image_id, image_business_id)

    return VirtualIPImageResponse.from_orm(image)


@router.get("/{virtual_ip_id}/images/{image_id}/download")
def download_virtual_ip_image(
    virtual_ip_id: str,
    image_id: int,
    image_business_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Download virtual IP image file."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    image = get_virtual_ip_image(db, virtual_ip, image_id, image_business_id)

    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="图像文件不存在")

    return FileResponse(
        image.file_path, filename=image.original_filename, media_type=image.mime_type
    )


@router.put("/{virtual_ip_id}/images/{image_id}", response_model=VirtualIPImageResponse)
async def update_virtual_ip_image(
    virtual_ip_id: str,
    image_id: int,
    image_update: VirtualIPImageUpdate,
    image_business_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update virtual IP image info."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    image = get_virtual_ip_image(db, virtual_ip, image_id, image_business_id)

    # Clear other default images if setting as default
    if image_update.is_default:
        not_deleted(db.query(VirtualIPImage), VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip.id,
            VirtualIPImage.is_default.is_(True),
            VirtualIPImage.id != image_id,
        ).update({"is_default": False})

    # Update image fields
    for field, value in image_update.dict(exclude_unset=True).items():
        setattr(image, field, value)

    if image_update.is_default:
        set_ip_default_avatar(db, virtual_ip.id, image)

    db.commit()
    db.refresh(image)

    return VirtualIPImageResponse.from_orm(image)


@router.delete("/{virtual_ip_id}/images/{image_id}")
async def delete_virtual_ip_image(
    virtual_ip_id: str,
    image_id: int,
    image_business_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete virtual IP image (soft delete)."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    image = get_virtual_ip_image(db, virtual_ip, image_id, image_business_id)

    image.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "图像删除成功"}


@router.post("/{virtual_ip_id}/images/{image_id}/set-default")
async def set_default_image(
    virtual_ip_id: str,
    image_id: int,
    image_business_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Set image as default."""
    virtual_ip = get_owned_virtual_ip(db, current_user, virtual_ip_id)
    image = get_virtual_ip_image(db, virtual_ip, image_id, image_business_id)

    # Clear other default images
    db.query(VirtualIPImage).filter(
        VirtualIPImage.virtual_ip_id == virtual_ip.id,
        VirtualIPImage.is_default.is_(True),
    ).update({"is_default": False})

    # Set current image as default
    image.is_default = True
    set_ip_default_avatar(db, virtual_ip.id, image)
    db.commit()

    return {"message": "默认图像设置成功"}
