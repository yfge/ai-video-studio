"""
AI工作节点提示词管理模块

本模块提供统一的提示词管理功能，支持各种AI任务的提示词模板。
包括：
- 虚拟IP生成
- 人物小传生成
- 故事大纲生成
- 剧集生成
- 剧本生成
- 图像生成
等等
"""

from .manager import PromptManager
from .templates import (
    DEFAULT_GENERATION_PARAMS,
    NEGATIVE_PROMPTS,
    QUALITY_ENHANCERS,
    TEMPLATE_EXAMPLES,
    DialogueStyle,
    ImageCategory,
    ImageStyle,
    Pacing,
    PlotComplexity,
    PromptCategory,
    PromptTemplate,
    ScriptFormat,
    get_category_by_template,
    get_template_by_category,
)

__all__ = [
    "DEFAULT_GENERATION_PARAMS",
    "NEGATIVE_PROMPTS",
    "QUALITY_ENHANCERS",
    "TEMPLATE_EXAMPLES",
    "DialogueStyle",
    "ImageCategory",
    "ImageStyle",
    "Pacing",
    "PlotComplexity",
    "PromptCategory",
    "PromptManager",
    "PromptTemplate",
    "ScriptFormat",
    "get_category_by_template",
    "get_template_by_category",
]
