from __future__ import annotations

from .base import AIServiceBase
from .episodes import EpisodeGenerationMixin
from .episodes_mock import EpisodeMockMixin
from .episodes_mock_script import EpisodeMockScriptMixin
from .images_generation import ImageGenerationMixin
from .images_ops import ImageOpsMixin
from .images_providers import ImageProviderMixin
from .images_storage import ImageStorageMixin
from .model_ui import ModelUiMixin
from .models import ModelRegistryMixin
from .scripts import ScriptGenerationMixin
from .scripts_ai_manager import ScriptManagerMixin
from .speech import SpeechGenerationMixin
from .story_outline import StoryOutlineMixin
from .storyboard_generation import StoryboardGenerationMixin
from .storyboard_plan import StoryboardPlanMixin
from .text_generation import TextGenerationMixin
from .video import VideoGenerationMixin


class AIService(
    AIServiceBase,
    ModelUiMixin,
    ModelRegistryMixin,
    TextGenerationMixin,
    StoryOutlineMixin,
    EpisodeGenerationMixin,
    EpisodeMockMixin,
    EpisodeMockScriptMixin,
    ScriptGenerationMixin,
    ScriptManagerMixin,
    StoryboardGenerationMixin,
    StoryboardPlanMixin,
    ImageGenerationMixin,
    ImageStorageMixin,
    ImageProviderMixin,
    ImageOpsMixin,
    VideoGenerationMixin,
    SpeechGenerationMixin,
):
    """AI服务接口 - 集成新的多提供商系统"""
