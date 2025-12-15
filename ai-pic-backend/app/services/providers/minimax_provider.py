"""
MiniMax服务提供商

支持文本生成和语音相关功能
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, Dict, Any

from app.services.minimax_client import MinimaxAPIError, MinimaxClient
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG

from .base import (
    BaseProvider,
    AIResponse,
    AIModelType,
    AITaskType,
    ModelInfo,
    ProviderConfig,
)


class MinimaxProvider(BaseProvider):
    """MiniMax服务提供商"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = MinimaxClient(
            api_key=config.api_key or "",
            group_id=config.group_id,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self.base_url = self.client.base_url
        self.group_id = config.group_id

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [AIModelType.TEXT_GENERATION, AIModelType.TEXT_TO_SPEECH]

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            # 文本生成模型
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
            # 语音合成模型
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
        ]

    async def _initialize_client(self):
        """初始化HTTP客户端"""
        await self.get_client()

    async def get_client(self):
        client = await self.client.get_client()
        try:
            self._loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            self._loop_id = None
        self._client = client
        return client

    async def generate_text(
        self,
        prompt: str,
        model: str = "abab6.5-chat",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str = None,
        **kwargs,
    ) -> AIResponse:
        """使用MiniMax生成文本"""
        try:
            # MiniMax 暂不支持流式，这里忽略外部传入的 stream 标记
            kwargs.pop("stream", None)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                **kwargs,
            }
            if max_tokens is not None:
                request_data["max_tokens"] = max_tokens

            data = await self.client.post_json("/text/chatcompletion_v2", request_data)
            content = data.get("choices", [{}])[0].get("message", {}).get("content")

            return AIResponse(
                success=True,
                data=content,
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
                usage=data.get("usage", {}),
                metadata={
                    "finish_reason": data.get("choices", [{}])[0].get("finish_reason"),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                    "trace_id": data.get("trace_id"),
                },
            )
        except MinimaxAPIError as err:
            return AIResponse(
                success=False,
                error=self.format_error(err),
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

    async def generate_image(
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """MiniMax不支持图像生成"""
        return AIResponse(
            success=False,
            error="MiniMax暂不支持图像生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def text_to_speech(
        self,
        text: str,
        model: str = "speech-2.6-hd",
        voice_id: str = "Chinese (Mandarin)_Lyrical_Voice",
        speed: float = 1.0,
        pitch: float = 0.0,
        emotion: str = "neutral",
        format: str = "mp3",
        output_format: str = "url",
        stream: bool = False,
        **kwargs,
    ) -> AIResponse:
        """MiniMax文本转语音"""
        try:
            voice_setting = {
                "voice_id": voice_id,
                "speed": speed,
                "pitch": pitch,
                "emotion": emotion,
                "vol": kwargs.pop("vol", 1.0),
            }
            audio_setting = {
                "format": format,
                "sample_rate": kwargs.pop("sample_rate", None),
                "bitrate": kwargs.pop("bitrate", None),
                "channel": kwargs.pop("channel", None),
            }
            # 清理 None 字段，避免发送冗余参数
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

            data = await self.client.post_json("/t2a_v2", request_data)
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
                provider=self.name,
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
                error=self.format_error(err),
                provider=self.name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH,
            )

    async def get_voices(self) -> AIResponse:
        """获取可用的语音列表"""
        try:
            payload = await self.client.post_json("/get_voice", {"voice_type": "all"})
            voices = {
                "system_voice": payload.get("system_voice", []) or SYSTEM_VOICE_CATALOG,
                "voice_cloning": payload.get("voice_cloning", []),
                "voice_generation": payload.get("voice_generation", []),
                "trace_id": payload.get("trace_id"),
            }

            return AIResponse(
                success=True,
                data=voices,
                provider=self.name,
                model="voice_list",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH,
            )

        except MinimaxAPIError as err:
            return AIResponse(
                success=False,
                error=self.format_error(err),
                provider=self.name,
                model="voice_list",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH,
            )
