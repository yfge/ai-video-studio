"""
AI服务提供商管理接口

提供多种AI服务提供商的统一接口，包括文本生成、图像生成、视频生成和语音合成等功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.core.middleware import get_current_active_user
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.storage.oss_service import oss_service

router = APIRouter()


class TextGenerationRequest(BaseModel):
    """文本生成请求"""
    prompt: str = Field(..., description="生成提示词")
    model: Optional[str] = Field(None, description="指定模型")
    prefer_provider: Optional[str] = Field(None, description="首选提供商")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    max_tokens: int = Field(2048, description="最大token数")
    temperature: float = Field(0.7, description="创造性参数")


class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像描述")
    model: Optional[str] = Field(None, description="指定模型")
    prefer_provider: Optional[str] = Field(None, description="首选提供商")
    width: int = Field(1024, description="图像宽度")
    height: int = Field(1024, description="图像高度")
    style: str = Field("realistic", description="图像风格")
    count: int = Field(1, description="生成图像数量")


class ImageToImageRequest(BaseModel):
    """图生图请求"""
    image_url: str = Field(..., description="原始图像URL")
    prompt: Optional[str] = Field(None, description="可选的引导提示词")
    model: Optional[str] = Field(None, description="指定模型（如不指定则由服务自动选择）")
    prefer_provider: Optional[str] = Field(None, description="首选提供商")
    count: int = Field(1, description="生成图像数量")


class VideoGenerationRequest(BaseModel):
    """视频生成请求"""
    prompt: Optional[str] = Field(None, description="视频描述")
    image_url: Optional[str] = Field(None, description="参考图像URL")
    model: Optional[str] = Field(None, description="指定模型")
    prefer_provider: Optional[str] = Field(None, description="首选提供商")
    duration: int = Field(5, description="视频时长(秒)")
    fps: int = Field(24, description="帧率")
    resolution: str = Field("1280x720", description="分辨率")
    style: str = Field("realistic", description="视频风格")


class SpeechGenerationRequest(BaseModel):
    """语音生成请求"""
    text: str = Field(..., description="要转换的文本")
    model: Optional[str] = Field(None, description="指定模型")
    prefer_provider: Optional[str] = Field(None, description="首选提供商")
    voice_type: Optional[str] = Field(None, description="语音类型")
    speed: float = Field(1.0, description="语速")


class ProviderConfigRequest(BaseModel):
    """提供商配置请求"""
    enabled: Optional[bool] = Field(None, description="是否启用")
    weight: Optional[float] = Field(None, description="权重")
    priority: Optional[str] = Field(None, description="优先级(high/medium/low)")
    max_requests_per_minute: Optional[int] = Field(None, description="每分钟最大请求数")


@router.post("/generate/text")
async def generate_text(
    request: TextGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成文本"""
    try:
        response = await ai_service.ai_manager.generate_text(
            prompt=request.prompt,
            model=request.model,
            prefer_provider=request.prefer_provider,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        if response.success:
            return {
                "success": True,
                "data": {
                    "content": response.data,
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": response.metadata
                }
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本生成失败: {str(e)}")


@router.post("/generate/image")
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成图像"""
    try:
        response = await ai_service.ai_manager.generate_image(
            prompt=request.prompt,
            model=request.model,
            prefer_provider=request.prefer_provider,
            width=request.width,
            height=request.height,
            style=request.style,
            n=request.count,
        )
        
        if response.success:
            return {
                "success": True,
                "data": {
                    "images": response.data.get("images", []),
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": response.metadata
                }
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


@router.post("/generate/image-to-image")
async def generate_image_to_image(
    request: ImageToImageRequest,
    current_user: User = Depends(get_current_active_user)
):
    """图生图生成接口（统一路由到支持 IMAGE_TO_IMAGE 的提供商）"""
    try:
        response = await ai_service.ai_manager.image_to_image(
            image_url=request.image_url,
            prompt=request.prompt,
            model=request.model,
            prefer_provider=request.prefer_provider,
            count=request.count,
        )

        if response.success:
            return {
                "success": True,
                "data": {
                    "images": response.data.get("images", []),
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": response.metadata,
                },
            }
        raise HTTPException(status_code=400, detail=response.error)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图生图生成失败: {str(e)}")


@router.post("/generate/video")
async def generate_video(
    request: VideoGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成视频"""
    try:
        if not request.prompt and not request.image_url:
            raise HTTPException(status_code=400, detail="必须提供prompt或image_url")
        
        response = await ai_service.ai_manager.generate_video(
            prompt=request.prompt,
            image_url=request.image_url,
            model=request.model,
            prefer_provider=request.prefer_provider,
            duration=request.duration,
            fps=request.fps,
            resolution=request.resolution
        )
        
        if response.success:
            return {
                "success": True,
                "data": {
                    "video_url": response.data.get("video_url"),
                    "thumbnail_url": response.data.get("thumbnail_url"),
                    "duration": response.data.get("duration"),
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": response.metadata
                }
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")


@router.post("/generate/speech")
async def generate_speech(
    request: SpeechGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """生成语音"""
    try:
        response = await ai_service.ai_manager.text_to_speech(
            text=request.text,
            model=request.model,
            prefer_provider=request.prefer_provider,
            voice_type=request.voice_type,
            speed=request.speed
        )
        
        if response.success:
            return {
                "success": True,
                "data": {
                    "audio_url": response.data.get("audio_url"),
                    "duration": response.data.get("duration"),
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": response.metadata
                }
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音生成失败: {str(e)}")


@router.get("/providers/status")
async def get_providers_status(
    current_user: User = Depends(get_current_active_user)
):
    """获取所有提供商状态"""
    try:
        status = ai_service.get_ai_providers_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.put("/providers/{provider_name}/config")
async def update_provider_config(
    provider_name: str,
    request: ProviderConfigRequest,
    current_user: User = Depends(get_current_active_user)
):
    """更新提供商配置"""
    try:
        # 验证提供商是否存在
        status = ai_service.get_ai_providers_status()
        if provider_name not in status:
            raise HTTPException(status_code=404, detail=f"提供商 {provider_name} 不存在")
        
        ai_service.update_provider_config(
            provider_name=provider_name,
            enabled=request.enabled,
            weight=request.weight,
            priority=request.priority,
            max_requests_per_minute=request.max_requests_per_minute
        )
        
        return {
            "success": True,
            "data": {
                "message": f"提供商 {provider_name} 配置已更新"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/providers/{provider_name}/models")
async def get_provider_models(
    provider_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取指定提供商的可用模型"""
    try:
        status = ai_service.get_ai_providers_status()
        if provider_name not in status:
            raise HTTPException(status_code=404, detail=f"提供商 {provider_name} 不存在")
        
        provider_status = status[provider_name]
        return {
            "success": True,
            "data": {
                "provider": provider_name,
                "models": provider_status.get("available_models", []),
                "supported_model_types": provider_status.get("supported_model_types", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/models/available")
async def get_available_models(
    model_type: Optional[str] = None,
    source: str = "static",
    current_user: User = Depends(get_current_active_user),
):
    """聚合返回所有提供商的可用模型列表

    Query:
    - model_type: 过滤模型类型，例如 'text' / 'image' / 'video'
    - source: 'static' | 'remote' | 'auto'（默认 auto: 优先官方接口，失败回退静态）
    """
    try:
        # 通过统一的 AIService/AIServiceManager 列出模型
        models = await ai_service.list_models(model_type_alias=model_type, source=source)
        # 添加前端期望的 model_id 字段（provider:model）
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
        return {"success": True, "data": {"models": enriched, "count": len(enriched)}}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"获取聚合模型列表失败: {str(e)}")


@router.post("/providers/test/{provider_name}")
async def test_provider(
    provider_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """测试指定提供商的连接"""
    try:
        # 测试文本生成
        response = await ai_service.ai_manager.generate_text(
            prompt="请说'Hello World'",
            prefer_provider=provider_name,
            max_tokens=50
        )
        
        if response.success:
            return {
                "success": True,
                "data": {
                    "provider": provider_name,
                    "status": "connected",
                    "test_response": response.data,
                    "model_used": response.model,
                    "usage": response.usage
                }
            }
        else:
            return {
                "success": False,
                "data": {
                    "provider": provider_name,
                    "status": "failed",
                    "error": response.error
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "data": {
                "provider": provider_name,
                "status": "error",
                "error": str(e)
            }
        }


# OSS存储管理相关接口

class UploadUrlRequest(BaseModel):
    """URL上传请求"""
    url: str = Field(..., description="要上传的文件URL")
    file_type: str = Field("image", description="文件类型(image/video/audio)")
    prefix: Optional[str] = Field(None, description="存储前缀")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文件元数据")


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    urls: List[str] = Field(..., description="要上传的文件URL列表")
    file_type: str = Field("image", description="文件类型")
    prefix: Optional[str] = Field(None, description="存储前缀")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文件元数据")


@router.post("/storage/upload-url")
async def upload_from_url(
    request: UploadUrlRequest,
    current_user: User = Depends(get_current_active_user)
):
    """从URL上传文件到OSS"""
    if not oss_service:
        raise HTTPException(status_code=503, detail="OSS服务未配置")
    
    try:
        result = await oss_service.upload_from_url(
            url=request.url,
            file_type=request.file_type,
            prefix=request.prefix,
            metadata=request.metadata
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/storage/batch-upload")
async def batch_upload_from_urls(
    request: BatchUploadRequest,
    current_user: User = Depends(get_current_active_user)
):
    """批量从URL上传文件到OSS"""
    if not oss_service:
        raise HTTPException(status_code=503, detail="OSS服务未配置")
    
    try:
        results = await oss_service.upload_multiple_urls(
            urls=request.urls,
            file_type=request.file_type,
            prefix=request.prefix,
            metadata=request.metadata
        )
        
        success_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - success_count
        
        return {
            "success": True,
            "data": {
                "total": len(results),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/storage/list")
async def list_storage_objects(
    prefix: str = "",
    max_keys: int = 100,
    marker: str = "",
    current_user: User = Depends(get_current_active_user)
):
    """列出OSS存储对象"""
    if not oss_service:
        raise HTTPException(status_code=503, detail="OSS服务未配置")
    
    try:
        result = oss_service.list_objects(
            prefix=prefix,
            max_keys=max_keys,
            marker=marker
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出对象失败: {str(e)}")


@router.get("/storage/info/{object_key:path}")
async def get_object_info(
    object_key: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取OSS对象信息"""
    if not oss_service:
        raise HTTPException(status_code=503, detail="OSS服务未配置")
    
    try:
        result = oss_service.get_object_info(object_key)
        
        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对象信息失败: {str(e)}")


@router.delete("/storage/{object_key:path}")
async def delete_storage_object(
    object_key: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除OSS存储对象"""
    if not oss_service:
        raise HTTPException(status_code=503, detail="OSS服务未配置")
    
    try:
        result = oss_service.delete_object(object_key)
        
        if result["success"]:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除对象失败: {str(e)}")


@router.get("/storage/signed-url/{object_key:path}")
async def get_signed_url(
    object_key: str,
    expires: int = 3600,
    method: str = "GET",
    current_user: User = Depends(get_current_active_user)
):
    """生成OSS对象签名URL"""
    if not oss_service:
        raise HTTPException(status_code=503, detail="OSS服务未配置")
    
    try:
        signed_url = oss_service.get_signed_url(
            object_key=object_key,
            expires=expires,
            method=method
        )
        
        return {
            "success": True,
            "data": {
                "object_key": object_key,
                "signed_url": signed_url,
                "expires_in": expires,
                "method": method
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成签名URL失败: {str(e)}")


@router.get("/storage/status")
async def get_storage_status(
    current_user: User = Depends(get_current_active_user)
):
    """获取OSS存储服务状态"""
    if not oss_service:
        return {
            "success": False,
            "data": {
                "status": "disabled",
                "message": "OSS服务未配置"
            }
        }
    
    try:
        # 测试OSS连接
        test_result = oss_service.list_objects(prefix="", max_keys=1)
        
        return {
            "success": True,
            "data": {
                "status": "enabled" if test_result["success"] else "error",
                "bucket": oss_service.bucket_name,
                "endpoint": oss_service.endpoint,
                "domain": oss_service.domain,
                "message": "OSS服务正常" if test_result["success"] else test_result.get("error", "连接失败")
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "error",
                "message": f"OSS服务状态检查失败: {str(e)}"
            }
        }
