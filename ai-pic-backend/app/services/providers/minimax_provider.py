"""
MiniMax服务提供商

支持文本生成、语音合成和视频生成功能

Updated to support video generation via:
- POST /v1/video_generation (create task)
- GET /v1/query/video_generation (query status)
- GET /v1/files/retrieve (get video file)
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.services.minimax_client import MinimaxAPIError, MinimaxClient
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG

from .base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from .polling_utils import TaskPoller, minimax_status_mapper


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
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_SPEECH,
            AIModelType.IMAGE_TO_VIDEO,
            AIModelType.TEXT_TO_VIDEO,
        ]

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
            # 视频生成模型
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
        emotion: Optional[str] = None,
        format: str = "mp3",
        output_format: str = "url",
        stream: bool = False,
        **kwargs,
    ) -> AIResponse:
        """MiniMax文本转语音"""
        try:
            # ai_service_manager 会透传 voice_type，但 MiniMax T2A API 不接收该字段
            kwargs.pop("voice_type", None)

            def _to_int(value: Any) -> Optional[int]:
                if value is None:
                    return None
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None

            voice_setting = {
                "voice_id": voice_id,
                "speed": speed,
                # MiniMax 侧期望 pitch 为整数（int64），避免 float 导致 invalid params
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

    async def generate_video(
        self,
        first_frame_image: str,
        prompt: Optional[str] = None,
        last_frame_image: Optional[str] = None,
        model: str = "MiniMax-Hailuo-2.3",
        duration: int = 6,  # 6 or 10 seconds
        resolution: str = "768P",  # 512P, 720P, 768P, or 1080P
        prompt_optimizer: bool = True,
        fast_pretreatment: bool = False,
        aigc_watermark: bool = False,
        **kwargs,
    ) -> AIResponse:
        """
        Generate video from image(s) using MiniMax video generation API.

        Endpoint: POST /v1/video_generation
        Polling: GET /v1/query/video_generation

        Args:
            first_frame_image: First frame image (URL or base64 data URL)
            prompt: Text description (max 2000 chars), supports camera control directives
            last_frame_image: Last frame image (optional, for first-last frame generation)
            model: Video generation model name
            duration: Video duration in seconds (6 or 10)
            resolution: Video resolution (512P/720P/768P/1080P, depends on model)
            prompt_optimizer: Auto-optimize prompt (default True)
            fast_pretreatment: Faster prompt optimization (Hailuo 2.3/02 only)
            aigc_watermark: Add watermark to generated video

        Returns:
            AIResponse with video URL or error
        """
        try:
            # Build request payload
            payload = {
                "model": model,
                "first_frame_image": first_frame_image,
                "duration": duration,
                "resolution": resolution,
                "prompt_optimizer": prompt_optimizer,
                "aigc_watermark": aigc_watermark,
            }

            if prompt:
                payload["prompt"] = prompt
            if last_frame_image:
                payload["last_frame_image"] = last_frame_image
            if fast_pretreatment and model in [
                "MiniMax-Hailuo-2.3",
                "MiniMax-Hailuo-2.3-Fast",
                "MiniMax-Hailuo-02",
            ]:
                payload["fast_pretreatment"] = fast_pretreatment

            # Create video generation task
            response_data = await self.client.post_json("/video_generation", payload)

            task_id = response_data.get("task_id")
            if not task_id:
                return AIResponse(
                    success=False,
                    error="No task_id in response",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                )

            # Poll task status
            result = await self._poll_video_task(task_id)

            if result and "video_url" in result:
                return AIResponse(
                    success=True,
                    data={
                        "video_url": result["video_url"],
                        "file_id": result.get("file_id"),
                        "duration": duration,
                        "width": result.get("video_width"),
                        "height": result.get("video_height"),
                    },
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                    metadata={
                        "task_id": task_id,
                        "resolution": resolution,
                        "duration": duration,
                    },
                )
            else:
                return AIResponse(
                    success=False,
                    error="Video generation task failed or timed out",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                )

        except MinimaxAPIError as err:
            return AIResponse(
                success=False,
                error=self.format_error(err),
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

    async def _poll_video_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll video generation task status.

        Endpoint: GET /v1/query/video_generation?task_id={task_id}
        """

        async def poll_fn() -> Dict[str, Any]:
            return await self.client.get_json(
                "/query/video_generation", params={"task_id": task_id}
            )

        async def extract_result(data: Dict[str, Any]) -> Dict[str, Any]:
            """Extract video info and download URL from response"""
            file_id = data.get("file_id")
            if not file_id:
                return {}

            # Retrieve video file information
            file_info = await self._retrieve_video_file(file_id)
            if file_info:
                return {
                    "video_url": file_info.get("download_url"),
                    "file_id": file_id,
                    "video_width": data.get("video_width"),
                    "video_height": data.get("video_height"),
                }
            return {}

        poller = TaskPoller(
            poll_fn=poll_fn,
            status_mapper=minimax_status_mapper,
            result_extractor=extract_result,
            max_attempts=120,  # 20 minutes with 10s interval
            initial_delay=10.0,
            task_id=task_id,
            task_type="video",
        )

        return await poller.poll()

    async def _retrieve_video_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve video file information including download URL.

        Endpoint: GET /v1/files/retrieve?file_id={file_id}

        Args:
            file_id: File ID from successful video generation task

        Returns:
            File information dict with download_url, or None on error
        """
        try:
            response_data = await self.client.get_json(
                "/files/retrieve", params={"file_id": file_id}
            )

            file_obj = response_data.get("file", {})
            return {
                "file_id": file_obj.get("file_id"),
                "download_url": file_obj.get("download_url"),
                "filename": file_obj.get("filename"),
                "bytes": file_obj.get("bytes"),
                "created_at": file_obj.get("created_at"),
            }

        except MinimaxAPIError as err:
            # Log error but don't crash
            print(f"Error retrieving video file {file_id}: {err}")
            return None
