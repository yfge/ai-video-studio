"""
可灵(Kling)服务提供商

专注于视频生成和图像相关功能
"""

import httpx
import json
import asyncio
from typing import List, Optional, Dict, Any
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig

class KelingProvider(BaseProvider):
    """可灵服务提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://klingai.com/api/v1"
    
    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.IMAGE_TO_VIDEO,
            AIModelType.TEXT_TO_IMAGE
        ]
    
    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                model_id="kling-v1",
                name="可灵视频生成 V1",
                description="专业的AI视频生成模型",
                model_type=AIModelType.TEXT_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["text_to_video", "high_quality", "smooth_motion"]
            ),
            ModelInfo(
                model_id="kling-video-pro",
                name="可灵视频专业版",
                description="高质量视频生成，支持更长时长",
                model_type=AIModelType.TEXT_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["text_to_video", "long_duration", "4k_quality"]
            ),
            ModelInfo(
                model_id="kling-image2video",
                name="可灵图生视频",
                description="基于图像生成视频",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["image_to_video", "motion_control", "style_preservation"]
            ),
            ModelInfo(
                model_id="kling-image",
                name="可灵图像生成",
                description="高质量图像生成模型",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "style_control", "high_resolution"]
            )
        ]
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0),  # 视频生成需要更长超时
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ai-video-studio/1.0"
            }
        )
    
    async def generate_text(self, prompt: str, model: str = None, **kwargs) -> AIResponse:
        """可灵不支持文本生成"""
        return AIResponse(
            success=False,
            error="可灵不支持纯文本生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION
        )
    
    async def generate_image(
        self, 
        prompt: str, 
        model: str = "kling-image",
        width: int = 1024,
        height: int = 1024,
        style: str = "realistic",
        **kwargs
    ) -> AIResponse:
        """使用可灵生成图像"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                client = await self.get_client()
                
                # 可灵AI图像生成API调用
                request_data = {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "model": model or "kling-image",
                    "style": style,
                    "num_outputs": 1,
                    "quality": "hd"
                }
                
                # 添加其他参数
                request_data.update(kwargs)
                
                response = await client.post(
                    f"{self.base_url}/images/generate",
                    json=request_data
                )
                
                # 处理不同状态码的响应
                if response.status_code == 200:
                    data = response.json()
                    
                    # 检查可灵AI特有的响应格式
                    if data.get("status") == 500 and "Service busy" in data.get("message", ""):
                        # 服务繁忙，重试
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        else:
                            return AIResponse(
                                success=False,
                                error=f"可灵AI服务繁忙，已重试{max_retries}次",
                                provider=self.name,
                                model=model,
                                task_type=AITaskType.PORTRAIT_GENERATION,
                                model_type=AIModelType.TEXT_TO_IMAGE
                            )
                    
                    # 检查是否成功
                    if data.get("result") == 1 or data.get("status") == 200:
                        # 检查是否返回了任务ID（异步任务）
                        if "task_id" in data or "data" in data and data["data"] and "task_id" in data["data"]:
                            task_id = data.get("task_id") or data["data"].get("task_id")
                            # 轮询任务状态
                            result = await self._poll_task_status(task_id, "image")
                            if result and "images" in result:
                                images = result["images"]
                                if isinstance(images, list) and images:
                                    return AIResponse(
                                        success=True,
                                        data={"images": images},
                                        provider=self.name,
                                        model=model,
                                        task_type=AITaskType.PORTRAIT_GENERATION,
                                        model_type=AIModelType.TEXT_TO_IMAGE,
                                        metadata={
                                            "task_id": task_id,
                                            "width": width,
                                            "height": height,
                                            "style": style,
                                            "prompt": prompt
                                        }
                                    )
                        
                        # 检查是否直接返回了图像（同步）
                        elif "images" in data or ("data" in data and data["data"] and "images" in data["data"]):
                            images = data.get("images") or data["data"].get("images", [])
                            if isinstance(images, list) and images:
                                return AIResponse(
                                    success=True,
                                    data={"images": images},
                                    provider=self.name,
                                    model=model,
                                    task_type=AITaskType.PORTRAIT_GENERATION,
                                    model_type=AIModelType.TEXT_TO_IMAGE,
                                    metadata={
                                        "width": width,
                                        "height": height,
                                        "style": style,
                                        "prompt": prompt,
                                        "direct_response": True
                                    }
                                )
                
                # 处理错误响应
                error_message = "可灵AI图像生成失败"
                try:
                    if response.status_code == 200:
                        error_data = response.json()
                        error_message = error_data.get("message") or error_data.get("error", {}).get("detail", error_message)
                    else:
                        error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                except:
                    error_message = f"HTTP {response.status_code}: 响应解析失败"
                
                # 如果不是服务繁忙错误，不重试
                if "Service busy" not in error_message:
                    return AIResponse(
                        success=False,
                        error=error_message,
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE
                    )
                
                # 服务繁忙，继续重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return AIResponse(
                        success=False,
                        error=f"可灵AI服务持续繁忙，已重试{max_retries}次",
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE
                    )
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return AIResponse(
                        success=False,
                        error=self.format_error(e),
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE
                    )
        
        return AIResponse(
            success=False,
            error="所有重试都已失败",
            provider=self.name,
            model=model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE
        )
    
    async def generate_video(
        self, 
        prompt: str = None,
        image_url: str = None, 
        model: str = "kling-v1",
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        **kwargs
    ) -> AIResponse:
        """使用可灵生成视频"""
        try:
            client = await self.get_client()
            
            # 根据输入类型选择端点
            if image_url and not prompt:
                # 图生视频
                endpoint = f"{self.base_url}/videos/image2video"
                request_data = {
                    "model": "kling-image2video",
                    "image_url": image_url,
                    "duration": duration,
                    "fps": fps,
                    "resolution": resolution,
                    **kwargs
                }
                task_type = AITaskType.VIDEO_GENERATION
                model_type = AIModelType.IMAGE_TO_VIDEO
            elif prompt:
                # 文生视频
                endpoint = f"{self.base_url}/videos/generations"
                request_data = {
                    "model": model,
                    "prompt": prompt,
                    "duration": duration,
                    "fps": fps,
                    "resolution": resolution,
                    **kwargs
                }
                task_type = AITaskType.VIDEO_GENERATION
                model_type = AIModelType.TEXT_TO_VIDEO
            else:
                return AIResponse(
                    success=False,
                    error="必须提供prompt或image_url",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.TEXT_TO_VIDEO
                )
            
            response = await client.post(endpoint, json=request_data)
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get("task_id")
            
            if task_id:
                # 轮询任务状态
                result = await self._poll_task_status(task_id, "video")
                if result:
                    return AIResponse(
                        success=True,
                        data={
                            "video_url": result.get("video_url"),
                            "thumbnail_url": result.get("thumbnail_url"),
                            "duration": duration
                        },
                        provider=self.name,
                        model=model,
                        task_type=task_type,
                        model_type=model_type,
                        metadata={
                            "task_id": task_id,
                            "duration": duration,
                            "fps": fps,
                            "resolution": resolution,
                            "input_image": image_url,
                            "input_prompt": prompt
                        }
                    )
            
            return AIResponse(
                success=False,
                error="视频生成任务失败",
                provider=self.name,
                model=model,
                task_type=task_type,
                model_type=model_type
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO
            )
    
    async def _poll_task_status(
        self, 
        task_id: str, 
        task_type: str,
        max_attempts: int = 60,
        delay: int = 5
    ) -> Optional[Dict[str, Any]]:
        """轮询任务状态"""
        client = await self.get_client()
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{self.base_url}/tasks/{task_id}")
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    return data.get("result")
                elif status == "failed":
                    return None
                elif status in ["pending", "running"]:
                    await asyncio.sleep(delay)
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"轮询任务状态失败 (尝试 {attempt + 1}): {e}")
                await asyncio.sleep(delay)
        
        return None
    
    async def get_task_status(self, task_id: str) -> AIResponse:
        """获取任务状态（公开方法）"""
        try:
            client = await self.get_client()
            
            response = await client.get(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            
            data = response.json()
            
            return AIResponse(
                success=True,
                data=data,
                provider=self.name,
                model="task_status",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO,
                metadata={"task_id": task_id}
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="task_status",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO
            )