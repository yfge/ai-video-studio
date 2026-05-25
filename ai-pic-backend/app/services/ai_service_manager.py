"""
AI服务管理器

统一管理所有AI服务提供商，提供负载均衡、故障转移等功能
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services import ai_manager_failure_responses as failure_responses
from app.services import ai_manager_image_assets as image_assets
from app.services import ai_manager_image_fallback as image_fallback
from app.services import ai_manager_image_style as image_style
from app.services import ai_manager_model_listing as model_listing
from app.services import ai_manager_model_resolution as model_resolution
from app.services import ai_manager_provider_selection as provider_selection
from app.services import ai_manager_provider_status as provider_status
from app.services import ai_manager_tts_generation as tts_generation
from app.services import ai_manager_video_generation as video_generation
from app.services.ai_manager_logging import (
    AI_MANAGER_PROVIDER,
    log_prompt,
    log_request,
    log_response,
    truncate,
)

from .providers.base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ProviderConfig,
)
from .providers.deepseek_provider import DeepSeekProvider
from .providers.google_provider import GoogleProvider
from .providers.jimeng_provider import JimengProvider
from .providers.keling_provider import KelingProvider
from .providers.minimax_provider import MinimaxProvider
from .providers.openai_provider import OpenAIProvider
from .providers.volcengine_provider import VolcengineProvider


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
    model_list_cache_ttl: float = 600.0  # 模型列表缓存时间（秒），0 关闭缓存


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
            "volcengine": VolcengineProvider,
            "google": GoogleProvider,
        }
        self._initialize_providers()
        self.logger = get_logger()
        self._models_cache: dict[str, tuple[float, List[Dict[str, Any]]]] = {}

    def _resolve_prefer_provider_and_model(
        self,
        model: str | None,
        prefer_provider: str | None,
    ) -> tuple[str | None, str | None]:
        """
        If model is prefixed like "google:gemini-...", pin to that provider and strip prefix.

        This prevents trying incompatible providers with a foreign model id.
        """
        if model and ":" in model:
            prefix, rest = model.split(":", 1)
            prefix_lower = prefix.lower().strip()
            if prefix_lower in self.providers:
                if prefer_provider and prefer_provider != prefix_lower:
                    try:
                        self.logger.warning(
                            "model provider prefix overrides prefer_provider | model=%s prefer_provider=%s",
                            model,
                            prefer_provider,
                        )
                    except Exception:
                        pass
                return prefix_lower, rest
        return prefer_provider, model

    def _truncate(self, text: Any, limit: int = 2000) -> str:
        return truncate(text, limit)

    def _log_request(
        self,
        *,
        task: str,
        provider: Optional[str],
        model: Optional[str],
        params: Dict[str, Any] | None = None,
    ):
        log_request(
            self.logger,
            task=task,
            provider=provider,
            model=model,
            params=params,
        )

    def _log_prompt(self, prompt: Optional[str]):
        log_prompt(self.logger, prompt)

    def _log_response(
        self,
        *,
        task: str,
        provider: Optional[str],
        model: Optional[str],
        response: AIResponse,
    ):
        log_response(
            self.logger,
            task=task,
            provider=provider,
            model=model,
            response=response,
        )

    async def _convert_base64_images_to_oss(
        self, images: Any, prefix: str = "ai-generated"
    ) -> List[str]:
        return await image_assets.convert_base64_images_to_oss(
            images,
            prefix=prefix,
            logger=self.logger,
        )

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
        self, model_type: AIModelType = None, task_type: AITaskType = None
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
        return provider_selection.check_rate_limit(
            self.config.provider_weights, provider_name
        )

    def _select_provider(
        self, available_providers: List[str], prefer_provider: str = None
    ) -> Optional[str]:
        """选择最佳提供商"""
        return provider_selection.select_provider(
            available_providers,
            self.config.provider_weights,
            enable_load_balancing=self.config.enable_load_balancing,
            default_priority_value=ProviderPriority.MEDIUM.value,
            prefer_provider=prefer_provider,
        )

    def _select_by_priority(self, providers: List[str]) -> str:
        """按优先级选择提供商"""
        return provider_selection.select_by_priority(
            providers,
            self.config.provider_weights,
            default_priority_value=ProviderPriority.MEDIUM.value,
        )

    def _select_by_weight(self, providers: List[str]) -> str:
        """按权重选择提供商"""
        return provider_selection.select_by_weight(
            providers, self.config.provider_weights
        )

    def _update_request_count(self, provider_name: str):
        """更新请求计数"""
        provider_selection.update_request_count(
            self.config.provider_weights, provider_name
        )

    async def _get_models_for_type(
        self,
        provider: BaseProvider,
        model_type: Optional[AIModelType],
    ):
        """统一的模型拉取入口，优先使用远端列表，失败时回退静态配置。"""
        fallback_models = provider.available_models or []
        models = []
        try:
            models = await provider.fetch_remote_models(model_type=model_type)
        except Exception:
            models = []
        if not models:
            models = fallback_models
        return models

    async def list_models(
        self,
        model_type: Optional[AIModelType] = None,
        source: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        聚合所有提供商的模型列表。

        - source='static'：仅使用各 Provider.available_models
        - source='remote'：尽量调用官方模型列表 API（fetch_remote_models），失败时回退静态
        - source='auto'：按 remote 优先，静态兜底
        """
        if not hasattr(self, "_models_cache"):
            self._models_cache = {}
        return await model_listing.list_models(
            providers=self.providers,
            provider_weights=self.config.provider_weights,
            models_cache=self._models_cache,
            cache_ttl=getattr(self.config, "model_list_cache_ttl", 0) or 0,
            model_type=model_type,
            source=source,
            get_models_for_type=self._get_models_for_type,
        )

    async def generate_text(
        self,
        prompt: str,
        model: str = None,
        prefer_provider: str = None,
        system_prompt: str = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        json_schema: dict | None = None,
        stream: bool = True,
        **kwargs,
    ) -> AIResponse:
        """统一文本生成接口"""
        available_providers = self.get_available_providers(
            model_type=AIModelType.TEXT_GENERATION
        )

        prefer_provider, model = self._resolve_prefer_provider_and_model(
            model, prefer_provider
        )
        if prefer_provider:
            available_providers = [
                p for p in available_providers if p == prefer_provider
            ]

        original_model = model
        last_model_used = original_model

        if not available_providers:
            return failure_responses.manager_failure_response(
                error="没有可用的文本生成提供商",
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

        # 记录请求
        params = {
            "temperature": temperature,
            "json_schema": True if json_schema else False,
            "stream": stream,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        self._log_request(
            task="generate_text", provider=prefer_provider, model=model, params=params
        )
        self._log_prompt(prompt)

        # 选择提供商并尝试生成
        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            # 如果未指定模型，为当前 provider 选择默认模型（不污染其他 provider）
            provider_model = await model_resolution.resolve_text_model(
                provider,
                original_model,
                self._get_models_for_type,
            )
            last_model_used = provider_model

            try:
                provider_kwargs = {
                    "prompt": prompt,
                    "model": provider_model,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "json_schema": json_schema,
                    "stream": stream,
                    **kwargs,
                }
                if max_tokens is not None:
                    provider_kwargs["max_tokens"] = max_tokens
                response = await provider.generate_text(**provider_kwargs)
                # 记录响应
                self._log_response(
                    task="generate_text",
                    provider=provider_name,
                    model=provider_model,
                    response=response,
                )
                if response.success or not self.config.enable_fallback:
                    return response

            except Exception as e:
                if not self.config.enable_fallback:
                    return failure_responses.exception_failure_response(
                        action="文本生成失败",
                        exc=e,
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.STORY_GENERATION,
                        model_type=AIModelType.TEXT_GENERATION,
                    )

            # 失败时从可用列表中移除该提供商
            if provider_name in available_providers:
                available_providers.remove(provider_name)

        return failure_responses.manager_failure_response(
            error="所有文本生成提供商都失败了",
            model=last_model_used,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        prefer_provider: str = None,
        width: int = 1024,
        height: int = 1024,
        style: str = "realistic",
        style_preset_id: str | None = None,
        style_spec: Any | None = None,
        **kwargs,
    ) -> AIResponse:
        """统一图像生成接口"""
        style_state = image_style.resolve_text_to_image_style(
            prompt=prompt,
            legacy_style=style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
        )
        prompt = style_state.prompt
        style = style_state.legacy_style
        openai_style_override = style_state.openai_style_override
        resolved_style_spec = style_state.resolved_style_spec
        style_resolution_meta = style_state.resolution_meta

        available_providers = self.get_available_providers(
            model_type=AIModelType.TEXT_TO_IMAGE
        )

        prefer_provider, model = self._resolve_prefer_provider_and_model(
            model, prefer_provider
        )

        # 如果调用方显式指定了首选 provider（或 model 已带 provider 前缀），则仅使用该 provider，避免跨厂商误用模型 id
        if prefer_provider:
            available_providers = [
                p for p in available_providers if p == prefer_provider
            ]

        original_model = model
        last_model_used = original_model

        if not available_providers:
            return failure_responses.manager_failure_response(
                error="没有可用的图像生成提供商",
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        # 记录请求
        self._log_request(
            task="generate_image",
            provider=prefer_provider,
            model=model,
            params={"width": width, "height": height, "style": style},
        )
        self._log_prompt(kwargs.get("prompt_override", prompt))

        last_error: str | None = None
        last_provider: str | None = None
        last_model: str | None = None

        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            # 为当前 provider 选择合适的默认模型，不影响下一轮选择
            provider_model = await model_resolution.resolve_image_model(
                provider,
                original_model,
                self._get_models_for_type,
            )
            last_model_used = provider_model

            try:
                provider_style = style
                if provider_name == "openai":
                    from app.utils.model_utils import normalize_openai_image_style

                    provider_style = normalize_openai_image_style(
                        openai_style_override or provider_style
                    )

                response = await provider.generate_image(
                    prompt=prompt,
                    model=provider_model,
                    width=width,
                    height=height,
                    style=provider_style,
                    **kwargs,
                )
                image_style.attach_style_metadata(
                    response,
                    resolved_style_spec,
                    style_resolution_meta,
                )
                self._log_response(
                    task="generate_image",
                    provider=provider_name,
                    model=provider_model,
                    response=response,
                )
                if not response.success and response.error:
                    last_error = response.error
                    last_provider = provider_name
                    last_model = provider_model
                if response.success or not self.config.enable_fallback:
                    # 将 base64 图片转换为 OSS URL
                    if response.success and response.data and "images" in response.data:
                        converted_images = await self._convert_base64_images_to_oss(
                            response.data["images"],
                            prefix="ai-generated/text-to-image",
                        )
                        response.data["images"] = converted_images
                    return response

            except Exception as e:
                last_error = str(e)
                last_provider = provider_name
                last_model = provider_model
                if not self.config.enable_fallback:
                    return failure_responses.exception_failure_response(
                        action="图像生成失败",
                        exc=e,
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE,
                    )

            if provider_name in available_providers:
                available_providers.remove(provider_name)

        if last_error:
            return failure_responses.failure_response(
                error=failure_responses.provider_prefixed_error(
                    last_error,
                    last_provider,
                ),
                provider=last_provider or AI_MANAGER_PROVIDER,
                model=last_model or last_model_used or model or "unknown",
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        return failure_responses.manager_failure_response(
            error="所有图像生成提供商都失败了",
            model=last_model_used,
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str | None = None,
        model: str | None = None,
        prefer_provider: str | None = None,
        count: int | None = None,
        style_preset_id: str | None = None,
        style_spec: Any | None = None,
        **kwargs,
    ) -> AIResponse:
        """统一图生图接口"""
        legacy_style = str(kwargs.get("style") or "realistic")
        style_state = image_style.resolve_image_to_image_style(
            prompt=prompt,
            legacy_style=legacy_style,
            style_preset_id=style_preset_id,
            style_spec=style_spec,
        )
        prompt = style_state.prompt
        legacy_style = style_state.legacy_style
        resolved_style_spec = style_state.resolved_style_spec
        style_resolution_meta = style_state.resolution_meta
        if resolved_style_spec is not None:
            kwargs["style"] = legacy_style

        available_providers = self.get_available_providers(
            model_type=AIModelType.IMAGE_TO_IMAGE
        )

        prefer_provider, model = self._resolve_prefer_provider_and_model(
            model, prefer_provider
        )

        # 显式指定首选 provider（或 model 带前缀）时，只在该 provider 上尝试，避免带着特定模型 id 在不同厂商间兜底
        if prefer_provider:
            available_providers = [
                p for p in available_providers if p == prefer_provider
            ]

        if not available_providers:
            return failure_responses.manager_failure_response(
                error="没有可用的图生图提供商",
                model=model,
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

        last_error: str | None = None
        last_provider: str | None = None
        last_model: str | None = None

        base64_images = await image_assets.preload_image_references_as_data_urls(
            image_url=image_url,
            extra_images=list(kwargs.get("extra_images") or []),
            prefer_provider=prefer_provider,
            available_providers=available_providers,
            timeout=self.config.default_timeout,
            logger=self.logger,
        )
        if base64_images:
            kwargs["base64_images"] = base64_images

        for _ in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            # 选择合适的默认模型（image_to_image 类型），必要时退回到 text_to_image 模型
            effective_model = await model_resolution.resolve_image_to_image_model(
                provider,
                model,
                self._get_models_for_type,
            )

            try:
                # 部分提供商可能未重写 image_to_image，此时调用 BaseProvider 的默认实现返回未实现错误
                response = await provider.image_to_image(
                    image_url=image_url,
                    prompt=prompt,
                    model=effective_model,
                    n=count or 1,
                    **kwargs,
                )
                self._log_response(
                    task="image_to_image",
                    provider=provider_name,
                    model=effective_model,
                    response=response,
                )
                image_style.attach_style_metadata(
                    response,
                    resolved_style_spec,
                    style_resolution_meta,
                )
                if not response.success:
                    error_value = (response.error or "").strip()
                    if not error_value:
                        error_value = "未知错误"
                    last_error = error_value
                    last_provider = provider_name
                    last_model = effective_model
                if response.success or not self.config.enable_fallback:
                    # 将 base64 图片转换为 OSS URL
                    if response.success and response.data and "images" in response.data:
                        converted_images = await self._convert_base64_images_to_oss(
                            response.data["images"],
                            prefix="ai-generated/image-to-image",
                        )
                        response.data["images"] = converted_images
                    return response
            except Exception as e:
                error_value = str(e).strip() or repr(e)
                last_error = error_value
                last_provider = provider_name
                last_model = effective_model
                if not self.config.enable_fallback:
                    return failure_responses.exception_failure_response(
                        action="图生图失败",
                        exc=e,
                        provider=provider_name,
                        model=effective_model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.IMAGE_TO_IMAGE,
                    )

            if provider_name in available_providers:
                available_providers.remove(provider_name)
        # 所有专用图生图通路失败时，尝试降级为同一模型的文生图（不使用参考图，只保留提示词）
        if self.config.enable_fallback:
            fallback_result = (
                await image_fallback.fallback_image_to_image_as_text_to_image(
                    self.generate_image,
                    prompt=prompt,
                    model=model,
                    prefer_provider=prefer_provider,
                    image_url=image_url,
                    count=count,
                    legacy_style=legacy_style,
                    style_preset_id=style_preset_id,
                    style_spec=style_spec,
                    logger=self.logger,
                )
            )
            if fallback_result.response:
                return fallback_result.response
            if fallback_result.last_error is not None:
                last_error = fallback_result.last_error
                last_provider = fallback_result.last_provider
                last_model = fallback_result.last_model

        if last_error is not None:
            return failure_responses.failure_response(
                error=failure_responses.provider_prefixed_error(
                    last_error,
                    last_provider,
                ),
                provider=last_provider or AI_MANAGER_PROVIDER,
                model=last_model or model or "unknown",
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        return failure_responses.manager_failure_response(
            error="所有图生图提供商都失败了（未捕获到具体错误信息）",
            model=model,
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
        **kwargs,
    ) -> AIResponse:
        """统一视频生成接口"""
        return await video_generation.generate_video_with_fallback(
            prompt=prompt,
            image_url=image_url,
            model=model,
            prefer_provider=prefer_provider,
            duration=duration,
            fps=fps,
            resolution=resolution,
            provider_kwargs=kwargs,
            providers=self.providers,
            max_retries=self.config.max_retries,
            enable_fallback=self.config.enable_fallback,
            resolve_prefer_provider_and_model=self._resolve_prefer_provider_and_model,
            get_available_providers=self.get_available_providers,
            select_provider=self._select_provider,
            update_request_count=self._update_request_count,
            get_models_for_type=self._get_models_for_type,
            log_request=self._log_request,
            log_prompt=self._log_prompt,
            log_response=self._log_response,
            truncate=self._truncate,
        )

    async def text_to_speech(
        self,
        text: str,
        model: str = None,
        prefer_provider: str = None,
        voice_type: str = None,
        speed: float = 1.0,
        **kwargs,
    ) -> AIResponse:
        """统一语音合成接口"""
        return await tts_generation.text_to_speech_with_fallback(
            text=text,
            model=model,
            prefer_provider=prefer_provider,
            voice_type=voice_type,
            speed=speed,
            provider_kwargs=kwargs,
            providers=self.providers,
            max_retries=self.config.max_retries,
            enable_fallback=self.config.enable_fallback,
            get_available_providers=self.get_available_providers,
            select_provider=self._select_provider,
            update_request_count=self._update_request_count,
            log_request=self._log_request,
            log_prompt=self._log_prompt,
            log_response=self._log_response,
        )

    def get_provider_status(self) -> Dict[str, Any]:
        """获取所有提供商的状态"""
        return provider_status.build_provider_status(
            self.providers,
            self.config.provider_weights,
        )

    def update_provider_config(
        self,
        provider_name: str,
        enabled: bool = None,
        weight: float = None,
        priority: ProviderPriority = None,
        max_requests_per_minute: int = None,
    ):
        """更新提供商配置"""
        provider_status.update_provider_config(
            self.config.provider_weights,
            provider_name=provider_name,
            create_provider_weight=ProviderWeight,
            enabled=enabled,
            weight=weight,
            priority=priority,
            max_requests_per_minute=max_requests_per_minute,
        )
