"""
AI服务管理器

统一管理所有AI服务提供商，提供负载均衡、故障转移等功能
"""

import asyncio
import random
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .providers.base import BaseProvider, AIResponse, AIModelType, AITaskType, ProviderConfig
from .providers.openai_provider import OpenAIProvider
from .providers.keling_provider import KelingProvider
from .providers.jimeng_provider import JimengProvider
from .providers.minimax_provider import MinimaxProvider
from .providers.deepseek_provider import DeepSeekProvider
from .providers.volcengine_provider import VolcengineProvider
from app.core.logging import get_logger


class ProviderPriority(Enum):
    """提供商优先级"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class ProviderWeight:
    """提供商权重配置"""
    provider_name: str
    weight: float = 1.0  # 权重，越高越容易被选中
    priority: ProviderPriority = ProviderPriority.MEDIUM
    enabled: bool = True
    max_requests_per_minute: int = 60
    current_requests: int = 0
    last_reset_time: float = 0.0


@dataclass
class AIServiceConfig:
    """AI服务配置"""
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    provider_weights: Dict[str, ProviderWeight] = field(default_factory=dict)
    enable_fallback: bool = True
    enable_load_balancing: bool = True
    default_timeout: float = 30.0
    max_retries: int = 3


class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self, config: AIServiceConfig):
        self.config = config
        self.providers: Dict[str, BaseProvider] = {}
        self.provider_classes = {
            "openai": OpenAIProvider,
            "keling": KelingProvider,
            "jimeng": JimengProvider,
            "minimax": MinimaxProvider,
            "deepseek": DeepSeekProvider,
            "volcengine": VolcengineProvider
        }
        self._initialize_providers()
        self.logger = get_logger()

    def _truncate(self, text: Any, limit: int = 2000) -> str:
        try:
            s = str(text)
        except Exception:
            s = repr(text)
        if not s:
            return ""
        return s if len(s) <= limit else s[:limit] + "...<truncated>"

    def _log_request(self, *, task: str, provider: Optional[str], model: Optional[str], params: Dict[str, Any] | None = None):
        try:
            self.logger.info(
                f"LLM Request | task={task} provider={provider or 'auto'} model={model or 'auto'} params={params or {}}"
            )
        except Exception:
            pass

    def _log_prompt(self, prompt: Optional[str]):
        if prompt is None:
            return
        try:
            self.logger.info(f"LLM Prompt Preview: {self._truncate(prompt, 2000)}")
        except Exception:
            pass

    def _log_response(self, *, task: str, provider: Optional[str], model: Optional[str], response: AIResponse):
        try:
            status = "success" if (response and response.success) else "failure"
            body_preview = self._truncate(response.data if response else None, 2000)
            usage = getattr(response, 'usage', None)
            p = response.provider if response and response.provider else provider
            m = response.model if response and response.model else model
            self.logger.info(
                f"LLM Response | task={task} provider={p} model={m} status={status} usage={usage} body={body_preview}"
            )
        except Exception:
            pass
    
    def _initialize_providers(self):
        """初始化所有提供商"""
        for provider_name, provider_config in self.config.providers.items():
            if provider_name in self.provider_classes:
                provider_class = self.provider_classes[provider_name]
                self.providers[provider_name] = provider_class(provider_config)
                
                # 初始化权重配置
                if provider_name not in self.config.provider_weights:
                    self.config.provider_weights[provider_name] = ProviderWeight(
                        provider_name=provider_name
                    )
    
    def get_available_providers(
        self, 
        model_type: AIModelType = None,
        task_type: AITaskType = None
    ) -> List[str]:
        """获取可用的提供商列表"""
        available = []
        
        for name, provider in self.providers.items():
            weight = self.config.provider_weights.get(name)
            if not weight or not weight.enabled:
                continue
                
            # 检查是否支持指定的模型类型
            if model_type and model_type not in provider.supported_model_types:
                continue
                
            # 检查请求频率限制
            if self._check_rate_limit(name):
                available.append(name)
        
        return available
    
    def _check_rate_limit(self, provider_name: str) -> bool:
        """检查提供商的请求频率限制"""
        weight = self.config.provider_weights.get(provider_name)
        if not weight:
            return True
            
        import time
        current_time = time.time()
        
        # 每分钟重置计数器
        if current_time - weight.last_reset_time > 60:
            weight.current_requests = 0
            weight.last_reset_time = current_time
        
        return weight.current_requests < weight.max_requests_per_minute
    
    def _select_provider(
        self, 
        available_providers: List[str],
        prefer_provider: str = None
    ) -> Optional[str]:
        """选择最佳提供商"""
        if not available_providers:
            return None
            
        # 如果指定了首选提供商且可用，直接使用
        if prefer_provider and prefer_provider in available_providers:
            return prefer_provider
        
        if not self.config.enable_load_balancing:
            # 不启用负载均衡时，按优先级选择
            return self._select_by_priority(available_providers)
        
        # 启用负载均衡时，按权重随机选择
        return self._select_by_weight(available_providers)
    
    def _select_by_priority(self, providers: List[str]) -> str:
        """按优先级选择提供商"""
        priority_map = {}
        for name in providers:
            weight = self.config.provider_weights.get(name)
            priority = weight.priority.value if weight else ProviderPriority.MEDIUM.value
            if priority not in priority_map:
                priority_map[priority] = []
            priority_map[priority].append(name)
        
        # 选择最高优先级的提供商
        highest_priority = min(priority_map.keys())
        return random.choice(priority_map[highest_priority])
    
    def _select_by_weight(self, providers: List[str]) -> str:
        """按权重选择提供商"""
        weights = []
        for name in providers:
            weight = self.config.provider_weights.get(name)
            weights.append(weight.weight if weight else 1.0)
        
        # 加权随机选择
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(providers)
        
        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return providers[i]
        
        return providers[-1]
    
    def _update_request_count(self, provider_name: str):
        """更新请求计数"""
        weight = self.config.provider_weights.get(provider_name)
        if weight:
            weight.current_requests += 1
    
    async def generate_text(
        self,
        prompt: str,
        model: str = None,
        prefer_provider: str = None,
        system_prompt: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        json_schema: dict | None = None,
        **kwargs
    ) -> AIResponse:
        """统一文本生成接口"""
        available_providers = self.get_available_providers(
            model_type=AIModelType.TEXT_GENERATION
        )
        
        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的文本生成提供商",
                provider="ai_service_manager",
                model=model or "unknown",
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION
            )
        
        # 记录请求
        self._log_request(task="generate_text", provider=prefer_provider, model=model, params={
            "max_tokens": max_tokens, "temperature": temperature, "json_schema": True if json_schema else False
        })
        self._log_prompt(prompt)

        # 选择提供商并尝试生成
        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break
                
            provider = self.providers[provider_name]
            self._update_request_count(provider_name)
            
            # 如果未指定模型，使用提供商的默认模型
            if not model:
                available_models = provider.available_models
                text_models = [m for m in available_models if m.model_type == AIModelType.TEXT_GENERATION]
                model = text_models[0].model_id if text_models else "default"
            
            try:
                response = await provider.generate_text(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_schema=json_schema,
                    **kwargs
                )
                # 记录响应
                self._log_response(task="generate_text", provider=provider_name, model=model, response=response)
                if response.success or not self.config.enable_fallback:
                    return response
                    
            except Exception as e:
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"文本生成失败: {str(e)}",
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.STORY_GENERATION,
                        model_type=AIModelType.TEXT_GENERATION
                    )
            
            # 失败时从可用列表中移除该提供商
            if provider_name in available_providers:
                available_providers.remove(provider_name)
        
        return AIResponse(
            success=False,
            error="所有文本生成提供商都失败了",
            provider="ai_service_manager",
            model=model,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION
        )
    
    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        prefer_provider: str = None,
        width: int = 1024,
        height: int = 1024,
        style: str = "realistic",
        **kwargs
    ) -> AIResponse:
        """统一图像生成接口"""
        available_providers = self.get_available_providers(
            model_type=AIModelType.TEXT_TO_IMAGE
        )
        
        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的图像生成提供商",
                provider="ai_service_manager",
                model=model or "unknown",
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE
            )
        
        # 记录请求
        self._log_request(task="generate_image", provider=prefer_provider, model=model, params={
            "width": width, "height": height, "style": style
        })
        self._log_prompt(kwargs.get("prompt_override", prompt))

        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break
                
            provider = self.providers[provider_name]
            self._update_request_count(provider_name)
            
            # 选择合适的默认模型
            if not model:
                available_models = provider.available_models
                image_models = [m for m in available_models if m.model_type == AIModelType.TEXT_TO_IMAGE]
                model = image_models[0].model_id if image_models else "default"
            
            try:
                response = await provider.generate_image(
                    prompt=prompt,
                    model=model,
                    width=width,
                    height=height,
                    style=style,
                    **kwargs
                )
                self._log_response(task="generate_image", provider=provider_name, model=model, response=response)
                if response.success or not self.config.enable_fallback:
                    return response
                    
            except Exception as e:
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"图像生成失败: {str(e)}",
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE
                    )
            
            if provider_name in available_providers:
                available_providers.remove(provider_name)
        
        return AIResponse(
            success=False,
            error="所有图像生成提供商都失败了",
            provider="ai_service_manager",
            model=model,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE
        )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str | None = None,
        model: str | None = None,
        prefer_provider: str | None = None,
        **kwargs,
    ) -> AIResponse:
        """统一图生图接口"""
        available_providers = self.get_available_providers(
            model_type=AIModelType.IMAGE_TO_IMAGE
        )

        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的图生图提供商",
                provider="ai_service_manager",
                model=model or "unknown",
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        self._log_request(
            task="image_to_image",
            provider=prefer_provider,
            model=model,
            params={"image_url": image_url},
        )
        self._log_prompt(prompt)

        for _ in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            # 选择合适的默认模型（image_to_image 类型），必要时退回到 text_to_image 模型
            effective_model = model
            if not effective_model:
                img2img_models = [
                    m for m in provider.available_models if m.model_type == AIModelType.IMAGE_TO_IMAGE
                ]
                if img2img_models:
                    effective_model = img2img_models[0].model_id
                else:
                    t2i_models = [
                        m for m in provider.available_models if m.model_type == AIModelType.TEXT_TO_IMAGE
                    ]
                    effective_model = t2i_models[0].model_id if t2i_models else "default"

            try:
                # 部分提供商可能未重写 image_to_image，此时调用 BaseProvider 的默认实现返回未实现错误
                response = await provider.image_to_image(
                    image_url=image_url,
                    prompt=prompt,
                    model=effective_model,
                    **kwargs,
                )
                self._log_response(
                    task="image_to_image",
                    provider=provider_name,
                    model=effective_model,
                    response=response,
                )
                if response.success or not self.config.enable_fallback:
                    return response
            except Exception as e:
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"图生图失败: {str(e)}",
                        provider=provider_name,
                        model=effective_model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.IMAGE_TO_IMAGE,
                    )

            if provider_name in available_providers:
                available_providers.remove(provider_name)

        return AIResponse(
            success=False,
            error="所有图生图提供商都失败了",
            provider="ai_service_manager",
            model=model or "unknown",
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )
    
    async def generate_video(
        self,
        prompt: str = None,
        image_url: str = None,
        model: str = None,
        prefer_provider: str = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        **kwargs
    ) -> AIResponse:
        """统一视频生成接口"""
        # 根据输入类型确定模型类型
        model_type = AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
        
        available_providers = self.get_available_providers(model_type=model_type)
        
        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的视频生成提供商",
                provider="ai_service_manager",
                model=model or "unknown",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=model_type
            )
        
        # 记录请求
        self._log_request(task="generate_video", provider=prefer_provider, model=model, params={
            "duration": duration, "fps": fps, "resolution": resolution, "mode": ("image_to_video" if image_url else "text_to_video")
        })
        self._log_prompt(prompt if not image_url else f"<image_url>: {self._truncate(image_url, 256)}")

        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break
                
            provider = self.providers[provider_name]
            self._update_request_count(provider_name)
            
            try:
                # 根据提供商类型调用不同方法
                if hasattr(provider, 'generate_video'):
                    response = await provider.generate_video(
                        prompt=prompt,
                        image_url=image_url,
                        model=model,
                        duration=duration,
                        fps=fps,
                        resolution=resolution,
                        **kwargs
                    )
                else:
                    response = AIResponse(
                        success=False,
                        error=f"提供商 {provider_name} 不支持视频生成",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VIDEO_GENERATION,
                        model_type=model_type
                    )
                self._log_response(task="generate_video", provider=provider_name, model=model, response=response)
                if response.success or not self.config.enable_fallback:
                    return response
                    
            except Exception as e:
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"视频生成失败: {str(e)}",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VIDEO_GENERATION,
                        model_type=model_type
                    )
            
            if provider_name in available_providers:
                available_providers.remove(provider_name)
        
        return AIResponse(
            success=False,
            error="所有视频生成提供商都失败了",
            provider="ai_service_manager",
            model=model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type
        )
    
    async def text_to_speech(
        self,
        text: str,
        model: str = None,
        prefer_provider: str = None,
        voice_type: str = None,
        speed: float = 1.0,
        **kwargs
    ) -> AIResponse:
        """统一语音合成接口"""
        available_providers = self.get_available_providers(
            model_type=AIModelType.TEXT_TO_SPEECH
        )
        
        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的语音合成提供商",
                provider="ai_service_manager",
                model=model or "unknown",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
        
        # 记录请求
        self._log_request(task="text_to_speech", provider=prefer_provider, model=model, params={
            "voice_type": voice_type, "speed": speed
        })
        self._log_prompt(text)

        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break
                
            provider = self.providers[provider_name]
            self._update_request_count(provider_name)
            
            try:
                if hasattr(provider, 'text_to_speech'):
                    response = await provider.text_to_speech(
                        text=text,
                        model=model,
                        voice_type=voice_type,
                        speed=speed,
                        **kwargs
                    )
                else:
                    response = AIResponse(
                        success=False,
                        error=f"提供商 {provider_name} 不支持语音合成",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VOICE_GENERATION,
                        model_type=AIModelType.TEXT_TO_SPEECH
                    )
                self._log_response(task="text_to_speech", provider=provider_name, model=model, response=response)
                if response.success or not self.config.enable_fallback:
                    return response
                    
            except Exception as e:
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"语音合成失败: {str(e)}",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VOICE_GENERATION,
                        model_type=AIModelType.TEXT_TO_SPEECH
                    )
            
            if provider_name in available_providers:
                available_providers.remove(provider_name)
        
        return AIResponse(
            success=False,
            error="所有语音合成提供商都失败了",
            provider="ai_service_manager",
            model=model,
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH
        )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """获取所有提供商的状态"""
        status = {}
        for name, provider in self.providers.items():
            weight = self.config.provider_weights.get(name)
            status[name] = {
                "enabled": weight.enabled if weight else True,
                "priority": weight.priority.name if weight else "MEDIUM",
                "weight": weight.weight if weight else 1.0,
                "current_requests": weight.current_requests if weight else 0,
                "max_requests_per_minute": weight.max_requests_per_minute if weight else 60,
                "supported_model_types": [mt.value for mt in provider.supported_model_types],
                "available_models": [
                    {
                        "id": model.model_id,
                        "name": model.name,
                        "type": model.model_type.value,
                        "capabilities": model.capabilities
                    }
                    for model in provider.available_models
                ]
            }
        return status
    
    def update_provider_config(
        self, 
        provider_name: str, 
        enabled: bool = None,
        weight: float = None,
        priority: ProviderPriority = None,
        max_requests_per_minute: int = None
    ):
        """更新提供商配置"""
        if provider_name not in self.config.provider_weights:
            self.config.provider_weights[provider_name] = ProviderWeight(
                provider_name=provider_name
            )
        
        weight_config = self.config.provider_weights[provider_name]
        
        if enabled is not None:
            weight_config.enabled = enabled
        if weight is not None:
            weight_config.weight = weight
        if priority is not None:
            weight_config.priority = priority
        if max_requests_per_minute is not None:
            weight_config.max_requests_per_minute = max_requests_per_minute
