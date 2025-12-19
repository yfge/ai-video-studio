"""
Keling provider model definitions.

Contains ModelInfo instances for video and image generation models.
"""

from __future__ import annotations

from typing import List

from ..base import AIModelType, ModelInfo


def get_available_models() -> List[ModelInfo]:
    """Return the list of available Keling models."""
    return [
        # V2 Series Models - Latest generation
        ModelInfo(
            model_id="kling-v2-6",
            name="可灵 V2.6",
            description="最新V2.6版本，支持声音控制，1080p高清输出",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "sound_control",
                "1080p",
                "30fps",
                "professional_mode",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["1080P", "720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "1080P",
                    "default_ratio": "16:9",
                    "supports_camera_control": True,
                    "supports_watermark": False,
                    "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                }
            },
        ),
        ModelInfo(
            model_id="kling-v2-5-turbo",
            name="可灵 V2.5 Turbo",
            description="V2.5快速版本，生成速度更快",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "fast_generation", "1080p", "30fps"],
            metadata={
                "ui": {
                    "resolution_options": ["1080P", "720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "1080P",
                    "default_ratio": "16:9",
                    "supports_camera_control": True,
                    "supports_watermark": False,
                    "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                }
            },
        ),
        ModelInfo(
            model_id="kling-v2-1-master",
            name="可灵 V2.1 Master",
            description="V2.1专业版，支持更多高级特性",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=[
                "image_to_video",
                "master_quality",
                "1080p",
                "30fps",
                "advanced_controls",
            ],
            metadata={
                "ui": {
                    "resolution_options": ["1080P", "720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "1080P",
                    "default_ratio": "16:9",
                    "supports_camera_control": True,
                    "supports_watermark": False,
                    "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                }
            },
        ),
        ModelInfo(
            model_id="kling-v2-1",
            name="可灵 V2.1",
            description="V2.1标准版，平衡质量与速度",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "1080p", "30fps"],
            metadata={
                "ui": {
                    "resolution_options": ["1080P", "720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "1080P",
                    "default_ratio": "16:9",
                    "supports_camera_control": True,
                    "supports_watermark": False,
                    "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                }
            },
        ),
        # V1 Series Models - Legacy but still supported
        ModelInfo(
            model_id="kling-v1-6",
            name="可灵 V1.6",
            description="V1.6版本，支持多图生成视频",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "multi_image", "720p", "24fps"],
            metadata={
                "ui": {
                    "resolution_options": ["720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "supports_camera_control": False,
                    "supports_watermark": False,
                }
            },
        ),
        ModelInfo(
            model_id="kling-v1-5",
            name="可灵 V1.5",
            description="V1.5版本，稳定可靠",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "720p", "24fps"],
            metadata={
                "ui": {
                    "resolution_options": ["720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "supports_camera_control": False,
                    "supports_watermark": False,
                }
            },
        ),
        ModelInfo(
            model_id="kling-v1",
            name="可灵 V1",
            description="V1基础版本",
            model_type=AIModelType.IMAGE_TO_VIDEO,
            supported_formats=["mp4"],
            capabilities=["image_to_video", "720p", "24fps"],
            metadata={
                "ui": {
                    "resolution_options": ["720P"],
                    "duration_options": [5, 10],
                    "supports_end_frame": True,
                    "supports_camera_fixed": False,
                    "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                    "default_resolution": "720P",
                    "default_ratio": "16:9",
                    "supports_camera_control": False,
                    "supports_watermark": False,
                }
            },
        ),
        # Image Generation Models
        ModelInfo(
            model_id="kling-image-v2",
            name="可灵图像生成 V2",
            description="V2图像生成模型，支持2K分辨率和人物参考",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpg"],
            capabilities=[
                "text_to_image",
                "image_to_image",
                "2k_resolution",
                "character_reference",
                "face_reference",
            ],
            metadata={
                "ui": {
                    "size_options": ["2k", "1k"],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "supports_aspect_ratio": True,
                    "supports_reference_image": True,
                }
            },
        ),
        ModelInfo(
            model_id="kling-image-v1",
            name="可灵图像生成 V1",
            description="V1图像生成模型，支持1K分辨率",
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png", "jpg"],
            capabilities=["text_to_image", "image_to_image", "1k_resolution"],
            metadata={
                "ui": {
                    "size_options": ["1k"],
                    "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "supports_aspect_ratio": True,
                    "supports_reference_image": True,
                }
            },
        ),
    ]
