"""
Volcengine text-to-speech module.

Contains TTS functionality with async polling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict

import httpx

from ..base import AIModelType, AIResponse, AITaskType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Predefined voice types for Volcengine TTS
VOICE_TYPES = [
    {
        "voice_type": "BV001_streaming",
        "name": "通用女声",
        "gender": "female",
        "language": "zh",
    },
    {
        "voice_type": "BV002_streaming",
        "name": "通用男声",
        "gender": "male",
        "language": "zh",
    },
    {
        "voice_type": "BV003_streaming",
        "name": "温暖女声",
        "gender": "female",
        "style": "warm",
    },
    {
        "voice_type": "BV004_streaming",
        "name": "阳光男声",
        "gender": "male",
        "style": "energetic",
    },
    {
        "voice_type": "BV005_streaming",
        "name": "知性女声",
        "gender": "female",
        "style": "intellectual",
    },
    {
        "voice_type": "BV006_streaming",
        "name": "成熟男声",
        "gender": "male",
        "style": "mature",
    },
    {
        "voice_type": "BV007_streaming",
        "name": "甜美女声",
        "gender": "female",
        "style": "sweet",
    },
    {
        "voice_type": "BV008_streaming",
        "name": "磁性男声",
        "gender": "male",
        "style": "magnetic",
    },
]


async def poll_tts_status(
    client: httpx.AsyncClient,
    base_url: str,
    task_id: str,
    max_attempts: int = 30,
    delay: int = 2,
) -> Dict[str, Any]:
    """Poll TTS task status.

    Returns result dict on success; raises RuntimeError on failure/timeout.
    """
    last_error: str | None = None

    for attempt in range(max_attempts):
        try:
            response = await client.get(f"{base_url}/tts/query/{task_id}")
            response.raise_for_status()

            data = response.json()

            if data.get("code") == 0:
                audio_info = data.get("data", {})
                if audio_info.get("status") == "success":
                    return {
                        "audio_url": audio_info.get("audio_url"),
                        "duration": audio_info.get("duration"),
                    }
                elif audio_info.get("status") == "failed":
                    err_msg = audio_info.get("message", "TTS任务执行失败")
                    raise RuntimeError(f"火山引擎TTS任务失败: {err_msg}")
                else:
                    await asyncio.sleep(delay)
                    continue
            else:
                err_msg = data.get("message", f"错误码: {data.get('code')}")
                raise RuntimeError(f"火山引擎TTS查询失败: {err_msg}")

        except RuntimeError:
            raise
        except Exception as e:
            last_error = str(e)
            logger.warning(
                "轮询火山引擎TTS状态失败 (尝试 %d/%d): %s",
                attempt + 1,
                max_attempts,
                e,
            )
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"火山引擎TTS任务 {task_id} 轮询超时 ({max_attempts * delay}s)"
        + (f", 最后错误: {last_error}" if last_error else "")
    )


async def text_to_speech(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    api_key: str,
    text: str,
    model: str = "volcengine-tts-v1",
    voice_type: str = "BV001_streaming",
    speed: float = 1.0,
    volume: float = 1.0,
    pitch: float = 1.0,
    emotion: str = "neutral",
    format: str = "mp3",
    format_error: callable = str,
    **kwargs,
) -> AIResponse:
    """Generate speech from text using Volcengine TTS."""
    try:
        request_data = {
            "app": {
                "appid": "your_app_id",  # Needs to be provided in config
                "token": api_key,
                "cluster": "volcano_tts",
            },
            "user": {"uid": "user_001"},
            "audio": {
                "voice_type": voice_type,
                "encoding": format,
                "speed_ratio": speed,
                "volume_ratio": volume,
                "pitch_ratio": pitch,
                "emotion": emotion,
            },
            "request": {
                "reqid": f"tts_{asyncio.get_event_loop().time()}",
                "text": text,
                "text_type": "plain",
                "operation": "submit",
            },
        }

        response = await client.post(f"{base_url}/tts/submit", json=request_data)
        response.raise_for_status()

        data = response.json()

        if data.get("code") != 0:
            error_msg = data.get("message", "Unknown error")
            return AIResponse(
                success=False,
                error=f"火山引擎TTS错误: {error_msg}",
                provider=provider_name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH,
            )

        # Async task, need to poll for result
        task_id = data.get("task_id")
        if not task_id:
            return AIResponse(
                success=False,
                error="火山引擎TTS未返回task_id",
                provider=provider_name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH,
            )

        # poll_tts_status raises RuntimeError on failure/timeout
        result = await poll_tts_status(client, base_url, task_id)
        return AIResponse(
            success=True,
            data={
                "audio_url": result.get("audio_url"),
                "duration": result.get("duration"),
            },
            provider=provider_name,
            model=model,
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
            metadata={
                "voice_type": voice_type,
                "speed": speed,
                "volume": volume,
                "pitch": pitch,
                "emotion": emotion,
                "format": format,
                "text_length": len(text),
            },
        )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=model,
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )


def get_voice_types(provider_name: str) -> AIResponse:
    """Get available voice types."""
    try:
        return AIResponse(
            success=True,
            data=VOICE_TYPES,
            provider=provider_name,
            model="voice_types",
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )
    except Exception as e:
        return AIResponse(
            success=False,
            error=str(e),
            provider=provider_name,
            model="voice_types",
            task_type=AITaskType.VOICE_GENERATION,
            model_type=AIModelType.TEXT_TO_SPEECH,
        )
