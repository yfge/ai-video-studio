"""
MiniMax text-to-speech module.

Contains TTS and voice listing functionality.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.services.minimax_client import MinimaxAPIError, MinimaxClient
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG

from ..base import AIModelType, AIResponse, AITaskType


def _to_int(value: Any) -> Optional[int]:
    """Convert value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def text_to_speech(
    client: MinimaxClient,
    provider_name: str,
    text: str,
    model: str = "speech-2.6-hd",
    voice_id: str = "Chinese (Mandarin)_Lyrical_Voice",
    speed: float = 1.0,
    pitch: float = 0.0,
    emotion: Optional[str] = None,
    format: str = "mp3",
    output_format: str = "url",
    stream: bool = False,
    format_error: Callable = str,
    **kwargs,
) -> AIResponse:
    """MiniMax text-to-speech."""
    try:
        # ai_service_manager passes voice_type, but MiniMax T2A API doesn't accept it
        kwargs.pop("voice_type", None)

        voice_setting = {
            "voice_id": voice_id,
            "speed": speed,
            # MiniMax expects pitch as int64, avoid float causing invalid params
            "pitch": _to_int(pitch),
            "emotion": emotion,
            "vol": kwargs.pop("vol", 1.0),
        }
        audio_setting = {
            "format": format,
            "sample_rate": _to_int(kwargs.pop("sample_rate", None)),
            "bitrate": _to_int(kwargs.pop("bitrate", None)),
            "channel": _to_int(kwargs.pop("channel", None)),
        }
        # Clean None fields to avoid sending redundant parameters
        voice_setting = {k: v for k, v in voice_setting.items() if v is not None}
        audio_setting = {k: v for k, v in audio_setting.items() if v is not None}

        request_data: Dict[str, Any] = {
            "model": model,
            "text": text,
            "stream": stream,
            "voice_setting": voice_setting,
            "audio_setting": audio_setting,
            "output_format": output_format,
            **kwargs,
        }

        data = await client.post_json("/t2a_v2", request_data)
        audio_payload = data.get("data") or {}
        audio_value = audio_payload.get("audio")

        return AIResponse(
            success=True,
            data={
                "audio_url": audio_value if output_format == "url" else None,
                "audio_hex": audio_value if output_format != "url" else None,
                "subtitle_file": audio_payload.get("subtitle_file"),
                "trace_id": data.get("trace_id"),
                "extra_info": data.get("extra_info"),
            },
            provider=provider_name,
            model=model,
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
            metadata={
                "voice_id": voice_id,
                "speed": speed,
                "pitch": pitch,
                "emotion": emotion,
                "format": format,
                "output_format": output_format,
                "text_length": len(text),
            },
        )
    except MinimaxAPIError as err:
        return AIResponse(
            success=False,
            error=format_error(err),
            provider=provider_name,
            model=model,
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )


async def get_voices(
    client: MinimaxClient,
    provider_name: str,
    format_error: Callable = str,
) -> AIResponse:
    """Get available voice list."""
    try:
        payload = await client.post_json("/get_voice", {"voice_type": "all"})
        voices = {
            "system_voice": payload.get("system_voice", []) or SYSTEM_VOICE_CATALOG,
            "voice_cloning": payload.get("voice_cloning", []),
            "voice_generation": payload.get("voice_generation", []),
            "trace_id": payload.get("trace_id"),
        }

        return AIResponse(
            success=True,
            data=voices,
            provider=provider_name,
            model="voice_list",
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )

    except MinimaxAPIError as err:
        return AIResponse(
            success=False,
            error=format_error(err),
            provider=provider_name,
            model="voice_list",
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )
