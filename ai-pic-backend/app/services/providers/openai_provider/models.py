"""
OpenAI provider model definitions.

Contains ModelInfo instances for GPT and OpenAI image models.
"""

from __future__ import annotations

from typing import List, Optional

from app.utils.model_utils import canonicalize_openai_image_model

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
        # Image models
        ModelInfo(
            model_id="gpt-image-2",
            name="GPT Image 2",
            description="OpenAI 最新的高质量图像生成与编辑模型",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg", "webp"],
            capabilities=[
                "text_to_image",
                "image_to_image",
                "reference_image",
                "high_resolution",
                "high_fidelity_input",
            ],
            metadata={
                "ui": {
                    "size_options": [
                        "1024x1024",
                        "1536x1024",
                        "1024x1536",
                        "2048x2048",
                        "2048x1152",
                        "3840x2160",
                        "2160x3840",
                        "auto",
                    ],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16"],
                    "supports_aspect_ratio": False,
                    "supports_reference_image": True,
                    "default_size": "1024x1024",
                }
            },
        ),
        ModelInfo(
            model_id="chatgpt-img-2",
            name="ChatGPT IMG 2",
            description=(
                "ChatGPT image template alias that routes to OpenAI GPT Image 2"
            ),
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg", "webp"],
            capabilities=[
                "text_to_image",
                "image_to_image",
                "reference_image",
                "high_resolution",
                "high_fidelity_input",
            ],
            metadata={
                "alias_for": "gpt-image-2",
                "routes_to": "gpt-image-2",
                "template_id": "chatgpt-img-2",
                "ui": {
                    "size_options": [
                        "1024x1024",
                        "1536x1024",
                        "1024x1536",
                        "2048x2048",
                        "2048x1152",
                        "3840x2160",
                        "2160x3840",
                        "auto",
                    ],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16"],
                    "supports_aspect_ratio": False,
                    "supports_reference_image": True,
                    "default_size": "1024x1024",
                },
            },
        ),
        ModelInfo(
            model_id="dall-e-3",
            name="DALL-E 3",
            description="上一代高质量图像生成模型",
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
    lid = (canonicalize_openai_image_model(model_id) or model_id).lower()
    if "dall-e" in lid or "image" in lid or "img-gen" in lid:
        return AIModelType.TEXT_TO_IMAGE
    return AIModelType.TEXT_GENERATION


def infer_capabilities(model_id: str) -> List[str]:
    """Infer model capabilities from model ID."""
    lid = (canonicalize_openai_image_model(model_id) or model_id).lower()
    if lid.startswith("gpt-image-2") or lid in {"img-gen-2", "image-gen-2"}:
        return ["text_to_image", "image_to_image", "reference_image"]
    if "dall-e" in lid or "image" in lid or "img-gen" in lid:
        return ["text_to_image"]
    caps = ["text_generation"]
    if "gpt" in lid or "o" in lid:
        caps.append("analysis")
    return caps
