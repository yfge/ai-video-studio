"""
AI服务管理器

统一管理所有AI服务提供商，提供负载均衡、故障转移等功能
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services import ai_manager_model_cache as model_cache
from app.services import ai_manager_provider_selection as provider_selection
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

    def _prefer_http_for_download(self, url: str) -> str:
        """在下载参考图时优先使用 http，避免生产环境 HTTPS 证书问题。"""
        if isinstance(url, str) and url.lower().startswith("https://"):
            return "http://" + url[len("https://") :]
        return url

    def _maybe_compress_inline_image(
        self,
        raw: bytes,
        *,
        content_type: str,
        target_max_bytes: int,
        max_side: int,
    ) -> tuple[bytes, str]:
        """
        Compress large reference images for inline/base64 transport.

        Some providers/proxies (e.g. Gemini via proxy) enforce strict request size limits.
        This helper tries to downscale + re-encode as JPEG when the payload is too large.
        """
        if not raw or len(raw) <= target_max_bytes:
            return raw, content_type or "image/png"

        try:
            from io import BytesIO

            from PIL import Image, ImageOps

            img = Image.open(BytesIO(raw))
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            w, h = img.size
            max_current = max(w, h) if w and h else 0
            if max_current and max_current > max_side:
                scale = max_side / float(max_current)
                new_w = max(1, int(round(w * scale)))
                new_h = max(1, int(round(h * scale)))
                img = img.resize((new_w, new_h), Image.LANCZOS)

            # Try a small number of quality levels to meet size budget
            for quality in (85, 75, 65):
                buf = BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                out = buf.getvalue()
                if out and len(out) <= target_max_bytes:
                    return out, "image/jpeg"

            # Even if we didn't hit the exact budget, return the smallest attempt.
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=60, optimize=True)
            out = buf.getvalue()
            if out:
                return out, "image/jpeg"
        except Exception:
            pass

        return raw, content_type or "image/png"

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
        """
        将 base64 格式的图片上传到 OSS 并返回 URL 列表。

        如果图片已经是 URL 格式，则直接返回。
        如果是 data:image/...;base64,... 格式，则解码后上传到 OSS。

        Args:
            images: 图片列表，可以是 URL 或 base64 格式
            prefix: OSS 存储前缀

        Returns:
            转换后的 URL 列表
        """
        if not images:
            return []

        normalized_images: List[str] = []
        raw_images: list[Any]
        if isinstance(images, list):
            raw_images = images
        else:
            raw_images = [images]

        for img in raw_images:
            candidate: Any = img
            if isinstance(img, dict):
                candidate = img.get("url") or img.get("image_url")
            if candidate is None:
                continue
            if not isinstance(candidate, str):
                candidate = str(candidate)
            candidate = candidate.strip()
            if not candidate:
                continue
            normalized_images.append(candidate)

        if not normalized_images:
            return []

        from app.services.storage.oss_service import oss_service

        if not oss_service:
            self.logger.warning("OSS service not available, returning original images")
            return normalized_images

        result_urls: List[str] = []

        for img in normalized_images:

            # 检查是否是 base64 格式
            if not img.startswith("data:image"):
                # 已经是 URL，直接添加
                result_urls.append(img)
                continue

            try:
                # 解析 base64 数据
                # 格式: data:image/png;base64,iVBORw0KGgo...
                header, b64_data = img.split(",", 1)
                # 从 header 中提取 MIME 类型，如 "data:image/png;base64"
                mime_part = header.split(";")[0]  # "data:image/png"
                mime_type = mime_part.split(":")[1] if ":" in mime_part else "image/png"
                ext = mime_type.split("/")[1] if "/" in mime_type else "png"

                # 上传到 OSS
                from app.services.media import build_generation_metadata
                from app.services.media import upload_base64 as upload_media_base64

                upload_result = await upload_media_base64(
                    base64_payload=b64_data,
                    filename=f"generated.{ext}",
                    media_type="image",
                    prefix=prefix,
                    metadata=build_generation_metadata(
                        provider="unknown",
                        model=None,
                        media_type="image",
                        mime_type=mime_type,
                        extra={"source": "base64"},
                    ),
                    oss_service_override=oss_service,
                )

                if upload_result.get("success"):
                    oss_url = upload_result.get("file_url")
                    result_urls.append(oss_url)
                    approx_size = len(b64_data) * 3 // 4
                    self.logger.info(
                        "Converted base64 image to OSS URL | size=%d url=%s",
                        approx_size,
                        oss_url,
                    )
                else:
                    # 上传失败，保留原始 base64（降级处理）
                    self.logger.warning(
                        "Failed to upload base64 image to OSS: %s",
                        upload_result.get("error"),
                    )
                    result_urls.append(img)

            except Exception as e:
                self.logger.error("Error converting base64 to OSS URL: %s", e)
                # 出错时保留原始数据
                result_urls.append(img)

        return result_urls

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
        cache_ttl = getattr(self.config, "model_list_cache_ttl", 0) or 0
        cache_key = model_cache.model_cache_key(source, model_type)
        cached_models = model_cache.get_cached_models(
            self._models_cache,
            cache_ttl=cache_ttl,
            cache_key=cache_key,
        )
        if cached_models is not None:
            return cached_models

        models: List[Dict[str, Any]] = []
        for provider_name, provider in self.providers.items():
            # 仅枚举已启用的 provider
            weight = self.config.provider_weights.get(provider_name)
            if weight and not weight.enabled:
                continue

            try:
                if source == "static":
                    infos = provider.available_models
                elif source == "remote":
                    infos = await provider.fetch_remote_models(model_type=model_type)
                else:  # auto
                    infos = await self._get_models_for_type(provider, model_type)
            except Exception:
                # 某个 provider 拉取失败，不影响其他 provider
                continue

            if not infos:
                continue

            for mi in infos:
                # model_type 进一步过滤（以防 Provider 忽略了参数）
                if model_type:
                    caps = [str(c).lower() for c in mi.capabilities or []]
                    supports_capability = (
                        model_type == AIModelType.IMAGE_TO_IMAGE
                        and "image_to_image" in caps
                    ) or (
                        model_type == AIModelType.IMAGE_TO_VIDEO
                        and "image_to_video" in caps
                    )
                    if not supports_capability and mi.model_type != model_type:
                        continue
                models.append(
                    {
                        "provider": provider_name,
                        "id": mi.model_id,
                        "name": mi.name,
                        "type": mi.model_type.value,
                        "capabilities": mi.capabilities,
                        "metadata": getattr(mi, "metadata", {}) or {},
                    }
                )

        # 简单排序：provider, name
        models.sort(key=lambda x: (x["provider"], x.get("name") or x["id"]))
        model_cache.store_cached_models(
            self._models_cache,
            cache_ttl=cache_ttl,
            cache_key=cache_key,
            models=models,
        )
        return models

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
            return AIResponse(
                success=False,
                error="没有可用的文本生成提供商",
                provider=AI_MANAGER_PROVIDER,
                model=model or "unknown",
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
            provider_model = original_model
            if not provider_model:
                static_models = [
                    m
                    for m in getattr(
                        provider, "available_models", []
                    )  # static list is more reliable
                    if m.model_type == AIModelType.TEXT_GENERATION
                ]
                if static_models:
                    provider_model = static_models[0].model_id
                else:
                    available_models = await self._get_models_for_type(
                        provider,
                        AIModelType.TEXT_GENERATION,
                    )
                    text_models = available_models
                    provider_model = (
                        text_models[0].model_id
                        if text_models
                        else getattr(provider, "default_model", "default")
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
                    return AIResponse(
                        success=False,
                        error=f"文本生成失败: {str(e)}",
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.STORY_GENERATION,
                        model_type=AIModelType.TEXT_GENERATION,
                    )

            # 失败时从可用列表中移除该提供商
            if provider_name in available_providers:
                available_providers.remove(provider_name)

        return AIResponse(
            success=False,
            error="所有文本生成提供商都失败了",
            provider=AI_MANAGER_PROVIDER,
            model=last_model_used or "unknown",
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
        resolved_style_spec = None
        style_resolution_meta: dict[str, Any] | None = None
        openai_style_override: str | None = None
        try:
            if style_preset_id or style_spec is not None:
                from app.utils.style_utils import (
                    build_style_prompt,
                    derive_legacy_image_style,
                    derive_openai_image_style,
                    resolve_style_spec,
                )

                resolved_style_spec, style_resolution_meta = resolve_style_spec(
                    style_spec=style_spec,
                    style_preset_id=style_preset_id,
                    legacy_style=style,
                    fill_defaults=True,
                )
                style_prompt = build_style_prompt(resolved_style_spec)
                if style_prompt:
                    prompt = f"{prompt.rstrip()}\n\n{style_prompt}"
                style = derive_legacy_image_style(resolved_style_spec)
                openai_style_override = derive_openai_image_style(
                    resolved_style_spec, fallback=style
                )
        except Exception as exc:  # pragma: no cover - defensive
            resolved_style_spec = None
            style_resolution_meta = {"error": str(exc)}

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
            return AIResponse(
                success=False,
                error="没有可用的图像生成提供商",
                provider=AI_MANAGER_PROVIDER,
                model=model or "unknown",
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
            provider_model = original_model
            if not provider_model:
                static_models = [
                    m
                    for m in getattr(provider, "available_models", [])
                    if m.model_type == AIModelType.TEXT_TO_IMAGE
                ]
                if static_models:
                    provider_model = static_models[0].model_id
                else:
                    available_models = await self._get_models_for_type(
                        provider,
                        AIModelType.TEXT_TO_IMAGE,
                    )
                    image_models = available_models
                    provider_model = (
                        image_models[0].model_id
                        if image_models
                        else getattr(provider, "default_model", "default")
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
                if resolved_style_spec is not None:
                    meta = dict(response.metadata or {})
                    meta["style_spec"] = resolved_style_spec.model_dump(
                        mode="json", exclude_none=True
                    )
                    if style_resolution_meta:
                        meta["style_spec_resolution"] = style_resolution_meta
                    response.metadata = meta
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
                    return AIResponse(
                        success=False,
                        error=f"图像生成失败: {str(e)}",
                        provider=provider_name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE,
                    )

            if provider_name in available_providers:
                available_providers.remove(provider_name)

        if last_error:
            error_msg = last_error
            if last_provider and not error_msg.lower().startswith(
                last_provider.lower()
            ):
                error_msg = f"{last_provider}: {error_msg}"
            return AIResponse(
                success=False,
                error=error_msg,
                provider=last_provider or AI_MANAGER_PROVIDER,
                model=last_model or last_model_used or model or "unknown",
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        return AIResponse(
            success=False,
            error="所有图像生成提供商都失败了",
            provider=AI_MANAGER_PROVIDER,
            model=last_model_used or "unknown",
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
        resolved_style_spec = None
        style_resolution_meta: dict[str, Any] | None = None
        legacy_style = str(kwargs.get("style") or "realistic")
        try:
            if style_preset_id or style_spec is not None:
                from app.utils.style_utils import (
                    build_style_prompt,
                    derive_legacy_image_style,
                    resolve_style_spec,
                )

                resolved_style_spec, style_resolution_meta = resolve_style_spec(
                    style_spec=style_spec,
                    style_preset_id=style_preset_id,
                    legacy_style=legacy_style,
                    fill_defaults=True,
                )
                style_prompt = build_style_prompt(resolved_style_spec)
                if style_prompt:
                    if prompt:
                        prompt = f"{prompt.rstrip()}\n\n{style_prompt}"
                    else:
                        prompt = style_prompt
                legacy_style = derive_legacy_image_style(resolved_style_spec)
                kwargs["style"] = legacy_style
        except Exception as exc:  # pragma: no cover - defensive
            resolved_style_spec = None
            style_resolution_meta = {"error": str(exc)}

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
            return AIResponse(
                success=False,
                error="没有可用的图生图提供商",
                provider=AI_MANAGER_PROVIDER,
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

        last_error: str | None = None
        last_provider: str | None = None
        last_model: str | None = None

        # 预读取参考图，转换为 data:image/...;base64,...，避免外部模型无法访问内网 URL
        base64_images: list[str] = []
        try:
            # 去重并过滤空 URL，最多预读取 14 张参考图
            urls_raw = [image_url] + list(kwargs.get("extra_images") or [])
            urls: list[str] = []
            for u in urls_raw:
                if not u:
                    continue
                if u not in urls:
                    urls.append(u)

            if urls:
                import base64

                import httpx

                # Google/Gemini 代理往往限制请求体大小，提前压缩参考图以避免 413
                prefer_is_google = (prefer_provider or "").lower() == "google"
                maybe_google = prefer_is_google or ("google" in available_providers)
                max_refs = 4 if prefer_is_google else (8 if maybe_google else 14)
                target_max_bytes = (
                    220_000
                    if prefer_is_google
                    else (350_000 if maybe_google else 2_000_000)
                )
                max_side = 512 if prefer_is_google else (768 if maybe_google else 2048)

                async with httpx.AsyncClient(
                    timeout=self.config.default_timeout,
                    trust_env=False,
                    follow_redirects=True,
                ) as client:
                    for url in urls[:max_refs]:
                        try:
                            download_url = self._prefer_http_for_download(url)
                            resp = await client.get(download_url)
                            resp.raise_for_status()
                        except Exception as e:
                            # 局部失败时仅跳过该 URL，不让单个 404/网络错误拖垮整个图生图调用
                            self.logger.warning(
                                "image_to_image base64 preload skip url=%s error=%s",
                                self._truncate(str(download_url), 256),
                                e,
                            )
                            continue

                        ctype = resp.headers.get("Content-Type", "image/png")
                        content, ctype = self._maybe_compress_inline_image(
                            resp.content,
                            content_type=ctype,
                            target_max_bytes=target_max_bytes,
                            max_side=max_side,
                        )
                        subtype = "png"
                        if "/" in ctype:
                            subtype = (
                                ctype.split("/", 1)[1].split(";", 1)[0] or "png"
                            ).strip()
                        b64 = base64.b64encode(content).decode("ascii")
                        base64_images.append(
                            f"data:image/{subtype.lower()};base64,{b64}"
                        )

                if base64_images:
                    # 将处理好的 base64 传递给 provider，避免重复下载
                    kwargs["base64_images"] = base64_images
                else:
                    self.logger.warning(
                        "image_to_image base64 preload finished with no valid images | urls=%s",
                        [self._truncate(str(u), 128) for u in urls],
                    )
        except Exception as e:
            # 预加载整体失败时记录告警，但不阻断后续 Provider 内部的 URL 访问/兜底逻辑
            self.logger.warning("image_to_image base64 preload failed: %s", e)

        for _ in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            # 选择合适的默认模型（image_to_image 类型），必要时退回到 text_to_image 模型
            effective_model = model
            if not effective_model:
                img2img_models = await self._get_models_for_type(
                    provider,
                    AIModelType.IMAGE_TO_IMAGE,
                )
                if img2img_models:
                    effective_model = img2img_models[0].model_id
                else:
                    t2i_models = await self._get_models_for_type(
                        provider,
                        AIModelType.TEXT_TO_IMAGE,
                    )
                    effective_model = (
                        t2i_models[0].model_id if t2i_models else "default"
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
                if resolved_style_spec is not None:
                    meta = dict(response.metadata or {})
                    meta["style_spec"] = resolved_style_spec.model_dump(
                        mode="json", exclude_none=True
                    )
                    if style_resolution_meta:
                        meta["style_spec_resolution"] = style_resolution_meta
                    response.metadata = meta
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
        # 所有专用图生图通路失败时，尝试降级为同一模型的文生图（不使用参考图，只保留提示词）
        if self.config.enable_fallback:
            try:
                inferred_provider: str | None = None
                if model:
                    lower = model.lower()
                    if (
                        lower.startswith("seedream")
                        or lower.startswith("volcengine")
                        or "doubao" in lower
                        or "seedream" in lower
                    ):
                        inferred_provider = "volcengine"
                    elif lower.startswith("deepseek"):
                        inferred_provider = "deepseek"
                    elif lower.startswith("keling") or lower.startswith("kling"):
                        inferred_provider = "keling"
                    elif lower.startswith("jimeng"):
                        inferred_provider = "jimeng"
                    elif lower.startswith(("dall-e", "dalle", "gpt-image", "img-gen")):
                        inferred_provider = "openai"
                    elif lower.startswith("gemini"):
                        inferred_provider = "google"

                fallback_prompt = (
                    prompt or "为当前角色生成不同视角/姿态的图像，例如背面照或全身照"
                )
                self.logger.warning(
                    "image_to_image fallback: using text-to-image without reference | model=%s provider_hint=%s image_url=%s",
                    model,
                    inferred_provider or prefer_provider,
                    self._truncate(image_url, 256),
                )

                text_resp = await self.generate_image(
                    prompt=fallback_prompt,
                    model=model,
                    prefer_provider=inferred_provider or prefer_provider,
                    prompt_override=fallback_prompt,
                    style=legacy_style,
                    style_preset_id=style_preset_id,
                    style_spec=style_spec,
                    n=count or 1,
                )
                if text_resp and text_resp.success:
                    meta = dict(text_resp.metadata or {})
                    meta.update(
                        {
                            "fallback_mode": "text_to_image_without_reference",
                            "fallback_from": "image_to_image",
                            "original_image_url": image_url,
                        }
                    )
                    text_resp.metadata = meta
                    text_resp.model_type = AIModelType.IMAGE_TO_IMAGE
                    text_resp.task_type = AITaskType.SCENE_GENERATION
                    return text_resp
                if text_resp and not text_resp.success:
                    error_value = (text_resp.error or "").strip()
                    if not error_value:
                        error_value = "未知错误"
                    last_error = error_value
                    last_provider = text_resp.provider
                    last_model = text_resp.model
            except Exception as e:
                last_error = str(e).strip() or repr(e)
                self.logger.error("image_to_image fallback failed: %s", e)

        if last_error is not None:
            error_msg = (last_error or "").strip() or "未知错误"
            if last_provider and not error_msg.lower().startswith(
                last_provider.lower()
            ):
                error_msg = f"{last_provider}: {error_msg}"
            return AIResponse(
                success=False,
                error=error_msg,
                provider=last_provider or AI_MANAGER_PROVIDER,
                model=last_model or model or "unknown",
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        return AIResponse(
            success=False,
            error="所有图生图提供商都失败了（未捕获到具体错误信息）",
            provider=AI_MANAGER_PROVIDER,
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
        **kwargs,
    ) -> AIResponse:
        """统一视频生成接口"""
        # 根据输入类型确定模型类型
        model_type = (
            AIModelType.IMAGE_TO_VIDEO if image_url else AIModelType.TEXT_TO_VIDEO
        )

        available_providers = self.get_available_providers(model_type=model_type)

        prefer_provider, model = self._resolve_prefer_provider_and_model(
            model, prefer_provider
        )
        if prefer_provider:
            available_providers = [
                p for p in available_providers if p == prefer_provider
            ]

        original_model = model
        last_model_used = original_model
        last_error: str | None = None
        last_provider: str | None = None

        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的视频生成提供商",
                provider=AI_MANAGER_PROVIDER,
                model=model or "unknown",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=model_type,
            )

        # 记录请求
        self._log_request(
            task="generate_video",
            provider=prefer_provider,
            model=model,
            params={
                "duration": duration,
                "fps": fps,
                "resolution": resolution,
                "mode": ("image_to_video" if image_url else "text_to_video"),
            },
        )
        self._log_prompt(
            prompt
            if not image_url
            else f"<image_url>: {self._truncate(image_url, 256)}"
        )

        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            try:
                provider_model = original_model
                if not provider_model:
                    static_models = [
                        m
                        for m in getattr(provider, "available_models", [])
                        if m.model_type == model_type
                    ]
                    if not static_models and model_type == AIModelType.IMAGE_TO_VIDEO:
                        static_models = [
                            m
                            for m in getattr(provider, "available_models", [])
                            if m.model_type == AIModelType.TEXT_TO_VIDEO
                        ]
                    if static_models:
                        provider_model = static_models[0].model_id
                    else:
                        available_models = await self._get_models_for_type(
                            provider,
                            model_type,
                        )
                        if (
                            not available_models
                            and model_type == AIModelType.IMAGE_TO_VIDEO
                        ):
                            available_models = await self._get_models_for_type(
                                provider,
                                AIModelType.TEXT_TO_VIDEO,
                            )
                        provider_model = (
                            available_models[0].model_id
                            if available_models
                            else getattr(provider, "default_model", "default")
                        )
                last_model_used = provider_model

                # 根据提供商类型调用不同方法
                if hasattr(provider, "generate_video"):
                    response = await provider.generate_video(
                        prompt=prompt,
                        image_url=image_url,
                        model=provider_model,
                        duration=duration,
                        fps=fps,
                        resolution=resolution,
                        **kwargs,
                    )
                else:
                    response = AIResponse(
                        success=False,
                        error=f"提供商 {provider_name} 不支持视频生成",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VIDEO_GENERATION,
                        model_type=model_type,
                    )
                self._log_response(
                    task="generate_video",
                    provider=provider_name,
                    model=provider_model,
                    response=response,
                )
                if not response.success and response.error:
                    last_error = response.error
                    last_provider = provider_name
                if response.success or not self.config.enable_fallback:
                    return response

            except Exception as e:
                last_error = str(e)
                last_provider = provider_name
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"视频生成失败: {str(e)}",
                        provider=provider_name,
                        model=last_model_used or "unknown",
                        task_type=AITaskType.VIDEO_GENERATION,
                        model_type=model_type,
                    )

            if provider_name in available_providers:
                available_providers.remove(provider_name)

        error_msg = last_error or "所有视频生成提供商都失败了"
        if last_provider and not error_msg.lower().startswith(last_provider.lower()):
            error_msg = f"{last_provider}: {error_msg}"
        return AIResponse(
            success=False,
            error=error_msg,
            provider=last_provider or AI_MANAGER_PROVIDER,
            model=last_model_used or "unknown",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=model_type,
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
        available_providers = self.get_available_providers(
            model_type=AIModelType.TEXT_TO_SPEECH
        )

        last_error: str | None = None
        last_provider: str | None = None

        if not available_providers:
            return AIResponse(
                success=False,
                error="没有可用的语音合成提供商",
                provider=AI_MANAGER_PROVIDER,
                model=model or "unknown",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH,
            )

        # 记录请求
        self._log_request(
            task="text_to_speech",
            provider=prefer_provider,
            model=model,
            params={"voice_type": voice_type, "speed": speed},
        )
        self._log_prompt(text)

        for attempt in range(self.config.max_retries):
            provider_name = self._select_provider(available_providers, prefer_provider)
            if not provider_name:
                break

            provider = self.providers[provider_name]
            self._update_request_count(provider_name)

            try:
                if hasattr(provider, "text_to_speech"):
                    response = await provider.text_to_speech(
                        text=text,
                        model=model,
                        voice_type=voice_type,
                        speed=speed,
                        **kwargs,
                    )
                else:
                    response = AIResponse(
                        success=False,
                        error=f"提供商 {provider_name} 不支持语音合成",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VOICE_GENERATION,
                        model_type=AIModelType.TEXT_TO_SPEECH,
                    )
                self._log_response(
                    task="text_to_speech",
                    provider=provider_name,
                    model=model,
                    response=response,
                )
                if not response.success and response.error:
                    last_error = response.error
                    last_provider = provider_name
                if response.success or not self.config.enable_fallback:
                    return response

            except Exception as e:
                last_error = str(e)
                last_provider = provider_name
                if not self.config.enable_fallback:
                    return AIResponse(
                        success=False,
                        error=f"语音合成失败: {str(e)}",
                        provider=provider_name,
                        model=model or "unknown",
                        task_type=AITaskType.VOICE_GENERATION,
                        model_type=AIModelType.TEXT_TO_SPEECH,
                    )

            if provider_name in available_providers:
                available_providers.remove(provider_name)

        error_msg = last_error or "所有语音合成提供商都失败了"
        if last_provider and not error_msg.lower().startswith(last_provider.lower()):
            error_msg = f"{last_provider}: {error_msg}"
        return AIResponse(
            success=False,
            error=error_msg,
            provider=last_provider or AI_MANAGER_PROVIDER,
            model=model or "unknown",
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
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
                "max_requests_per_minute": (
                    weight.max_requests_per_minute if weight else 60
                ),
                "supported_model_types": [
                    mt.value for mt in provider.supported_model_types
                ],
                "available_models": [
                    {
                        "id": model.model_id,
                        "name": model.name,
                        "type": model.model_type.value,
                        "capabilities": model.capabilities,
                    }
                    for model in provider.available_models
                ],
            }
        return status

    def update_provider_config(
        self,
        provider_name: str,
        enabled: bool = None,
        weight: float = None,
        priority: ProviderPriority = None,
        max_requests_per_minute: int = None,
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
