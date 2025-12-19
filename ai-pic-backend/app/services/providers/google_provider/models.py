"""
Google model definitions and model-related utilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..base import AIModelType, ModelInfo


def get_available_models(default_model: str) -> List[ModelInfo]:
    """Return static fallback models for Google/Gemini."""
    return [
        ModelInfo(
            model_id=default_model,
            name="Gemini 3 Pro (preview)",
            description="Google Gemini 3 Pro 文本与推理模型",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=65535,
            capabilities=["text_generation", "analysis", "reasoning"],
        ),
        ModelInfo(
            model_id="gemini-1.5-pro-latest",
            name="Gemini 1.5 Pro (stable)",
            description="Gemini 1.5 Pro 通用推理模型（稳定版兜底）",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=1048576,
            capabilities=["text_generation", "analysis", "reasoning"],
        ),
        ModelInfo(
            model_id="gemini-1.5-flash-latest",
            name="Gemini 1.5 Flash (fast)",
            description="Gemini 1.5 Flash 高速通用模型（稳定版兜底）",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=2097152,
            capabilities=["text_generation", "analysis"],
        ),
        ModelInfo(
            model_id="gemini-1.0-pro",
            name="Gemini 1.0 Pro",
            description="Gemini 1.0 Pro 文本模型（兼容旧配置）",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=30720,
            capabilities=["text_generation", "analysis"],
        ),
        ModelInfo(
            model_id="gemini-2.0-flash-exp",
            name="Gemini 2.0 Flash (image exp)",
            description="Gemini Flash 试验性图片生成模型，支持文生图与图生图能力",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg"],
            capabilities=["text_to_image", "image_to_image"],
            metadata={
                "ui": {
                    "size_options": [],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "supports_aspect_ratio": True,
                    "supports_reference_image": True,
                }
            },
        ),
        ModelInfo(
            model_id="gemini-2.5-flash-image",
            name="Gemini 2.5 Flash Image",
            description="Gemini 2.5 Flash 快速图片生成模型，支持文/图生图",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg"],
            capabilities=["text_to_image", "image_to_image"],
            metadata={
                "ui": {
                    "size_options": [],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "supports_aspect_ratio": True,
                    "supports_reference_image": True,
                }
            },
        ),
        ModelInfo(
            model_id="gemini-3-pro-image-preview",
            name="Gemini 3 Pro Image Preview",
            description="Gemini 3 Pro 专业级图片生成模型（预览版），支持文/图生图",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpeg"],
            capabilities=["text_to_image", "image_to_image"],
            metadata={
                "ui": {
                    "size_options": [],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "supports_aspect_ratio": True,
                    "supports_reference_image": True,
                }
            },
        ),
    ]


def supports_type(model: ModelInfo, model_type: Optional[AIModelType]) -> bool:
    """Check if model supports the given type."""
    if not model_type:
        return True
    if model.model_type == model_type:
        return True
    caps = [c.lower() for c in (model.capabilities or [])]
    if model_type == AIModelType.IMAGE_TO_IMAGE and "image_to_image" in caps:
        return True
    return False


def fallback_models(
    available: List[ModelInfo], model_type: Optional[AIModelType]
) -> List[ModelInfo]:
    """Filter available models by type."""
    if model_type:
        return [m for m in available if supports_type(m, model_type)]
    return available


def normalize_model_id(raw: Optional[str]) -> Optional[str]:
    """Extract model ID from potential path format."""
    if not raw:
        return None
    return raw.split("/")[-1]


def supported_methods(item: Dict[str, Any]) -> List[str]:
    """Extract supported generation methods from model item."""
    methods = (
        item.get("supportedGenerationMethods")
        or item.get("supported_generation_methods")
        or []
    )
    return [m.lower() for m in methods if isinstance(m, str)]


def infer_model_type(item: Dict[str, Any]) -> AIModelType:
    """Infer model type from supported methods."""
    methods = supported_methods(item)
    if "generateimage" in methods:
        return AIModelType.TEXT_TO_IMAGE
    return AIModelType.TEXT_GENERATION


def infer_capabilities(item: Dict[str, Any]) -> List[str]:
    """Infer capabilities from supported methods."""
    methods = supported_methods(item)
    caps: List[str] = []
    if any(m in methods for m in ["generatecontent", "generatetext"]):
        caps.append("text_generation")
    if "generateimage" in methods:
        caps.append("text_to_image")
        caps.append("image_to_image")
    if not caps:
        caps.append("text_generation")
    return caps


def from_payload(
    server_models: List[Dict[str, Any]],
    model_type: Optional[AIModelType],
    supported_model_types: List[AIModelType],
) -> List[ModelInfo]:
    """Convert server model list to ModelInfo list."""
    models: List[ModelInfo] = []
    for item in server_models:
        if not isinstance(item, dict):
            continue
        mid = normalize_model_id(item.get("name") or item.get("id"))
        if not mid:
            continue
        mtype = infer_model_type(item)
        if mtype not in supported_model_types:
            continue
        caps = infer_capabilities(item)
        if model_type and not (
            mtype == model_type
            or (model_type == AIModelType.IMAGE_TO_IMAGE and "image_to_image" in caps)
        ):
            continue
        models.append(
            ModelInfo(
                model_id=mid,
                name=item.get("displayName") or item.get("title") or mid,
                description=item.get("description") or f"Google model {mid}",
                model_type=mtype,
                capabilities=caps,
            )
        )
    return models


def dedupe(models: List[ModelInfo]) -> List[ModelInfo]:
    """Remove duplicate model_ids while preserving order."""
    seen = set()
    unique: List[ModelInfo] = []
    for m in models:
        if m.model_id in seen:
            continue
        seen.add(m.model_id)
        unique.append(m)
    return unique
