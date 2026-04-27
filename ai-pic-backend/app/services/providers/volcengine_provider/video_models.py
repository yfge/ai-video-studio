"""Volcengine video model definitions."""

from __future__ import annotations

from typing import Any, List

from ..base import AIModelType, ModelInfo

SEEDANCE_20_MODEL = "doubao-seedance-2-0-260128"
SEEDANCE_20_FAST_MODEL = "doubao-seedance-2-0-fast-260128"
SEEDANCE_15_PRO_MODEL = "doubao-seedance-1-5-pro-251215"
SEEDANCE_10_PRO_MODEL = "doubao-seedance-1-0-pro-250528"
SEEDANCE_10_FAST_MODEL = "doubao-seedance-1-0-pro-fast-251015"
SEEDANCE_10_LITE_T2V_MODEL = "doubao-seedance-1-0-lite-t2v-250428"
SEEDANCE_10_LITE_I2V_MODEL = "doubao-seedance-1-0-lite-i2v-250428"


def _ui(
    *,
    durations: list[int],
    resolutions: list[str] | None = None,
    supports_end_frame: bool = True,
    supports_refs: bool = False,
    supports_audio: bool = False,
    supports_camera_fixed: bool = True,
    default_ratio: str = "16:9",
) -> dict[str, Any]:
    return {
        "ui": {
            "resolution_options": resolutions or ["480P", "720P", "1080P"],
            "duration_options": durations,
            "supports_end_frame": supports_end_frame,
            "supports_reference_images": supports_refs,
            "supports_reference_video": supports_refs,
            "supports_reference_audio": supports_refs,
            "max_reference_images": 9 if supports_refs else 0,
            "max_reference_videos": 3 if supports_refs else 0,
            "max_reference_audios": 3 if supports_refs else 0,
            "supports_generate_audio": supports_audio,
            "supports_camera_fixed": supports_camera_fixed,
            "supports_camera_control": False,
            "ratio_options": [
                "adaptive",
                "16:9",
                "9:16",
                "1:1",
                "4:3",
                "3:4",
                "21:9",
            ],
            "default_resolution": "720P",
            "default_ratio": default_ratio,
            "default_watermark": False,
            "supports_watermark": True,
        }
    }


def _video_model(
    model_id: str,
    name: str,
    description: str,
    model_type: AIModelType,
    capabilities: list[str],
    metadata: dict[str, Any],
) -> ModelInfo:
    return ModelInfo(
        model_id=model_id,
        name=name,
        description=description,
        model_type=model_type,
        supported_formats=["mp4"],
        capabilities=capabilities,
        metadata=metadata,
    )


def _seedance20_caps() -> list[str]:
    return [
        "text_to_video",
        "image_to_video",
        "image_to_video_start_frame",
        "image_to_video_start_end_frame",
        "reference_images",
        "reference_video",
        "reference_audio",
        "generate_audio",
        "4s",
        "15s",
    ]


def get_video_models() -> List[ModelInfo]:
    """Return static fallback models for Volcengine video generation."""
    seedance20_ui = _ui(
        durations=list(range(4, 16)),
        supports_refs=True,
        supports_audio=True,
        supports_camera_fixed=False,
        default_ratio="adaptive",
    )
    seedance20_fast_ui = _ui(
        durations=list(range(4, 16)),
        resolutions=["480P", "720P"],
        supports_refs=True,
        supports_audio=True,
        supports_camera_fixed=False,
        default_ratio="adaptive",
    )
    seedance15_ui = _ui(
        durations=list(range(4, 13)),
        supports_audio=True,
        supports_camera_fixed=True,
        default_ratio="adaptive",
    )
    seedance10_ui = _ui(durations=list(range(2, 13)))
    return [
        _video_model(
            "seedance-2.0-i2v",
            "Seedance 2.0 图生视频（推荐）",
            "Seedance 2.0 图生视频/多模态参考别名，提交时映射到方舟标准模型",
            AIModelType.IMAGE_TO_VIDEO,
            [c for c in _seedance20_caps() if c != "text_to_video"],
            seedance20_ui,
        ),
        _video_model(
            "seedance-2.0-fast-i2v",
            "Seedance 2.0 Fast 图生视频",
            "Seedance 2.0 Fast 图生视频/多模态参考别名",
            AIModelType.IMAGE_TO_VIDEO,
            [c for c in _seedance20_caps() if c != "text_to_video"],
            seedance20_fast_ui,
        ),
        _video_model(
            SEEDANCE_20_MODEL,
            "豆包 Seedance 2.0（推荐）",
            "支持文生视频、图生视频、首尾帧、多模态参考和有声视频",
            AIModelType.TEXT_TO_VIDEO,
            _seedance20_caps(),
            seedance20_ui,
        ),
        _video_model(
            SEEDANCE_20_FAST_MODEL,
            "豆包 Seedance 2.0 Fast",
            "支持 Seedance 2.0 能力的快速模型，最高 720p",
            AIModelType.TEXT_TO_VIDEO,
            _seedance20_caps(),
            seedance20_fast_ui,
        ),
        _video_model(
            SEEDANCE_15_PRO_MODEL,
            "豆包 Seedance 1.5 Pro",
            "支持文生视频、首帧/首尾帧图生视频和有声视频",
            AIModelType.TEXT_TO_VIDEO,
            [
                "text_to_video",
                "image_to_video",
                "image_to_video_start_end_frame",
                "generate_audio",
            ],
            seedance15_ui,
        ),
        _video_model(
            SEEDANCE_10_PRO_MODEL,
            "豆包 Seedance 1.0 Pro",
            "支持文生视频、图生视频（首帧/首尾帧）",
            AIModelType.TEXT_TO_VIDEO,
            [
                "text_to_video",
                "image_to_video",
                "image_to_video_start_end_frame",
            ],
            seedance10_ui,
        ),
        _video_model(
            SEEDANCE_10_FAST_MODEL,
            "豆包 Seedance 1.0 Pro Fast",
            "支持文生视频、图生视频（首帧），更快",
            AIModelType.TEXT_TO_VIDEO,
            ["text_to_video", "image_to_video", "image_to_video_start_frame"],
            _ui(durations=list(range(2, 13)), supports_end_frame=False),
        ),
        _video_model(
            SEEDANCE_10_LITE_T2V_MODEL,
            "豆包 Seedance 1.0 Lite（文生视频）",
            "Seedance 1.0 Lite 文生视频",
            AIModelType.TEXT_TO_VIDEO,
            ["text_to_video"],
            seedance10_ui,
        ),
        _video_model(
            SEEDANCE_10_LITE_I2V_MODEL,
            "豆包 Seedance 1.0 Lite（图生视频）",
            "支持参考图、首帧和首尾帧图生视频",
            AIModelType.TEXT_TO_VIDEO,
            [
                "image_to_video",
                "reference_images",
                "image_to_video_start_end_frame",
            ],
            seedance10_ui,
        ),
    ]
