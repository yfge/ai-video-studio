import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.core.config import settings
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.models.user import User
from app.schemas.virtual_ip import VirtualIPImageCreate, VirtualIPImageResponse, VirtualIPImageUpdate
from app.services.ai_service import ai_service
from app.core.middleware import get_current_active_user
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
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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

@router.get("/{virtual_ip_id}/models/available")
async def get_available_models(
    virtual_ip_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取可用的AI模型列表 - 动态从配置的API获取"""
    # 检查虚拟IP是否存在
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    
    models: List[Dict[str, Any]] = await ai_service.list_models(
        model_type_alias="image",
        source="auto",
    )
    if not models:
        raise HTTPException(
            status_code=503,
            detail="没有配置可用的AI图像生成服务，请检查各 Provider API Key。",
        )

    enriched = [
        {
            "model_id": f"{m['provider']}:{m['id']}",
            "id": m["id"],
            "name": m.get("name"),
            "provider": m["provider"],
            "type": m.get("type"),
            "capabilities": m.get("capabilities", []),
        }
        for m in models
    ]

    providers = {m["provider"] for m in models if m.get("provider")}
    default_model = enriched[0]["model_id"] if enriched else None
    return {
        "models": enriched,
        "default": default_model,
        "configured_providers": len(providers),
        "count": len(enriched),
        "message": f"找到{len(enriched)}个可用模型",
    }

@router.post("/{virtual_ip_id}/images/generate", response_model=VirtualIPImageResponse)
async def generate_virtual_ip_image(
    virtual_ip_id: int,
    request: Request,
    style: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    additional_prompts: Optional[str] = Form(None),
    is_default: Optional[str] = Form(None),
    count: Optional[int] = Form(None),
    size: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """使用AI生成虚拟IP图像"""
    # 检查虚拟IP是否存在
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    
    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    style = payload.get("style", style) or "realistic"
    category = payload.get("category", category) or "portrait"
    raw_model = payload.get("model", model)
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    additional_prompts_value = payload.get("additional_prompts", additional_prompts) or ""
    is_default_value = payload.get("is_default", is_default)
    selected_model = (payload.get("model_id") or model_id or raw_model or "dalle-3").strip()
    if not selected_model:
        selected_model = "dalle-3"

    additional_prompt_list = [p.strip() for p in additional_prompts_value.split(",") if p.strip()]

    is_default_bool = False
    if isinstance(is_default_value, bool):
        is_default_bool = is_default_value
    elif isinstance(is_default_value, str):
        is_default_bool = is_default_value.lower() in {"true", "1", "yes", "on"}

    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    # 记录收到的参数，便于排查模型选择问题
    try:
        from app.core.logging import get_logger
        get_logger().info(
            "VirtualIP image gen | ip=%s model=%s style=%s category=%s prompts=%s",
            virtual_ip_id,
            selected_model,
            style,
            category,
            additional_prompts_value,
        )
    except Exception:
        pass

    # 将虚拟 IP 页面上填写的多种文案聚合进描述，保证提示词包含角色设定
    description_parts = []
    if virtual_ip.description:
        description_parts.append(f"角色简介：{virtual_ip.description}")
    if getattr(virtual_ip, "background_story", None):
        description_parts.append(f"背景故事：{virtual_ip.background_story}")
    if getattr(virtual_ip, "biography", None):
        description_parts.append(f"人物小传：{virtual_ip.biography}")
    if getattr(virtual_ip, "style_prompt", None):
        description_parts.append(f"风格设定：{virtual_ip.style_prompt}")
    aggregated_description = "；".join(description_parts) or (virtual_ip.description or "")

    result = await ai_service.generate_virtual_ip_image(
        ip_name=virtual_ip.name,
        description=aggregated_description,
        style=style,
        category=category,
        model=selected_model,
        additional_prompts=additional_prompt_list,
        background_story=getattr(virtual_ip, "background_story", None),
        count=count_int,
        size=size_value,
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="AI图像生成失败")
    
    # 如果设置为默认图像，先取消其他默认图像
    if is_default_bool:
        db.query(VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id,
            VirtualIPImage.is_default == True
        ).update({"is_default": False})
    
    # 创建图像记录
    tags = [style, category, "ai_generated", result["generation_method"]]
    if additional_prompt_list:
        tags.extend(additional_prompt_list)
    
    # 获取本地文件路径和信息
    local_file_path = result.get("local_file_path")
    if not local_file_path or not os.path.exists(local_file_path):
        raise HTTPException(status_code=500, detail="图像文件生成失败")
    
    # 获取文件信息
    file_size = os.path.getsize(local_file_path)
    filename = os.path.basename(local_file_path)
    
    # 使用相对路径保存到数据库
    relative_path = f"/uploads/{filename}"
    
    # 获取OSS URL
    oss_url = result.get("oss_upload", {}).get("oss_url") if result.get("oss_upload") else None
    
    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id,
        file_path=relative_path,  # 使用短的相对路径
        oss_url=oss_url,  # OSS存储URL
        filename=filename,
        original_filename=f"{virtual_ip.name}_{category}_generated.png",
        file_size=file_size,
        mime_type="image/png",
        category=category,
        tags=tags,
        prompt=result["prompt"],
        ai_model=result["model_used"],
        generation_params=result.get("usage", {}),
        is_default=is_default_bool,
        metadata={
            "generation_method": result["generation_method"],
            "prompt": result["prompt"],
            "style": result["style"],
            "additional_prompts": additional_prompt_list,
            "original_openai_url": result.get("original_image_url", ""),
            "local_file_path": local_file_path,
            "oss_upload": result.get("oss_upload")
        }
    )
    
    db_image = VirtualIPImage(**image_data.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return VirtualIPImageResponse.from_orm(db_image)

@router.get("/{virtual_ip_id}/images/categories")
async def get_image_categories(
    virtual_ip_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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

@router.get("/{virtual_ip_id}/images", response_model=List[VirtualIPImageResponse])
async def get_virtual_ip_images(
    virtual_ip_id: int,
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
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


@router.post("/{virtual_ip_id}/images/{image_id}/variants", response_model=List[VirtualIPImageResponse])
async def generate_virtual_ip_image_variant(
    virtual_ip_id: int,
    image_id: int,
    request: Request,
    prompt: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    count: Optional[int] = Form(1),
    size: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """基于已有虚拟IP图像生成变体并保存"""
    virtual_ip = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id).first()
    if not virtual_ip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")

    base_image = (
        db.query(VirtualIPImage)
        .filter(
            VirtualIPImage.id == image_id,
            VirtualIPImage.virtual_ip_id == virtual_ip_id,
        )
        .first()
    )
    if not base_image:
        raise HTTPException(status_code=404, detail="基础图像不存在")

    payload: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    prompt_value = payload.get("prompt", prompt) or "为当前角色生成不同视角/姿态的图像，如背面照或全身照"
    raw_model = payload.get("model", model)
    count_value = payload.get("count", count)
    size_value = payload.get("size", size)
    selected_model = (payload.get("model_id") or model_id or raw_model or base_image.ai_model or "").strip()

    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    # 选择原图 URL：优先使用 OSS，其次使用本地服务地址
    if base_image.oss_url:
        image_url = base_image.oss_url
    else:
        file_path = base_image.file_path or ""
        if file_path and not file_path.startswith("/"):
            file_path = "/" + file_path
        # backend 容器内部通过 localhost 访问自身上传文件
        image_url = f"http://localhost:8000{file_path}"

    normalized_model = (selected_model or "").lower()
    prefer_provider: Optional[str] = None
    if normalized_model.startswith("seedream") or normalized_model.startswith("volcengine"):
        prefer_provider = "volcengine"
    elif normalized_model.startswith("deepseek"):
        prefer_provider = "deepseek"
    elif normalized_model.startswith("keling") or normalized_model.startswith("kling"):
        prefer_provider = "keling"
    elif normalized_model.startswith("jimeng"):
        prefer_provider = "jimeng"
    elif normalized_model.startswith("dall-e") or normalized_model.startswith("dalle"):
        prefer_provider = "openai"

    if not ai_service.ai_manager:
        raise HTTPException(status_code=503, detail="AI管理器未初始化，无法执行图生图")

    try:
        response = await ai_service.ai_manager.image_to_image(
            image_url=image_url,
            prompt=prompt_value,
            model=selected_model or None,
            prefer_provider=prefer_provider,
            count=count_int,
            size=size_value,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"图生图调用失败: {exc}") from exc

    if not response.success:
        raise HTTPException(status_code=500, detail=response.error or "图生图生成失败")

    images = response.data.get("images", []) if isinstance(response.data, dict) else []
    if not images:
        raise HTTPException(status_code=500, detail="图生图接口未返回任何图像")

    created_images: list[VirtualIPImage] = []

    for idx, variant_url in enumerate(images):
        # 下载变体图像到本地 uploads 目录
        local_file_path = await ai_service._download_image(
            variant_url,
            virtual_ip.name,
            base_image.category or "portrait",
        )
        if not local_file_path or not os.path.exists(local_file_path):
            raise HTTPException(status_code=500, detail="图生图文件下载失败")

        file_size = os.path.getsize(local_file_path)
        filename = os.path.basename(local_file_path)
        relative_path = f"/uploads/{filename}"

        tags = [
            base_image.category or "portrait",
            "ai_generated",
            "variant",
        ]

        image_data = VirtualIPImageCreate(
            virtual_ip_id=virtual_ip_id,
            file_path=relative_path,
            oss_url=None,
            filename=filename,
            original_filename=(
                f"{virtual_ip.name}_{base_image.category or 'variant'}_img2img_{idx + 1}.png"
            ),
            file_size=file_size,
            mime_type="image/png",
            category=base_image.category or "portrait",
            tags=tags,
            prompt=prompt_value,
            ai_model=selected_model or response.model,
            generation_params=response.usage or {},
            is_default=False,
            metadata={
                "generation_method": "image_to_image",
                "provider": response.provider,
                "model": response.model,
                "base_image_id": base_image.id,
                "base_image_url": image_url,
                "variant_url": variant_url,
            },
        )

        db_image = VirtualIPImage(**image_data.dict())
        db.add(db_image)
        created_images.append(db_image)

    db.commit()
    for img in created_images:
        db.refresh(img)

    return [VirtualIPImageResponse.from_orm(img) for img in created_images]
