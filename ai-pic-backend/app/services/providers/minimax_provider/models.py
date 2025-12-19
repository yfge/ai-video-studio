"""
MiniMax model definitions.

Contains all available model configurations for text, TTS, and video generation.
"""

from __future__ import annotations

from typing import List

from ..base import AIModelType, ModelInfo


def get_available_models() -> List[ModelInfo]:
    """Return all available MiniMax models."""
    return [
        # Text generation models
        ModelInfo(
            model_id="abab6.5s-chat",
            name="MiniMax Chat 6.5s",
            description="快速响应的对话模型",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=8192,
            capabilities=["chat", "fast_response", "chinese_optimized"],
        ),
        ModelInfo(
            model_id="abab6.5-chat",
            name="MiniMax Chat 6.5",
            description="平衡性能和质量的对话模型",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=16384,
            capabilities=["chat", "balanced", "multi_turn"],
        ),
        ModelInfo(
            model_id="abab6.5g-chat",
            name="MiniMax Chat 6.5g",
            description="高质量文本生成模型",
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=32768,
            capabilities=["chat", "high_quality", "long_context"],
        ),
        # TTS models
        ModelInfo(
            model_id="speech-2.6-hd",
            name="MiniMax Speech 2.6 HD",
            description="高质量中文英文双语音色，支持情绪控制",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav", "pcm", "flac"],
            capabilities=[
                "text_to_speech",
                "multiple_voices",
                "emotion_control",
                "subtitle",
            ],
        ),
        ModelInfo(
            model_id="speech-2.6-turbo",
            name="MiniMax Speech 2.6 Turbo",
            description="高速情感语音合成，支持流式输出",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav", "pcm", "flac"],
            capabilities=[
                "text_to_speech",
                "multiple_voices",
                "emotion_control",
                "streaming",
            ],
        ),
        ModelInfo(
            model_id="speech-02-hd",
            name="MiniMax Speech 02 HD",
            description="高清音质语音合成",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav", "pcm", "flac"],
            capabilities=["text_to_speech", "multiple_voices"],
        ),
        ModelInfo(
            model_id="speech-02-turbo",
            name="MiniMax Speech 02 Turbo",
            description="快速语音合成",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav", "pcm", "flac"],
            capabilities=["text_to_speech", "multiple_voices"],
        ),
        ModelInfo(
            model_id="speech-01-hd",
            name="MiniMax Speech 01 HD",
            description="高清音质语音合成（经典版）",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav", "pcm", "flac"],
            capabilities=["text_to_speech", "multiple_voices"],
        ),
        ModelInfo(
            model_id="speech-01-turbo",
            name="MiniMax Speech 01 Turbo",
            description="快速语音合成（经典版）",
            model_type=AIModelType.TEXT_TO_SPEECH,
            supported_formats=["mp3", "wav", "pcm", "flac"],
            capabilities=["text_to_speech", "multiple_voices"],
        ),
        # Video generation models
        ModelInfo(
            model_id="MiniMax-Hailuo-2.3",
            name="MiniMax Hailuo 2.3",
            description="海螺视频生成2.3版本，支持768P/1080P，6s/10s时长",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "768p",
                "1080p",
                "6s",
                "10s",
                "camera_control",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["768P", "1080P"],
                    "duration_options": [6, 10],
                    "supports_end_frame": False,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "768P",
                    "default_ratio": "16:9",
                    "supports_camera_control": False,
                    "supports_watermark": True,
                }
            },
        ),
        ModelInfo(
            model_id="MiniMax-Hailuo-2.3-Fast",
            name="MiniMax Hailuo 2.3 Fast",
            description="海螺视频生成2.3快速版，生成速度更快",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "768p",
                "1080p",
                "6s",
                "10s",
                "fast_generation",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["768P", "1080P"],
                    "duration_options": [6, 10],
                    "supports_end_frame": False,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "768P",
                    "default_ratio": "16:9",
                    "supports_camera_control": False,
                    "supports_watermark": True,
                }
            },
        ),
        ModelInfo(
            model_id="MiniMax-Hailuo-02",
            name="MiniMax Hailuo 0.2",
            description="海螺视频生成0.2版本，支持512P/768P/1080P多种分辨率",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "512p",
                "768p",
                "1080p",
                "6s",
                "10s",
                "first_last_frame",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["512P", "768P", "1080P"],
                    "duration_options": [6, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "768P",
                    "default_ratio": "16:9",
                    "supports_camera_control": False,
                    "supports_watermark": True,
                }
            },
        ),
        ModelInfo(
            model_id="I2V-01-Director",
            name="MiniMax I2V-01-Director",
            description="专业级图生视频模型，支持精细控制",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "720p",
                "director_mode",
                "camera_control",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["720P"],
                    "duration_options": [6, 10],
                    "supports_end_frame": False,
                    "supports_camera_fixed": True,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                }
            },
        ),
        ModelInfo(
            model_id="I2V-01-live",
            name="MiniMax I2V-01-Live",
            description="实时图生视频模型，生成速度快",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "720p", "fast_generation"],
            metadata={
                "ui": {
                    "resolution_options": ["720P"],
                    "duration_options": [6, 10],
                    "supports_end_frame": False,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                }
            },
        ),
        ModelInfo(
            model_id="I2V-01",
            name="MiniMax I2V-01",
            description="标准图生视频模型",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "720p"],
            metadata={
                "ui": {
                    "resolution_options": ["720P"],
                    "duration_options": [6, 10],
                    "supports_end_frame": False,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                }
            },
        ),
    ]
