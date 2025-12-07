"""
AI服务提供商基类

定义了所有AI服务提供商的统一接口和规范
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
from datetime import datetime

class AIModelType(Enum):
    """AI模型类型枚举"""
    TEXT_GENERATION = "text_generation"         # 文本生成
    TEXT_TO_IMAGE = "text_to_image"             # 文生图
    IMAGE_TO_IMAGE = "image_to_image"           # 图生图
    IMAGE_TO_VIDEO = "image_to_video"           # 图生视频
    TEXT_TO_VIDEO = "text_to_video"             # 文生视频
    TEXT_TO_SPEECH = "text_to_speech"           # 文本转语音
    SPEECH_TO_TEXT = "speech_to_text"           # 语音转文本
    IMAGE_UNDERSTANDING = "image_understanding" # 图像理解
    VIDEO_UNDERSTANDING = "video_understanding" # 视频理解

class AITaskType(Enum):
    """AI任务类型枚举"""
    STORY_GENERATION = "story_generation"       # 故事生成
    CHARACTER_CREATION = "character_creation"   # 角色创建
    EPISODE_PLANNING = "episode_planning"       # 剧集规划
    SCRIPT_WRITING = "script_writing"           # 剧本写作
    PORTRAIT_GENERATION = "portrait_generation" # 肖像生成
    SCENE_GENERATION = "scene_generation"       # 场景生成
    VIDEO_GENERATION = "video_generation"       # 视频生成
    VOICE_GENERATION = "voice_generation"       # 语音生成

class AIRequest(BaseModel):
    """AI请求基类"""
    task_type: AITaskType
    model_type: AIModelType
    prompt: str
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    model_config = {
        "protected_namespaces": (),
    }

class AIResponse(BaseModel):
    """AI响应基类"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    provider: str
    model: str
    task_type: AITaskType
    model_type: AIModelType
    usage: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

    model_config = {
        "protected_namespaces": (),
    }

class ModelInfo(BaseModel):
    """模型信息"""
    model_id: str
    name: str
    description: str
    model_type: AIModelType
    max_tokens: Optional[int] = None
    supported_formats: List[str] = []
    pricing: Dict[str, Any] = {}
    capabilities: List[str] = []

    model_config = {
        "protected_namespaces": (),
    }

class ProviderConfig(BaseModel):
    """服务提供商配置"""
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    rate_limit: Dict[str, int] = {}
    enabled: bool = True
    default_model: Optional[str] = None

    model_config = {
        "protected_namespaces": (),
        "extra": "ignore",
    }

class BaseProvider(ABC):
    """AI服务提供商基类"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self._client = None
    
    @property
    @abstractmethod
    def supported_model_types(self) -> List[AIModelType]:
        """支持的模型类型列表"""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[ModelInfo]:
        """可用的模型列表"""
        pass
    
    @abstractmethod
    async def _initialize_client(self):
        """初始化API客户端"""
        pass
    
    async def get_client(self):
        """获取API客户端"""
        if self._client is None:
            await self._initialize_client()
        return self._client
    
    @abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """生成文本"""
        pass
    
    @abstractmethod  
    async def generate_image(
        self, 
        prompt: str, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """文生图"""
        pass
    
    async def image_to_image(
        self, 
        image_url: str, 
        prompt: str = None,
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """图生图（可选实现）"""
        return AIResponse(
            success=False,
            error="图生图功能未实现",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE
        )
    
    async def generate_video(
        self, 
        prompt: str = None,
        image_url: str = None, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """视频生成（可选实现）"""
        return AIResponse(
            success=False,
            error="视频生成功能未实现",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.TEXT_TO_VIDEO if prompt else AIModelType.IMAGE_TO_VIDEO
        )
    
    async def text_to_speech(
        self, 
        text: str, 
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """文本转语音（可选实现）"""
        return AIResponse(
            success=False,
            error="文本转语音功能未实现",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH
        )
    
    async def understand_image(
        self, 
        image_url: str, 
        question: str = None,
        model: str = None,
        **kwargs
    ) -> AIResponse:
        """图像理解（可选实现）"""
        return AIResponse(
            success=False,
            error="图像理解功能未实现",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.CHARACTER_CREATION,
            model_type=AIModelType.IMAGE_UNDERSTANDING
        )
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        for model in self.available_models:
            if model.model_id == model_id:
                return model
        return None

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """
        默认的远端模型拉取实现。

        大多数提供商没有单独的「列出模型」API，默认直接返回静态 available_models，
        调用方可以根据 model_type 进行过滤。
        """
        models = self.available_models
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        return models
    
    def supports_model_type(self, model_type: AIModelType) -> bool:
        """检查是否支持指定的模型类型"""
        return model_type in self.supported_model_types
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self.get_client()
            return client is not None
        except Exception:
            return False
    
    def estimate_cost(self, request: AIRequest) -> float:
        """估算请求成本（可选实现）"""
        return 0.0
    
    def format_error(self, error: Exception) -> str:
        """格式化错误信息"""
        return f"{self.name} 错误: {str(error)}"
