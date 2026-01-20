from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.episode_agent import EpisodeLangGraphAgent
from app.services.script_agent import ScriptLangGraphAgent
from app.services.story_agent import StoryLangGraphAgent
from app.services.storyboard_reasoner import LANGGRAPH_AVAILABLE, StoryboardReActReasoner

from .manager import (
    AI_MANAGER_AVAILABLE,
    AIServiceConfig,
    AIServiceManager,
    ProviderConfig,
    ProviderPriority,
    ProviderWeight,
)


class AIServiceBase:
    """Shared AI service initialization and provider setup."""

    def __init__(self) -> None:
        self.logger = get_logger()
        self.logger.info("Initializing AI Service")

        # 保持向后兼容的配置
        self.base_url = settings.AI_SERVICE_URL
        self.api_key = settings.AI_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.stability_api_key = settings.STABILITY_API_KEY

        # 初始化多提供商AI服务管理器
        self.ai_manager = self._initialize_ai_manager()
        self.model_cache: dict[str, list[dict]] = {}
        self._warm_model_cache()
        self.storyboard_reasoner = (
            StoryboardReActReasoner(self) if LANGGRAPH_AVAILABLE else None
        )
        self.episode_agent = (
            EpisodeLangGraphAgent(self) if LANGGRAPH_AVAILABLE else None
        )
        self.script_agent = ScriptLangGraphAgent(self) if LANGGRAPH_AVAILABLE else None
        self.story_agent = StoryLangGraphAgent(self) if LANGGRAPH_AVAILABLE else None

    def _initialize_ai_manager(self) -> Optional[AIServiceManager]:
        """初始化AI服务管理器"""
        if not AI_MANAGER_AVAILABLE:
            self.logger.warning("AI服务管理器不可用，使用fallback模式")
            return None

        try:
            # 构建提供商配置
            providers = {}
            provider_weights = {}

            # OpenAI配置
            if self.openai_api_key:
                openai_base = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
                providers["openai"] = ProviderConfig(
                    name="openai",
                    api_key=self.openai_api_key,
                    base_url=openai_base,
                    timeout=120.0,
                )
                provider_weights["openai"] = ProviderWeight(
                    provider_name="openai",
                    weight=1.0,
                    priority=ProviderPriority.HIGH,
                    enabled=True,
                    max_requests_per_minute=100,
                )

            # 其他提供商配置（支持双密钥认证）
            # 可灵AI（快手）
            if settings.KELING_API_KEY and settings.KELING_SECRET_KEY:
                providers["keling"] = ProviderConfig(
                    name="keling",
                    api_key=settings.KELING_API_KEY,
                    api_secret=settings.KELING_SECRET_KEY,
                    base_url="https://api-beijing.klingai.com",
                    timeout=120.0,
                )
                provider_weights["keling"] = ProviderWeight(
                    provider_name="keling",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # 即梦AI
            if settings.JIMENG_API_KEY and settings.JIMENG_SECRET_KEY:
                providers["jimeng"] = ProviderConfig(
                    name="jimeng",
                    api_key=settings.JIMENG_API_KEY,
                    api_secret=settings.JIMENG_SECRET_KEY,
                    base_url="https://api.jimeng.ai/v1",
                    timeout=120.0,
                )
                provider_weights["jimeng"] = ProviderWeight(
                    provider_name="jimeng",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # DeepSeek（单密钥）
            if settings.DEEPSEEK_API_KEY:
                providers["deepseek"] = ProviderConfig(
                    name="deepseek",
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com/v1",
                    timeout=120.0,
                )
                provider_weights["deepseek"] = ProviderWeight(
                    provider_name="deepseek",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # MiniMax
            if settings.MINIMAX_API_KEY:
                providers["minimax"] = ProviderConfig(
                    name="minimax",
                    api_key=settings.MINIMAX_API_KEY,
                    group_id=settings.MINIMAX_GROUP_ID,
                    base_url="https://api.minimax.chat/v1",
                    timeout=120.0,
                )
                provider_weights["minimax"] = ProviderWeight(
                    provider_name="minimax",
                    weight=0.7,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # 火山引擎（Ark Seedream / 文本 & 图片）
            if settings.VOLCENGINE_API_KEY:
                providers["volcengine"] = ProviderConfig(
                    name="volcengine",
                    api_key=settings.VOLCENGINE_API_KEY,
                    api_secret=settings.VOLCENGINE_SECRET_KEY,
                    timeout=120.0,
                )
                provider_weights["volcengine"] = ProviderWeight(
                    provider_name="volcengine",
                    weight=0.7,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=50,
                )

            # Google Gemini / Vertex AI 文本模型
            if settings.GOOGLE_API_KEY:
                google_base = (
                    settings.GOOGLE_BASE_URL
                    or "https://generativelanguage.googleapis.com"
                )
                providers["google"] = ProviderConfig(
                    name="google",
                    api_key=settings.GOOGLE_API_KEY,
                    # 默认使用 Generative Language API，可通过 GOOGLE_BASE_URL 覆盖
                    base_url=google_base,
                    video_base_url=settings.GOOGLE_VIDEO_BASE_URL,
                    vertex_project_id=settings.GOOGLE_VERTEX_PROJECT_ID,
                    vertex_location=settings.GOOGLE_VERTEX_LOCATION,
                    vertex_access_token=settings.GOOGLE_VERTEX_ACCESS_TOKEN,
                    vertex_service_account_json=settings.GOOGLE_VERTEX_SERVICE_ACCOUNT_JSON,
                    vertex_service_account_path=settings.GOOGLE_VERTEX_SERVICE_ACCOUNT_PATH,
                    timeout=120.0,
                    default_model=settings.GOOGLE_DEFAULT_MODEL,
                )
                provider_weights["google"] = ProviderWeight(
                    provider_name="google",
                    weight=0.8,
                    priority=ProviderPriority.MEDIUM,
                    enabled=True,
                    max_requests_per_minute=60,
                )

            # 如果没有配置任何provider，返回None
            if not providers:
                print("警告: 没有配置任何AI服务提供商，将使用fallback模式")
                return None

            # 创建AI服务配置
            config = AIServiceConfig(
                providers=providers,
                provider_weights=provider_weights,
                enable_fallback=True,
                enable_load_balancing=True,
                default_timeout=120.0,
                max_retries=3,
            )

            return AIServiceManager(config)
        except Exception as exc:
            print(f"AI服务管理器初始化失败: {exc}")
            return None
