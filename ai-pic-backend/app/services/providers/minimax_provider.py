"""
MiniMax服务提供商

支持文本生成和语音相关功能
"""

import httpx
import json
from typing import List, Optional, Dict, Any
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig

class MinimaxProvider(BaseProvider):
    """MiniMax服务提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.minimax.chat/v1"
        self.group_id = config.group_id if hasattr(config, 'group_id') else None
    
    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_SPEECH
        ]
    
    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            # 文本生成模型
            ModelInfo(
                model_id="abab6.5s-chat",
                name="MiniMax Chat 6.5s",
                description="快速响应的对话模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=8192,
                capabilities=["chat", "fast_response", "chinese_optimized"]
            ),
            ModelInfo(
                model_id="abab6.5-chat",
                name="MiniMax Chat 6.5",
                description="平衡性能和质量的对话模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=16384,
                capabilities=["chat", "balanced", "multi_turn"]
            ),
            ModelInfo(
                model_id="abab6.5g-chat",
                name="MiniMax Chat 6.5g",
                description="高质量文本生成模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=32768,
                capabilities=["chat", "high_quality", "long_context"]
            ),
            # 语音合成模型
            ModelInfo(
                model_id="speech-01",
                name="MiniMax TTS",
                description="高质量语音合成",
                model_type=AIModelType.TEXT_TO_SPEECH,
                supported_formats=["mp3", "wav"],
                capabilities=["text_to_speech", "multiple_voices", "emotion_control"]
            ),
            ModelInfo(
                model_id="speech-01-240228",
                name="MiniMax TTS Pro",
                description="专业版语音合成，支持更多语音",
                model_type=AIModelType.TEXT_TO_SPEECH,
                supported_formats=["mp3", "wav"],
                capabilities=["text_to_speech", "voice_cloning", "prosody_control"]
            )
        ]
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 如果有group_id，添加到头部
        if self.group_id:
            headers["GroupId"] = self.group_id
        
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers
        )
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "abab6.5-chat",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str = None,
        **kwargs
    ) -> AIResponse:
        """使用MiniMax生成文本"""
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
                **kwargs
            }
            
            response = await client.post(
                f"{self.base_url}/text/chatcompletion_v2",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("base_resp", {}).get("status_code") == 0:
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
                        "total_tokens": data.get("usage", {}).get("total_tokens", 0)
                    }
                )
            else:
                error_msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                return AIResponse(
                    success=False,
                    error=f"MiniMax API错误: {error_msg}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.STORY_GENERATION,
                    model_type=AIModelType.TEXT_GENERATION
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
    
    async def generate_image(self, prompt: str, model: str = None, **kwargs) -> AIResponse:
        """MiniMax不支持图像生成"""
        return AIResponse(
            success=False,
            error="MiniMax暂不支持图像生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE
        )
    
    async def text_to_speech(
        self, 
        text: str, 
        model: str = "speech-01",
        voice_id: str = "female-shaonv",
        speed: float = 1.0,
        pitch: float = 0.0,
        emotion: str = "neutral",
        format: str = "mp3",
        **kwargs
    ) -> AIResponse:
        """MiniMax文本转语音"""
        try:
            client = await self.get_client()
            
            request_data = {
                "model": model,
                "text": text,
                "voice_id": voice_id,
                "speed": speed,
                "pitch": pitch,
                "emotion": emotion,
                "format": format,
                **kwargs
            }
            
            response = await client.post(
                f"{self.base_url}/t2a_v2",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("base_resp", {}).get("status_code") == 0:
                audio_file = data.get("audio_file")
                extra_audio_file = data.get("extra_audio_file")
                
                return AIResponse(
                    success=True,
                    data={
                        "audio_url": audio_file,
                        "extra_audio_url": extra_audio_file,
                        "duration": data.get("duration")
                    },
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VOICE_GENERATION,
                    model_type=AIModelType.TEXT_TO_SPEECH,
                    metadata={
                        "voice_id": voice_id,
                        "speed": speed,
                        "pitch": pitch,
                        "emotion": emotion,
                        "format": format,
                        "text_length": len(text)
                    }
                )
            else:
                error_msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                return AIResponse(
                    success=False,
                    error=f"MiniMax TTS错误: {error_msg}",
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
    
    async def get_voices(self) -> AIResponse:
        """获取可用的语音列表"""
        try:
            # MiniMax预定义的语音列表
            voices = [
                {"voice_id": "female-shaonv", "name": "少女音", "gender": "female", "age": "young"},
                {"voice_id": "female-chengshu", "name": "成熟女声", "gender": "female", "age": "mature"},
                {"voice_id": "male-qingshu", "name": "清澈男声", "gender": "male", "age": "young"},
                {"voice_id": "male-chengshu", "name": "成熟男声", "gender": "male", "age": "mature"},
                {"voice_id": "presenter_male", "name": "男主播", "gender": "male", "style": "broadcast"},
                {"voice_id": "presenter_female", "name": "女主播", "gender": "female", "style": "broadcast"},
                {"voice_id": "audiobook_male_1", "name": "有声书男声1", "gender": "male", "style": "audiobook"},
                {"voice_id": "audiobook_female_1", "name": "有声书女声1", "gender": "female", "style": "audiobook"}
            ]
            
            return AIResponse(
                success=True,
                data=voices,
                provider=self.name,
                model="voice_list",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="voice_list",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )