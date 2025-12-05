"""
火山引擎(Volcengine)服务提供商

支持文本生成、图像生成和视频生成等功能
"""

import httpx
import json
import asyncio
from typing import List, Optional, Dict, Any
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig

class VolcengineProvider(BaseProvider):
    """火山引擎服务提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self.region = config.region if hasattr(config, 'region') else "cn-beijing"
    
    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.TEXT_TO_SPEECH
        ]
    
    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            # 文本生成模型
            ModelInfo(
                model_id="doubao-lite-4k",
                name="豆包轻量版",
                description="轻量级文本生成模型，快速响应",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=4096,
                capabilities=["text_generation", "conversation", "fast_response"]
            ),
            ModelInfo(
                model_id="doubao-pro-4k",
                name="豆包专业版",
                description="专业级文本生成模型，高质量输出",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=4096,
                capabilities=["text_generation", "analysis", "reasoning", "high_quality"]
            ),
            ModelInfo(
                model_id="doubao-pro-32k",
                name="豆包专业版长文本",
                description="支持长文本处理的专业版模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=32768,
                capabilities=["text_generation", "long_context", "document_analysis"]
            ),
            ModelInfo(
                model_id="seedream-4.5",
                name="Seedream 4.5",
                description="方舟大模型服务平台的通用对话/创作模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=32768,
                capabilities=["text_generation", "conversation", "reasoning"]
            ),
            # 图像生成模型
            ModelInfo(
                model_id="volcengine-visual-v1",
                name="火山视觉生成V1",
                description="高质量图像生成模型",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "style_control", "high_resolution"]
            ),
            ModelInfo(
                model_id="volcengine-visual-pro",
                name="火山视觉生成Pro",
                description="专业版图像生成，支持更多风格",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "multiple_styles", "ultra_quality"]
            ),
            # 视频生成模型
            ModelInfo(
                model_id="volcengine-video-v1",
                name="火山视频生成V1",
                description="AI视频生成模型",
                model_type=AIModelType.TEXT_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["text_to_video", "motion_control", "scene_generation"]
            ),
            # 语音合成模型
            ModelInfo(
                model_id="volcengine-tts-v1",
                name="火山语音合成",
                description="高质量语音合成服务",
                model_type=AIModelType.TEXT_TO_SPEECH,
                supported_formats=["mp3", "wav"],
                capabilities=["text_to_speech", "emotion_control", "voice_cloning"]
            )
        ]
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 如果有region信息，添加到头部
        if self.region:
            headers["X-Region"] = self.region
        
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers
        )
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "doubao-pro-4k",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str = None,
        **kwargs
    ) -> AIResponse:
        """使用豆包生成文本"""
        try:
            client = await self.get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False,
                **kwargs
            }
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎API错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.STORY_GENERATION,
                    model_type=AIModelType.TEXT_GENERATION
                )
            
            content = data["choices"][0]["message"]["content"]
            
            return AIResponse(
                success=True,
                data=content,
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
                usage=data.get("usage", {}),
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0)
                }
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION
            )
    
    async def generate_image(
        self, 
        prompt: str, 
        model: str = "volcengine-visual-v1",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.5,
        style: str = "realistic",
        seed: int = -1,
        **kwargs
    ) -> AIResponse:
        """使用火山引擎生成图像"""
        try:
            client = await self.get_client()
            
            request_data = {
                "model": model,
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_inference_steps": steps,
                "guidance_scale": cfg_scale,
                "style": style,
                **kwargs
            }
            
            if seed != -1:
                request_data["seed"] = seed
            
            response = await client.post(
                f"{self.base_url}/images/generations",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎图像生成错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE
                )
            
            # 检查是否为异步任务
            if "task_id" in data:
                task_id = data["task_id"]
                result = await self._poll_task_status(task_id, "image")
                if result:
                    return AIResponse(
                        success=True,
                        data={"images": result.get("images", [])},
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE,
                        metadata={
                            "task_id": task_id,
                            "width": width,
                            "height": height,
                            "steps": steps,
                            "cfg_scale": cfg_scale,
                            "style": style,
                            "seed": result.get("seed")
                        }
                    )
            elif "data" in data:
                # 直接返回结果
                images = data["data"]
                return AIResponse(
                    success=True,
                    data={"images": [img.get("url") for img in images]},
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                    metadata={
                        "width": width,
                        "height": height,
                        "steps": steps,
                        "cfg_scale": cfg_scale,
                        "style": style,
                        "count": len(images)
                    }
                )
            
            return AIResponse(
                success=False,
                error="图像生成响应格式错误",
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE
            )
    
    async def generate_video(
        self, 
        prompt: str, 
        model: str = "volcengine-video-v1",
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        style: str = "realistic",
        **kwargs
    ) -> AIResponse:
        """使用火山引擎生成视频"""
        try:
            client = await self.get_client()
            
            request_data = {
                "model": model,
                "prompt": prompt,
                "duration": duration,
                "fps": fps,
                "resolution": resolution,
                "style": style,
                **kwargs
            }
            
            response = await client.post(
                f"{self.base_url}/videos/generations",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎视频生成错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.TEXT_TO_VIDEO
                )
            
            # 视频生成通常为异步任务
            task_id = data.get("task_id")
            if task_id:
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
                        task_type=AITaskType.VIDEO_GENERATION,
                        model_type=AIModelType.TEXT_TO_VIDEO,
                        metadata={
                            "task_id": task_id,
                            "duration": duration,
                            "fps": fps,
                            "resolution": resolution,
                            "style": style
                        }
                    )
            
            return AIResponse(
                success=False,
                error="视频生成任务失败",
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO
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
    
    async def text_to_speech(
        self, 
        text: str, 
        model: str = "volcengine-tts-v1",
        voice_type: str = "BV001_streaming",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "neutral",
        format: str = "mp3",
        **kwargs
    ) -> AIResponse:
        """火山引擎文本转语音"""
        try:
            client = await self.get_client()
            
            request_data = {
                "app": {
                    "appid": "your_app_id",  # 需要在配置中提供
                    "token": self.config.api_key,
                    "cluster": "volcano_tts"
                },
                "user": {
                    "uid": "user_001"
                },
                "audio": {
                    "voice_type": voice_type,
                    "encoding": format,
                    "speed_ratio": speed,
                    "volume_ratio": volume,
                    "pitch_ratio": pitch,
                    "emotion": emotion
                },
                "request": {
                    "reqid": f"tts_{asyncio.get_event_loop().time()}",
                    "text": text,
                    "text_type": "plain",
                    "operation": "submit"
                }
            }
            
            response = await client.post(
                f"{self.base_url}/tts/submit",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 0:
                # 异步任务，需要轮询结果
                task_id = data.get("task_id")
                if task_id:
                    result = await self._poll_tts_status(task_id)
                    if result:
                        return AIResponse(
                            success=True,
                            data={
                                "audio_url": result.get("audio_url"),
                                "duration": result.get("duration")
                            },
                            provider=self.name,
                            model=model,
                            task_type=AITaskType.VOICE_GENERATION,
                            model_type=AIModelType.TEXT_TO_SPEECH,
                            metadata={
                                "voice_type": voice_type,
                                "speed": speed,
                                "volume": volume,
                                "pitch": pitch,
                                "emotion": emotion,
                                "format": format,
                                "text_length": len(text)
                            }
                        )
            else:
                error_msg = data.get("message", "Unknown error")
                return AIResponse(
                    success=False,
                    error=f"火山引擎TTS错误: {error_msg}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VOICE_GENERATION,
                    model_type=AIModelType.TEXT_TO_SPEECH
                )
            
            return AIResponse(
                success=False,
                error="语音生成任务失败",
                provider=self.name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
    
    async def _poll_task_status(
        self, 
        task_id: str,
        task_type: str,
        max_attempts: int = 60,
        delay: int = 3
    ) -> Optional[Dict[str, Any]]:
        """轮询任务状态"""
        client = await self.get_client()
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(
                    f"{self.base_url}/tasks/{task_id}",
                    params={"task_type": task_type}
                )
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status")
                
                if status == "success":
                    return data.get("result")
                elif status == "failed":
                    return None
                elif status in ["pending", "running", "processing"]:
                    await asyncio.sleep(delay)
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"轮询火山引擎任务状态失败 (尝试 {attempt + 1}): {e}")
                await asyncio.sleep(delay)
        
        return None
    
    async def _poll_tts_status(
        self, 
        task_id: str,
        max_attempts: int = 30,
        delay: int = 2
    ) -> Optional[Dict[str, Any]]:
        """轮询TTS任务状态"""
        client = await self.get_client()
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{self.base_url}/tts/query/{task_id}")
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("code") == 0:
                    audio_info = data.get("data", {})
                    if audio_info.get("status") == "success":
                        return {
                            "audio_url": audio_info.get("audio_url"),
                            "duration": audio_info.get("duration")
                        }
                    elif audio_info.get("status") == "failed":
                        return None
                    else:
                        await asyncio.sleep(delay)
                        continue
                else:
                    return None
                    
            except Exception as e:
                print(f"轮询火山引擎TTS状态失败 (尝试 {attempt + 1}): {e}")
                await asyncio.sleep(delay)
        
        return None
    
    async def get_voice_types(self) -> AIResponse:
        """获取可用的声音类型列表"""
        try:
            # 火山引擎预定义的声音类型
            voice_types = [
                {"voice_type": "BV001_streaming", "name": "通用女声", "gender": "female", "language": "zh"},
                {"voice_type": "BV002_streaming", "name": "通用男声", "gender": "male", "language": "zh"},
                {"voice_type": "BV003_streaming", "name": "温暖女声", "gender": "female", "style": "warm"},
                {"voice_type": "BV004_streaming", "name": "阳光男声", "gender": "male", "style": "energetic"},
                {"voice_type": "BV005_streaming", "name": "知性女声", "gender": "female", "style": "intellectual"},
                {"voice_type": "BV006_streaming", "name": "成熟男声", "gender": "male", "style": "mature"},
                {"voice_type": "BV007_streaming", "name": "甜美女声", "gender": "female", "style": "sweet"},
                {"voice_type": "BV008_streaming", "name": "磁性男声", "gender": "male", "style": "magnetic"}
            ]
            
            return AIResponse(
                success=True,
                data=voice_types,
                provider=self.name,
                model="voice_types",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="voice_types",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
