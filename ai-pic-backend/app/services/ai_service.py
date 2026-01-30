from app.services.ai.service import AIService
from app.services.ai.storyboard_utils import (
    build_storyboard_context as _build_storyboard_context,
)

# 创建全局AI服务实例
ai_service = AIService()

__all__ = ["AIService", "ai_service", "_build_storyboard_context"]
