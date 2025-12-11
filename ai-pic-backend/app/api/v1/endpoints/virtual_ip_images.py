import os
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType, TaskStatus
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.virtual_ip import VirtualIPImageCreate, VirtualIPImageResponse, VirtualIPImageUpdate
from app.services.ai_service import ai_service
from app.services.storage import oss_service
from app.services.task_worker import (
    virtual_ip_image_generate_task,
    virtual_ip_image_variant_task,
)
from app.utils.model_utils import infer_provider_from_model
import shutil

router = APIRouter()


def _get_owned_virtual_ip(
    db: Session,
    current_user: User,
    virtual_ip_id: int,
) -> VirtualIP:
    """获取当前用户可访问的虚拟 IP 资产。"""
    query = db.query(VirtualIP).filter(VirtualIP.id == virtual_ip_id)
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(VirtualIP.user_id == current_user.id)
    vip = query.first()
    if not vip:
        raise HTTPException(status_code=404, detail="虚拟IP不存在")
    return vip

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
    # 检查虚拟IP是否存在且归属当前用户（或管理员）
    virtual_ip = _get_owned_virtual_ip(db, current_user, virtual_ip_id)
    
    # 检查文件类型
    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # 读取文件内容并做体积校验
    content = await image.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
        )

    # 通过统一持久化抽象处理：本地保存 + 可选 OSS 上传
    try:
        stored = await ai_service.persist_uploaded_image(
            file_bytes=content,
            original_filename=image.filename,
            prefix="user-uploads/virtual-ip",
            metadata={
                "virtual_ip_id": virtual_ip_id,
                "uploader_id": current_user.id,
                "category": category,
            },
            # 宽松兜底：OSS 上传失败时自动回退到本地存储
            require_upload=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"虚拟IP图像保存失败: {exc}") from exc
    
    # 如果设置为默认图像，先取消其他默认图像
    if is_default:
        db.query(VirtualIPImage).filter(
            VirtualIPImage.virtual_ip_id == virtual_ip_id,
            VirtualIPImage.is_default == True
        ).update({"is_default": False})
    
    # 创建图像记录
    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id,
        file_path=stored.get("relative_path") or f"/uploads/{stored.get('filename')}",
        oss_url=stored.get("oss_url"),
        filename=stored.get("filename"),
        original_filename=image.filename,
        file_size=stored.get("file_size"),
        mime_type=image.content_type or "image/png",
        category=category,
        tags=tags.split(",") if tags else [],
        is_default=is_default
    )
    
    db_image = VirtualIPImage(**image_data.dict())
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return VirtualIPImageResponse.from_orm(db_image)


def _build_virtual_ip_image_payload(
    virtual_ip_id: int,
    style: Optional[str],
    category: Optional[str],
    model: Optional[str],
    count: Optional[int],
    size: Optional[str],
    additional_prompts: Optional[str],
    is_default: Optional[str] | Optional[bool],
    current_user: User,
    db: Session,
) -> Dict[str, Any]:
    """将前端传入的参数收敛为任务 payload，便于 Celery worker 重建上下文。"""
    virtual_ip = _get_owned_virtual_ip(db, current_user, virtual_ip_id)

    style_value = style or "realistic"
    category_value = category or "portrait"
    raw_model = model
    selected_model = (raw_model or "dalle-3").strip()
    if not selected_model:
        selected_model = "dalle-3"

    try:
        count_int = int(count) if count is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    additional_prompt_list = [
        p.strip()
        for p in (additional_prompts or "").split(",")
        if p.strip()
    ]

    is_default_bool = False
    if isinstance(is_default, bool):
        is_default_bool = is_default
    elif isinstance(is_default, str):
        is_default_bool = is_default.lower() in {"true", "1", "yes", "on"}

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

    return {
        "virtual_ip_id": virtual_ip_id,
        "virtual_ip_name": virtual_ip.name,
        "aggregated_description": aggregated_description,
        "style": style_value,
        "category": category_value,
        "model": selected_model,
        "count": count_int,
        "size": size,
        "additional_prompts": additional_prompt_list,
        "is_default": is_default_bool,
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
    """使用AI生成虚拟IP图像（同步路径，保留以兼容旧调用）"""
    # 尽量使用 OSS，若未配置则退回本地相对路径
    # 检查虚拟IP是否存在且归属当前用户（或管理员）
    virtual_ip = _get_owned_virtual_ip(db, current_user, virtual_ip_id)
    
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
    oss_url = result.get("oss_url") or result.get("oss_upload", {}).get("file_url")

    image_data = VirtualIPImageCreate(
        virtual_ip_id=virtual_ip_id,
        file_path=relative_path,  # 使用短的相对路径
        oss_url=oss_url,  # OSS存储URL（未配置时为空）
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


@router.post("/{virtual_ip_id}/images/generate-async")
async def generate_virtual_ip_image_async(
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成虚拟IP图像：创建 Task 并委托 Celery 处理。"""
    # 先解析请求体，复用同步接口的参数处理逻辑
    virtual_ip = _get_owned_virtual_ip(db, current_user, virtual_ip_id)

    payload_body: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload_body = await request.json()
        except Exception:
            payload_body = {}

    style = payload_body.get("style", style)
    category = payload_body.get("category", category)
    raw_model = payload_body.get("model", model)
    count_value = payload_body.get("count", count)
    size_value = payload_body.get("size", size)
    additional_prompts_value = payload_body.get("additional_prompts", additional_prompts) or ""
    is_default_value = payload_body.get("is_default", is_default)
    selected_model = (payload_body.get("model_id") or model_id or raw_model or "dalle-3").strip()

    # 组装用于 worker 的 payload
    payload = _build_virtual_ip_image_payload(
        virtual_ip_id=virtual_ip_id,
        style=style,
        category=category,
        model=selected_model,
        count=count_value,
        size=size_value,
        additional_prompts=additional_prompts_value,
        is_default=is_default_value,
        current_user=current_user,
        db=db,
    )

    # 创建任务
    task = Task(
        title=f"虚拟IP文生图 - {virtual_ip.name}",
        description="异步生成虚拟IP图像",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=f"VirtualIP image gen for {virtual_ip.name}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 委托 Celery worker 处理
    virtual_ip_image_generate_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}

@router.get("/{virtual_ip_id}/images/categories")
async def get_image_categories(
    virtual_ip_id: int,
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """获取虚拟IP图像分类列表"""
    # 检查虚拟IP是否存在且归属当前用户（或管理员）
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
    
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
    # 检查虚拟IP是否存在且归属当前用户（或管理员）
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
    
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
    # 先校验虚拟 IP 归属
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
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
    # 校验虚拟 IP 归属
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
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
    # 校验虚拟 IP 归属
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
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
    # 校验虚拟 IP 归属
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
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
    # 检查虚拟 IP 归属和图像是否存在
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
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
    """基于已有虚拟IP图像生成变体并保存（同步路径，保留以兼容旧调用）"""
    # 优先使用 OSS，未配置则退回本地存储
    virtual_ip = _get_owned_virtual_ip(db, current_user, virtual_ip_id)

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
        # Celery / Provider 在容器内部通过 INTERNAL_BACKEND_URL 访问上传文件
        backend_base = (getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000").rstrip("/")
        image_url = f"{backend_base}{file_path}"

    prefer_provider = infer_provider_from_model(selected_model or "")

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
        # 统一使用 AIService._persist_generated_image 做本地保存 + OSS 上传，
        # 行为与文生图、环境图生成保持一致
        try:
            stored = await ai_service._persist_generated_image(
                image_data=variant_url,
                ip_name=virtual_ip.name,
                category=base_image.category or "portrait",
                prefix="ai-generated/virtual-ip",
                metadata={
                    "virtual_ip_id": virtual_ip_id,
                    "base_image_id": base_image.id,
                    "prompt": prompt_value,
                    "provider": response.provider,
                    "model": selected_model or response.model,
                },
                # 宽松兜底：OSS 上传失败时自动回退到本地存储
                require_upload=False,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"图生图文件保存失败: {exc}") from exc

        local_file_path = stored.get("local_file_path")
        if not local_file_path or not os.path.exists(local_file_path):
            raise HTTPException(status_code=500, detail="图生图文件下载失败")

        file_size = stored.get("file_size") or os.path.getsize(local_file_path)
        filename = stored.get("filename") or os.path.basename(local_file_path)
        relative_path = stored.get("relative_path") or f"/uploads/{filename}"
        oss_result = stored.get("oss_upload")
        oss_url = stored.get("oss_url")

        tags = [
            base_image.category or "portrait",
            "ai_generated",
            "variant",
        ]

        image_data = VirtualIPImageCreate(
            virtual_ip_id=virtual_ip_id,
            file_path=relative_path,
            oss_url=oss_url,
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
                "oss_upload": oss_result,
            },
        )

        db_image = VirtualIPImage(**image_data.dict())
        db.add(db_image)
        created_images.append(db_image)

    db.commit()
    for img in created_images:
        db.refresh(img)

    return [VirtualIPImageResponse.from_orm(img) for img in created_images]


@router.post("/{virtual_ip_id}/images/{image_id}/variants-async")
async def generate_virtual_ip_image_variant_async(
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
    """异步基于已有虚拟IP图像生成变体：创建 Task 并委托 Celery 处理。"""
    # 权限与基础图像校验
    _get_owned_virtual_ip(db, current_user, virtual_ip_id)
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

    payload_body: Dict[str, Any] = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            payload_body = await request.json()
        except Exception:
            payload_body = {}

    prompt_value = (
        payload_body.get("prompt", prompt)
        or "为当前角色生成不同视角/姿态的图像，如背面照或全身照"
    )
    raw_model = payload_body.get("model", model)
    count_value = payload_body.get("count", count)
    size_value = payload_body.get("size", size)
    reference_images_value = payload_body.get("reference_images") or []

    # DEBUG: 打印收到的 payload
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"[DEBUG] 虚拟IP图生图异步接口收到 payload_body: {payload_body.keys()}")
    logger.warning(f"[DEBUG] reference_images_value: {reference_images_value}")
    selected_model = (
        payload_body.get("model_id") or model_id or raw_model or base_image.ai_model or ""
    ).strip()

    try:
        count_int = int(count_value) if count_value is not None else 1
    except (TypeError, ValueError):
        count_int = 1

    # 组装 payload
    payload: Dict[str, Any] = {
        "virtual_ip_id": virtual_ip_id,
        "image_id": image_id,
        "prompt": prompt_value,
        "model": selected_model,
        "count": count_int,
        "size": size_value,
        "reference_images": reference_images_value,
    }

    # 创建任务
    task = Task(
        title=f"虚拟IP图生图 - 图像{image_id}",
        description="异步生成虚拟IP图像变体",
        task_type=TaskType.IMAGE_GENERATION,
        prompt=f"VirtualIP img2img for image {image_id}",
        parameters=json.dumps(payload, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    virtual_ip_image_variant_task.delay(task.id, payload, current_user.id)

    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


def _process_virtual_ip_image_task(task_id: int, payload: Dict[str, Any], user_id: int) -> None:
    """
    Celery worker 使用的虚拟 IP 文生图处理函数。

    逻辑与同步接口 generate_virtual_ip_image 保持一致：
    - 调用 AIService.generate_virtual_ip_image 生成图像并通过统一持久化抽象存储
    - 在数据库中创建 VirtualIPImage 记录
    - 更新 Task 状态与结果信息
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        virtual_ip = db.query(VirtualIP).filter(
            VirtualIP.id == payload["virtual_ip_id"]
        ).first()
        if not virtual_ip:
            raise RuntimeError("虚拟IP不存在")

        import anyio

        async def _run() -> VirtualIPImage:
            result = await ai_service.generate_virtual_ip_image(
                ip_name=payload.get("virtual_ip_name") or virtual_ip.name,
                description=payload.get("aggregated_description")
                or virtual_ip.description
                or "",
                style=payload.get("style") or "realistic",
                category=payload.get("category") or "portrait",
                model=payload.get("model") or "dalle-3",
                additional_prompts=payload.get("additional_prompts") or [],
                background_story=None,
                count=int(payload.get("count") or 1),
                size=payload.get("size"),
            )
            if not result:
                raise RuntimeError("AI图像生成失败")

            additional_prompts_list = payload.get("additional_prompts") or []
            is_default_bool = bool(payload.get("is_default"))

            if is_default_bool:
                db.query(VirtualIPImage).filter(
                    VirtualIPImage.virtual_ip_id == virtual_ip.id,
                    VirtualIPImage.is_default == True,  # noqa: E712
                ).update({"is_default": False})

            tags = [
                payload.get("style") or "realistic",
                payload.get("category") or "portrait",
                "ai_generated",
                result["generation_method"],
            ]
            if additional_prompts_list:
                tags.extend(additional_prompts_list)

            local_file_path = result.get("local_file_path")
            if not local_file_path or not os.path.exists(local_file_path):
                raise RuntimeError("图像文件生成失败")

            file_size = os.path.getsize(local_file_path)
            filename = os.path.basename(local_file_path)
            relative_path = result.get("relative_path") or f"/uploads/{filename}"
            oss_url = result.get("oss_url") or result.get("oss_upload", {}).get(
                "file_url"
            )

            image_data = VirtualIPImageCreate(
                virtual_ip_id=virtual_ip.id,
                file_path=relative_path,
                oss_url=oss_url,
                filename=filename,
                original_filename=f"{virtual_ip.name}_{payload.get('category') or 'portrait'}_generated.png",
                file_size=file_size,
                mime_type="image/png",
                category=payload.get("category") or "portrait",
                tags=tags,
                prompt=result["prompt"],
                ai_model=result["model_used"],
                generation_params=result.get("usage", {}),
                is_default=is_default_bool,
                metadata={
                    "generation_method": result["generation_method"],
                    "prompt": result["prompt"],
                    "style": result["style"],
                    "additional_prompts": additional_prompts_list,
                    "original_openai_url": result.get("original_image_url", ""),
                    "local_file_path": local_file_path,
                    "oss_upload": result.get("oss_upload"),
                },
            )

            db_image = VirtualIPImage(**image_data.dict())
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            return db_image

        created_image = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            # 记录结果位置，便于后续查询
            task.result_file_path = f"virtual_ip_image:{created_image.virtual_ip_id}:{created_image.id}"
            db.commit()
    except Exception as exc:  # pragma: no cover - 守护 Celery worker
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()


def _process_virtual_ip_image_variant_task(
    task_id: int, payload: Dict[str, Any], user_id: int
) -> None:
    """
    Celery worker 使用的虚拟 IP 图生图处理函数。

    逻辑与同步接口 generate_virtual_ip_image_variant 保持一致：
    - 调用 AIServiceManager.image_to_image 生成图像变体
    - 通过 AIService._persist_generated_image 下载/上传并在数据库中创建 VirtualIPImage 记录
    - 更新 Task 状态与结果信息
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        virtual_ip = db.query(VirtualIP).filter(
            VirtualIP.id == payload["virtual_ip_id"]
        ).first()
        if not virtual_ip:
            raise RuntimeError("虚拟IP不存在")

        base_image = (
            db.query(VirtualIPImage)
            .filter(
                VirtualIPImage.id == payload["image_id"],
                VirtualIPImage.virtual_ip_id == payload["virtual_ip_id"],
            )
            .first()
        )
        if not base_image:
            raise RuntimeError("基础图像不存在")

        import anyio

        async def _run() -> list[VirtualIPImage]:
            # 构造基准图 URL：优先 OSS，其次本地服务
            if base_image.oss_url:
                image_url = base_image.oss_url
            else:
                file_path = base_image.file_path or ""
                if file_path and not file_path.startswith("/"):
                    file_path = "/" + file_path
                backend_base = (
                    getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
                ).rstrip("/")
                image_url = f"{backend_base}{file_path}"

            selected_model = payload.get("model") or base_image.ai_model or ""
            prompt_value = payload.get("prompt") or (
                "为当前角色生成不同视角/姿态的图像，如背面照或全身照"
            )
            count_int = int(payload.get("count") or 1)
            size_value = payload.get("size")
            prefer_provider = infer_provider_from_model(selected_model or "")

            if not ai_service.ai_manager:
                raise RuntimeError("AI管理器未初始化，无法执行图生图")

            # 提取参考图并转换为绝对 URL
            reference_images = payload.get("reference_images") or []
            extra_images = []
            for ref_url in reference_images:
                if not ref_url:
                    continue
                if ref_url.startswith("http"):
                    extra_images.append(ref_url)
                else:
                    # 转换相对路径为绝对 URL
                    path = ref_url if ref_url.startswith("/") else f"/{ref_url}"
                    backend_base = (
                        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
                    ).rstrip("/")
                    extra_images.append(f"{backend_base}{path}")

            response = await ai_service.ai_manager.image_to_image(
                image_url=image_url,
                prompt=prompt_value,
                model=selected_model or None,
                prefer_provider=prefer_provider,
                count=count_int,
                size=size_value,
                extra_images=extra_images,
            )
            if not response.success:
                raise RuntimeError(response.error or "图生图生成失败")

            images = (
                response.data.get("images", [])
                if isinstance(response.data, dict)
                else []
            )
            if not images:
                raise RuntimeError("图生图接口未返回任何图像")

            created_images: list[VirtualIPImage] = []
            for idx, variant_url in enumerate(images):
                stored = await ai_service._persist_generated_image(
                    image_data=variant_url,
                    ip_name=virtual_ip.name,
                    category=base_image.category or "portrait",
                    prefix="ai-generated/virtual-ip",
                    metadata={
                        "virtual_ip_id": virtual_ip.id,
                        "base_image_id": base_image.id,
                        "prompt": prompt_value,
                        "provider": response.provider,
                        "model": selected_model or response.model,
                    },
                    # 宽松兜底：OSS 上传失败时自动回退到本地存储，确保任务成功
                    require_upload=False,
                )

                local_file_path = stored.get("local_file_path")
                if not local_file_path or not os.path.exists(local_file_path):
                    raise RuntimeError("图生图文件下载失败")

                file_size = stored.get("file_size") or os.path.getsize(
                    local_file_path
                )
                filename = stored.get("filename") or os.path.basename(local_file_path)
                relative_path = stored.get("relative_path") or f"/uploads/{filename}"
                oss_result = stored.get("oss_upload")
                oss_url = stored.get("oss_url")

                tags = [
                    base_image.category or "portrait",
                    "ai_generated",
                    "variant",
                ]

                image_data = VirtualIPImageCreate(
                    virtual_ip_id=virtual_ip.id,
                    file_path=relative_path,
                    oss_url=oss_url,
                    filename=filename,
                    original_filename=f"{virtual_ip.name}_{base_image.category or 'variant'}_img2img_{idx + 1}.png",
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
                        "oss_upload": oss_result,
                    },
                )

                db_image = VirtualIPImage(**image_data.dict())
                db.add(db_image)
                created_images.append(db_image)

            db.commit()
            for img in created_images:
                db.refresh(img)
            return created_images

        created_images = anyio.run(_run)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"virtual_ip_image_variants:{payload['image_id']}:{len(created_images)}"
            )
            db.commit()
    except Exception as exc:  # pragma: no cover - 守护 Celery worker
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
    finally:
        db.close()
