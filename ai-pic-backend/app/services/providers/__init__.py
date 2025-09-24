"""
AI服务提供商模块

支持多种第三方AI服务提供商：
- OpenAI (文本、图像)
- 可灵 (视频生成)
- 即梦 (图像生成)
- MiniMax (文本、语音)
- DeepSeek (文本)
- 火山引擎 (文本、图像、视频)
"""

from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig
from .openai_provider import OpenAIProvider
from .keling_provider import KelingProvider
from .jimeng_provider import JimengProvider
from .minimax_provider import MinimaxProvider
from .deepseek_provider import DeepSeekProvider
from .volcengine_provider import VolcengineProvider

__all__ = [
    'BaseProvider',
    'AIResponse',
    'AIModelType', 
    'AITaskType',
    'ModelInfo',
    'ProviderConfig',
    'OpenAIProvider',
    'KelingProvider',
    'JimengProvider',
    'MinimaxProvider',
    'DeepSeekProvider',
    'VolcengineProvider'
]