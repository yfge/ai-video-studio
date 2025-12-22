"""
Volcengine provider model definitions.

Contains ModelInfo instances and model-related helper functions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..base import AIModelType, ModelInfo


def get_available_models() -> List[ModelInfo]:
    """Return the list of available Volcengine models."""
    return [
        # Text generation models
        ModelInfo(
            model_id="doubao-lite-4k",
            name="豆包轻量版",
            description="轻量级文本生成模型，快速响应",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=4096,
            capabilities=["text_generation", "conversation", "fast_response"],
        ),
        ModelInfo(
            model_id="doubao-pro-4k",
            name="豆包专业版",
            description="专业级文本生成模型，高质量输出",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=4096,
            capabilities=[
                "text_generation",
                "analysis",
                "reasoning",
                "high_quality",
            ],
        ),
        ModelInfo(
            model_id="doubao-pro-32k",
            name="豆包专业版长文本",
            description="支持长文本处理的专业版模型",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=32768,
            capabilities=["text_generation", "long_context", "document_analysis"],
        ),
        ModelInfo(
            model_id="doubao-seedream-4-5-251128",
            name="Seedream 4.5",
            description="方舟大模型服务平台的图片生成模型（Seedream 4.5）",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpg"],
            capabilities=["text_to_image", "image_to_image", "high_resolution"],
            metadata={
                "ui": {
                    "size_options": ["2K"],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "supports_reference_image": True,
                }
            },
        ),
        # Image generation models
        ModelInfo(
            model_id="volcengine-visual-v1",
            name="火山视觉生成V1",
            description="高质量图像生成模型",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpg"],
            capabilities=["text_to_image", "style_control", "high_resolution"],
        ),
        ModelInfo(
            model_id="volcengine-visual-pro",
            name="火山视觉生成Pro",
            description="专业版图像生成，支持更多风格",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpg"],
            capabilities=["text_to_image", "multiple_styles", "ultra_quality"],
        ),
        # Seedream image-to-video (internally uses Ark Video Generation / Seedance)
        ModelInfo(
            model_id="seedream-i2v-pro",
            name="Seedream 图生视频 Pro（推荐）",
            description="Seedream 图生视频，支持首帧/首尾帧",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "image_to_video_start_frame",
                "image_to_video_start_end_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["480P", "720P", "1080P"],
                    "duration_options": [2, 12],
                    "supports_end_frame": True,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "default_watermark": False,
                    "supports_watermark": True,
                    "supports_camera_control": False,
                }
            },
        ),
        ModelInfo(
            model_id="seedream-i2v-fast",
            name="Seedream 图生视频 Fast",
            description="Seedream 图生视频（更快），仅支持首帧",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "image_to_video_start_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["480P", "720P", "1080P"],
                    "duration_options": [2, 12],
                    "supports_end_frame": False,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "default_watermark": False,
                    "supports_watermark": True,
                    "supports_camera_control": False,
                }
            },
        ),
        ModelInfo(
            model_id="seedream-i2v-lite",
            name="Seedream 图生视频 Lite",
            description="Seedream 图生视频（Lite），支持首帧/首尾帧",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "image_to_video_start_frame",
                "image_to_video_start_end_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["480P", "720P", "1080P"],
                    "duration_options": [2, 12],
                    "supports_end_frame": True,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "default_watermark": False,
                    "supports_watermark": True,
                    "supports_camera_control": False,
                }
            },
        ),
        # Video generation models (Volcengine Ark / Seedance)
        ModelInfo(
            model_id="doubao-seedance-1-0-pro-250528",
            name="豆包 Seedance 1.0 Pro（推荐）",
            description="支持文生视频、图生视频（首帧/首尾帧）",
            model_type=AIModelType.TEXT_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "text_to_video",
                "image_to_video",
                "image_to_video_start_frame",
                "image_to_video_start_end_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["480P", "720P", "1080P"],
                    "duration_options": [2, 12],
                    "supports_end_frame": True,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "default_watermark": False,
                    "supports_watermark": True,
                    "supports_camera_control": False,
                }
            },
        ),
        ModelInfo(
            model_id="doubao-seedance-1-0-pro-fast-251015",
            name="豆包 Seedance 1.0 Pro Fast",
            description="支持文生视频、图生视频（首帧），更快",
            model_type=AIModelType.TEXT_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "text_to_video",
                "image_to_video",
                "image_to_video_start_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["480P", "720P", "1080P"],
                    "duration_options": [2, 12],
                    "supports_end_frame": False,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "default_watermark": False,
                    "supports_watermark": True,
                    "supports_camera_control": False,
                }
            },
        ),
        ModelInfo(
            model_id="doubao-seedance-1-0-lite-t2v-250428",
            name="豆包 Seedance 1.0 Lite（文生视频）",
            description="仅支持文生视频",
            model_type=AIModelType.TEXT_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["text_to_video"],
        ),
        ModelInfo(
            model_id="doubao-seedance-1-0-lite-i2v-250428",
            name="豆包 Seedance 1.0 Lite（图生视频）",
            description="支持图生视频（参考图/首帧/首尾帧）",
            model_type=AIModelType.TEXT_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "image_to_video_reference",
                "image_to_video_start_frame",
                "image_to_video_start_end_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["480P", "720P", "1080P"],
                    "duration_options": [2, 12],
                    "supports_end_frame": True,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "default_watermark": False,
                    "supports_watermark": True,
                    "supports_camera_control": False,
                }
            },
        ),
        # TTS models
        ModelInfo(
            model_id="volcengine-tts-v1",
            name="火山语音合成",
            description="高质量语音合成服务",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav"],
            capabilities=["text_to_speech", "emotion_control", "voice_cloning"],
        ),
    ]


def fallback_models(
    models: List[ModelInfo], model_type: Optional[AIModelType]
) -> List[ModelInfo]:
    """Filter models by type for fallback."""
    if model_type:
        return [m for m in models if m.model_type == model_type]
    return models


def infer_model_type(model_id: str, item: Dict[str, Any]) -> AIModelType:
    """Infer model type from model ID and capability fields."""
    tokens: List[str] = []
    for key in ["task_type", "type", "category"]:
        val = item.get(key)
        if isinstance(val, str):
            tokens.append(val.lower())
    abilities = item.get("abilities") or item.get("ability") or []
    if isinstance(abilities, str):
        tokens.append(abilities.lower())
    elif isinstance(abilities, list):
        tokens.extend([str(a).lower() for a in abilities])
    tokens.append(model_id.lower())

    def _has_any(keywords: List[str]) -> bool:
        return any(keyword in token for token in tokens for keyword in keywords)

    if _has_any(["image", "visual", "seedream", "picture", "painting"]):
        return AIModelType.TEXT_TO_IMAGE
    if _has_any(["video", "vid", "movie"]):
        return AIModelType.TEXT_TO_VIDEO
    if _has_any(["tts", "speech", "voice", "audio"]):
        return AIModelType.TEXT_TO_SPEECH
    if _has_any(["stt", "asr"]):
        return AIModelType.SPEECH_TO_TEXT
    return AIModelType.TEXT_GENERATION


def infer_capabilities(
    model_type: AIModelType,
    item: Dict[str, Any],
) -> List[str]:
    """Infer model capabilities from type and item metadata."""
    abilities = item.get("abilities") or item.get("ability") or []
    ability_tokens: List[str] = []
    if isinstance(abilities, str):
        ability_tokens = [abilities.lower()]
    elif isinstance(abilities, list):
        ability_tokens = [str(a).lower() for a in abilities]

    caps: List[str] = []
    if model_type == AIModelType.TEXT_TO_IMAGE:
        caps.append("text_to_image")
    elif model_type == AIModelType.TEXT_TO_VIDEO:
        caps.append("text_to_video")
    elif model_type == AIModelType.TEXT_TO_SPEECH:
        caps.append("text_to_speech")
    elif model_type == AIModelType.SPEECH_TO_TEXT:
        caps.append("speech_to_text")
    else:
        caps.append("text_generation")

    for token in ability_tokens:
        if "code" in token:
            caps.append("code_generation")
        if "chat" in token:
            caps.append("conversation")
        if "embed" in token:
            caps.append("embedding")
    # Deduplicate while preserving order
    return list(dict.fromkeys(caps))
