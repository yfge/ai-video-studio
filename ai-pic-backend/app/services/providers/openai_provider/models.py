"""
OpenAI provider model definitions.

Contains ModelInfo instances for GPT and DALL-E models.
"""

from __future__ import annotations

from typing import List, Optional

from ..base import AIModelType, ModelInfo


def get_available_models() -> List[ModelInfo]:
    """Return the list of available OpenAI models."""
    return [
        # GPT models
        ModelInfo(
            model_id="gpt-4o",
            name="GPT-4o",
            description="最新的GPT-4优化版本，支持多模态",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=128000,
            supported_formats=["text", "image"],
            capabilities=[
                "text_generation",
                "image_understanding",
                "code_generation",
            ],
        ),
        ModelInfo(
            model_id="gpt-4-turbo",
            name="GPT-4 Turbo",
            description="GPT-4的增强版本，更快更便宜",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=128000,
            capabilities=["text_generation", "code_generation", "analysis"],
        ),
        ModelInfo(
            model_id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            description="快速且经济的文本生成模型",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=16385,
            capabilities=["text_generation", "conversation", "summarization"],
        ),
        # DALL-E models
        ModelInfo(
            model_id="dall-e-3",
            name="DALL-E 3",
            description="最新的图像生成模型，高质量输出",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg"],
            capabilities=["text_to_image", "high_resolution", "detailed"],
            metadata={
                "ui": {
                    "size_options": ["1024x1024", "1024x1792", "1792x1024"],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16"],
                    "supports_reference_image": False,
                }
            },
        ),
        ModelInfo(
            model_id="dall-e-2",
            name="DALL-E 2",
            description="经典的图像生成模型，快速生成",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg"],
            capabilities=[
                "text_to_image",
                "variations",
                "inpainting",
                "image_to_image",
            ],
            metadata={
                "ui": {
                    "size_options": ["256x256", "512x512", "1024x1024"],
                    "aspect_ratio_options": ["1:1"],
                    "supports_reference_image": True,
                }
            },
        ),
    ]


def fallback_models(
    models: List[ModelInfo], model_type: Optional[AIModelType]
) -> List[ModelInfo]:
    """Filter models by type for fallback."""
    if model_type:
        return [m for m in models if m.model_type == model_type]
    return models


def infer_model_type(model_id: str) -> AIModelType:
    """Infer model type from model ID."""
    lid = model_id.lower()
    if "dall-e" in lid or "image" in lid:
        return AIModelType.TEXT_TO_IMAGE
    return AIModelType.TEXT_GENERATION


def infer_capabilities(model_id: str) -> List[str]:
    """Infer model capabilities from model ID."""
    lid = model_id.lower()
    if "dall-e" in lid or "image" in lid:
        return ["text_to_image"]
    caps = ["text_generation"]
    if "gpt" in lid or "o" in lid:
        caps.append("analysis")
    return caps
