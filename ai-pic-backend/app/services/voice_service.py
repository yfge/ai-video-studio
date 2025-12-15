"""
Voice service facade

Provides a provider-agnostic entrypoint for voice synthesis, voice design/management,
and MiniMax music generation. MiniMax is the initial provider, but the service is
structured to allow future voice providers.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.minimax_client import MinimaxClient
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG

logger = get_logger(__name__)

DEFAULT_MINIMAX_VOICE_ID = "Chinese (Mandarin)_Lyrical_Voice"


def _compact(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values to avoid sending redundant payload fields."""
    return {k: v for k, v in data.items() if v is not None}


def _to_int(value: Optional[Any]) -> Optional[int]:
    """Coerce numeric to int when not None."""
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


VOICE_TYPE_OPTIONS: List[Dict[str, str]] = [
    {"value": "system", "label_zh": "系统音色", "label_en": "System voices"},
    {"value": "voice_cloning", "label_zh": "快速复刻", "label_en": "Voice cloning"},
    {
        "value": "voice_generation",
        "label_zh": "文生音色",
        "label_en": "Voice generation",
    },
    {"value": "all", "label_zh": "全部", "label_en": "All"},
]

TTS_MODEL_OPTIONS: List[Dict[str, str]] = [
    {
        "value": "speech-2.6-hd",
        "label_zh": "Speech 2.6 高清",
        "label_en": "Speech 2.6 HD",
    },
    {
        "value": "speech-2.6-turbo",
        "label_zh": "Speech 2.6 极速",
        "label_en": "Speech 2.6 Turbo",
    },
    {"value": "speech-02-hd", "label_zh": "Speech 02 高清", "label_en": "Speech 02 HD"},
    {
        "value": "speech-02-turbo",
        "label_zh": "Speech 02 极速",
        "label_en": "Speech 02 Turbo",
    },
    {"value": "speech-01-hd", "label_zh": "Speech 01 高清", "label_en": "Speech 01 HD"},
    {
        "value": "speech-01-turbo",
        "label_zh": "Speech 01 极速",
        "label_en": "Speech 01 Turbo",
    },
]

EMOTION_OPTIONS: List[Dict[str, str]] = [
    {"value": "happy", "label_zh": "高兴", "label_en": "Happy"},
    {"value": "sad", "label_zh": "悲伤", "label_en": "Sad"},
    {"value": "angry", "label_zh": "愤怒", "label_en": "Angry"},
    {"value": "fearful", "label_zh": "害怕", "label_en": "Fearful"},
    {"value": "disgusted", "label_zh": "厌恶", "label_en": "Disgusted"},
    {"value": "surprised", "label_zh": "惊讶", "label_en": "Surprised"},
    {"value": "calm", "label_zh": "中性", "label_en": "Calm"},
    {"value": "fluent", "label_zh": "生动", "label_en": "Fluent"},
    {"value": "whisper", "label_zh": "低语", "label_en": "Whisper"},
]

LANGUAGE_BOOST_OPTIONS: List[Dict[str, str]] = [
    {"value": "Chinese", "label_zh": "中文", "label_en": "Chinese"},
    {"value": "Chinese,Yue", "label_zh": "粤语", "label_en": "Cantonese"},
    {"value": "English", "label_zh": "英语", "label_en": "English"},
    {"value": "Japanese", "label_zh": "日语", "label_en": "Japanese"},
    {"value": "Korean", "label_zh": "韩语", "label_en": "Korean"},
    {"value": "French", "label_zh": "法语", "label_en": "French"},
    {"value": "Spanish", "label_zh": "西班牙语", "label_en": "Spanish"},
    {"value": "German", "label_zh": "德语", "label_en": "German"},
    {"value": "Italian", "label_zh": "意大利语", "label_en": "Italian"},
    {"value": "Russian", "label_zh": "俄语", "label_en": "Russian"},
    {"value": "Thai", "label_zh": "泰语", "label_en": "Thai"},
    {"value": "Vietnamese", "label_zh": "越南语", "label_en": "Vietnamese"},
    {"value": "Indonesian", "label_zh": "印尼语", "label_en": "Indonesian"},
    {"value": "Turkish", "label_zh": "土耳其语", "label_en": "Turkish"},
    {"value": "Arabic", "label_zh": "阿拉伯语", "label_en": "Arabic"},
    {"value": "auto", "label_zh": "自动", "label_en": "Auto detect"},
]

OUTPUT_FORMAT_OPTIONS = [
    {"value": "url", "label_zh": "临时链接（24小时）", "label_en": "URL (24h)"},
    {"value": "hex", "label_zh": "HEX 编码", "label_en": "Hex encoded"},
]

AUDIO_FORMAT_OPTIONS = [
    {"value": "mp3", "label_zh": "MP3", "label_en": "MP3"},
    {"value": "wav", "label_zh": "WAV", "label_en": "WAV"},
    {"value": "pcm", "label_zh": "PCM", "label_en": "PCM"},
    {"value": "flac", "label_zh": "FLAC", "label_en": "FLAC"},
]

SAMPLE_RATE_OPTIONS = [
    {"value": 8000, "label_zh": "8kHz", "label_en": "8000 Hz"},
    {"value": 16000, "label_zh": "16kHz", "label_en": "16000 Hz"},
    {"value": 22050, "label_zh": "22.05kHz", "label_en": "22050 Hz"},
    {"value": 24000, "label_zh": "24kHz", "label_en": "24000 Hz"},
    {"value": 32000, "label_zh": "32kHz", "label_en": "32000 Hz"},
    {"value": 44100, "label_zh": "44.1kHz", "label_en": "44100 Hz"},
]

BITRATE_OPTIONS = [
    {"value": 32000, "label_zh": "32 kbps", "label_en": "32 kbps"},
    {"value": 64000, "label_zh": "64 kbps", "label_en": "64 kbps"},
    {"value": 128000, "label_zh": "128 kbps", "label_en": "128 kbps"},
    {"value": 256000, "label_zh": "256 kbps", "label_en": "256 kbps"},
]

CHANNEL_OPTIONS = [
    {"value": 1, "label_zh": "单声道", "label_en": "Mono"},
    {"value": 2, "label_zh": "双声道", "label_en": "Stereo"},
]

MUSIC_MODEL_OPTIONS = [
    {"value": "music-2.0", "label_zh": "Music 2.0", "label_en": "Music 2.0"},
]


class MinimaxVoiceProvider:
    """MiniMax-specific voice provider built on the shared client."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = MinimaxClient(
            api_key=settings.MINIMAX_API_KEY or "",
            group_id=settings.MINIMAX_GROUP_ID,
            base_url="https://api.minimax.chat/v1",
            timeout=120.0,
        )
        self.voice_cache: Dict[str, Dict[str, Any]] = {}
        self._warm_voice_cache()

    def _warm_voice_cache(self) -> None:
        """Load voice lists on initialization as required."""
        if not self.client.api_key:
            return
        try:
            asyncio.run(self.list_voices(force_refresh=True))
        except RuntimeError:
            threading.Thread(
                target=lambda: asyncio.run(self.list_voices(force_refresh=True)),
                daemon=True,
            ).start()
        except Exception as exc:  # pragma: no cover - startup guard
            self.logger.warning("预加载 MiniMax 音色列表失败: %s", exc)

    def _validate_voice_type(self, voice_type: str) -> str:
        allowed = {item["value"] for item in VOICE_TYPE_OPTIONS}
        if voice_type not in allowed:
            raise ValueError(f"不支持的 voice_type: {voice_type}")
        return voice_type

    async def list_voices(
        self, voice_type: str = "all", force_refresh: bool = False
    ) -> Dict[str, Any]:
        voice_type = self._validate_voice_type(voice_type)
        if not force_refresh and voice_type in self.voice_cache:
            return self.voice_cache[voice_type]

        payload = await self.client.post_json("/get_voice", {"voice_type": voice_type})
        result = {
            "system_voice": payload.get("system_voice", []) or SYSTEM_VOICE_CATALOG,
            "voice_cloning": payload.get("voice_cloning", []),
            "voice_generation": payload.get("voice_generation", []),
            "trace_id": payload.get("trace_id"),
            "base_resp": payload.get("base_resp"),
        }
        self.voice_cache[voice_type] = result
        return result

    async def delete_voice(self, voice_type: str, voice_id: str) -> Dict[str, Any]:
        payload = await self.client.post_json(
            "/delete_voice",
            {"voice_type": self._validate_voice_type(voice_type), "voice_id": voice_id},
        )
        # 删除后刷新缓存，防止脏数据
        try:
            await self.list_voices("all", force_refresh=True)
        except Exception:
            pass
        return {
            "voice_id": payload.get("voice_id"),
            "created_time": payload.get("created_time"),
            "trace_id": payload.get("trace_id"),
            "base_resp": payload.get("base_resp"),
        }

    async def design_voice(
        self,
        prompt: str,
        preview_text: str,
        voice_id: Optional[str] = None,
        aigc_watermark: bool = False,
    ) -> Dict[str, Any]:
        body = await self.client.post_json(
            "/voice_design",
            _compact(
                {
                    "prompt": prompt,
                    "preview_text": preview_text,
                    "voice_id": voice_id,
                    "aigc_watermark": aigc_watermark,
                }
            ),
        )
        return {
            "voice_id": body.get("voice_id"),
            "trial_audio": body.get("trial_audio"),
            "trace_id": body.get("trace_id"),
            "base_resp": body.get("base_resp"),
        }

    async def text_to_speech(
        self,
        *,
        text: str,
        model: str,
        voice_id: Optional[str],
        speed: float,
        vol: Optional[float],
        pitch: Optional[float],
        emotion: Optional[str],
        sample_rate: Optional[int],
        bitrate: Optional[int],
        format: Optional[str],
        channel: Optional[int],
        output_format: str,
        stream: bool,
        subtitle_enable: bool,
        aigc_watermark: bool,
        language_boost: Optional[str] = None,
        text_normalization: Optional[bool] = None,
        latex_read: Optional[bool] = None,
        pronunciation_dict: Optional[Dict[str, Any]] = None,
        stream_options: Optional[Dict[str, Any]] = None,
        timber_weights: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        voice_id = voice_id or DEFAULT_MINIMAX_VOICE_ID
        voice_setting = _compact(
            {
                "voice_id": voice_id,
                "speed": speed,
                "vol": vol,
                "pitch": _to_int(pitch),
                "emotion": emotion,
                "text_normalization": text_normalization,
                "latex_read": latex_read,
            }
        )
        audio_setting = _compact(
            {
                "sample_rate": _to_int(sample_rate),
                "bitrate": _to_int(bitrate),
                "format": format,
                "channel": _to_int(channel),
            }
        )
        payload = _compact(
            {
                "model": model,
                "text": text,
                "stream": stream,
                "output_format": output_format,
                "subtitle_enable": subtitle_enable,
                "aigc_watermark": aigc_watermark,
                "language_boost": language_boost,
                "voice_setting": voice_setting,
                "audio_setting": audio_setting,
                "pronunciation_dict": pronunciation_dict,
                "stream_options": stream_options,
                "timber_weights": timber_weights,
            }
        )

        body = await self.client.post_json("/t2a_v2", payload)
        data = body.get("data") or {}
        audio_value = data.get("audio")
        return {
            "audio_url": audio_value if output_format == "url" else None,
            "audio_hex": audio_value if output_format != "url" else None,
            "subtitle_file": data.get("subtitle_file"),
            "trace_id": body.get("trace_id"),
            "extra_info": body.get("extra_info"),
            "base_resp": body.get("base_resp"),
        }

    async def generate_music(
        self,
        *,
        model: str,
        prompt: str,
        lyrics: str,
        stream: bool,
        output_format: str,
        sample_rate: Optional[int],
        bitrate: Optional[int],
        format: Optional[str],
        aigc_watermark: bool,
    ) -> Dict[str, Any]:
        payload = _compact(
            {
                "model": model,
                "prompt": prompt,
                "lyrics": lyrics,
                "stream": stream,
                "output_format": output_format,
                "audio_setting": _compact(
                    {
                        "sample_rate": sample_rate,
                        "bitrate": bitrate,
                        "format": format,
                    }
                ),
                "aigc_watermark": aigc_watermark,
            }
        )
        body = await self.client.post_json("/music_generation", payload)
        data = body.get("data") or {}
        return {
            "audio_url": data.get("audio") if output_format == "url" else None,
            "audio_hex": data.get("audio") if output_format != "url" else None,
            "status": data.get("status"),
            "trace_id": body.get("trace_id"),
            "extra_info": body.get("extra_info"),
            "base_resp": body.get("base_resp"),
        }


class VoiceService:
    """Facade that selects the correct voice provider (currently MiniMax)."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.providers: Dict[str, MinimaxVoiceProvider] = {}
        if settings.MINIMAX_API_KEY:
            self.providers["minimax"] = MinimaxVoiceProvider()
        self.default_provider: Optional[str] = next(iter(self.providers), None)
        self._enums = self._build_enums()

    def _build_enums(self) -> Dict[str, Any]:
        providers = (
            [{"value": "minimax", "label_zh": "MiniMax", "label_en": "MiniMax"}]
            if self.providers
            else []
        )
        return {
            "providers": providers,
            "voice_types": VOICE_TYPE_OPTIONS,
            "tts_models": TTS_MODEL_OPTIONS,
            "emotions": EMOTION_OPTIONS,
            "language_boost": LANGUAGE_BOOST_OPTIONS,
            "output_formats": OUTPUT_FORMAT_OPTIONS,
            "audio_formats": AUDIO_FORMAT_OPTIONS,
            "sample_rates": SAMPLE_RATE_OPTIONS,
            "bitrates": BITRATE_OPTIONS,
            "channels": CHANNEL_OPTIONS,
            "music_models": MUSIC_MODEL_OPTIONS,
            "defaults": {
                "tts_model": "speech-2.6-hd",
                "voice_id": DEFAULT_MINIMAX_VOICE_ID,
                "output_format": "url",
                "music_model": "music-2.0",
            },
            "system_voices": [
                {
                    "value": item["voice_id"],
                    "label_zh": item["voice_name"],
                    "label_en": item["voice_name"],
                    "language": item.get("language"),
                }
                for item in SYSTEM_VOICE_CATALOG
            ],
        }

    def enums(self) -> Dict[str, Any]:
        return self._enums

    def _get_provider(self, provider: Optional[str]) -> MinimaxVoiceProvider:
        name = provider or self.default_provider
        if not name or name not in self.providers:
            raise ValueError("未配置可用的声音提供商")
        return self.providers[name]

    async def synthesize(
        self, provider: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        client = self._get_provider(provider)
        return await client.text_to_speech(**kwargs)

    async def design_voice(
        self,
        *,
        prompt: str,
        preview_text: str,
        voice_id: Optional[str] = None,
        aigc_watermark: bool = False,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = self._get_provider(provider)
        return await client.design_voice(
            prompt=prompt,
            preview_text=preview_text,
            voice_id=voice_id,
            aigc_watermark=aigc_watermark,
        )

    async def delete_voice(
        self,
        *,
        voice_type: str,
        voice_id: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = self._get_provider(provider)
        return await client.delete_voice(voice_type=voice_type, voice_id=voice_id)

    async def list_voices(
        self,
        voice_type: str = "all",
        provider: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        client = self._get_provider(provider)
        return await client.list_voices(
            voice_type=voice_type, force_refresh=force_refresh
        )

    async def generate_music(
        self,
        *,
        model: str,
        prompt: str,
        lyrics: str,
        stream: bool,
        output_format: str,
        sample_rate: Optional[int],
        bitrate: Optional[int],
        format: Optional[str],
        aigc_watermark: bool,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = self._get_provider(provider)
        return await client.generate_music(
            model=model,
            prompt=prompt,
            lyrics=lyrics,
            stream=stream,
            output_format=output_format,
            sample_rate=sample_rate,
            bitrate=bitrate,
            format=format,
            aigc_watermark=aigc_watermark,
        )


voice_service = VoiceService()
