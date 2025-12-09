"""
火山引擎(Volcengine)服务提供商

支持文本生成、图像生成和视频生成等功能
"""

import httpx
import asyncio
import json
from typing import List, Optional, Dict, Any
from app.core.logging import get_logger
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig

logger = get_logger(__name__)

class VolcengineProvider(BaseProvider):
    """火山引擎服务提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self.region = config.region if hasattr(config, 'region') else "cn-beijing"
    
    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.TEXT_TO_SPEECH
        ]
    
    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            # 文本生成模型
            ModelInfo(
                model_id="doubao-lite-4k",
                name="豆包轻量版",
                description="轻量级文本生成模型，快速响应",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=4096,
                capabilities=["text_generation", "conversation", "fast_response"]
            ),
            ModelInfo(
                model_id="doubao-pro-4k",
                name="豆包专业版",
                description="专业级文本生成模型，高质量输出",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=4096,
                capabilities=["text_generation", "analysis", "reasoning", "high_quality"]
            ),
            ModelInfo(
                model_id="doubao-pro-32k",
                name="豆包专业版长文本",
                description="支持长文本处理的专业版模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=32768,
                capabilities=["text_generation", "long_context", "document_analysis"]
            ),
            ModelInfo(
                model_id="seedream-4.5",
                name="Seedream 4.5",
                description="方舟大模型服务平台的图片生成模型",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "high_resolution"]
            ),
            # 图像生成模型
            ModelInfo(
                model_id="volcengine-visual-v1",
                name="火山视觉生成V1",
                description="高质量图像生成模型",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "style_control", "high_resolution"]
            ),
            ModelInfo(
                model_id="volcengine-visual-pro",
                name="火山视觉生成Pro",
                description="专业版图像生成，支持更多风格",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "multiple_styles", "ultra_quality"]
            ),
            # 视频生成模型
            ModelInfo(
                model_id="volcengine-video-v1",
                name="火山视频生成V1",
                description="AI视频生成模型",
                model_type=AIModelType.TEXT_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["text_to_video", "motion_control", "scene_generation"]
            ),
            # 语音合成模型
            ModelInfo(
                model_id="volcengine-tts-v1",
                name="火山语音合成",
                description="高质量语音合成服务",
                model_type=AIModelType.TEXT_TO_SPEECH,
                supported_formats=["mp3", "wav"],
                capabilities=["text_to_speech", "emotion_control", "voice_cloning"]
            )
        ]

    def _fallback_models(self, model_type: Optional[AIModelType]) -> List[ModelInfo]:
        models = self.available_models
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        return models

    def _infer_model_type(self, model_id: str, item: Dict[str, Any]) -> AIModelType:
        """根据模型 id 和能力字段推断模型类型，尽量覆盖文本/图像/视频/语音。"""
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
        lid = model_id.lower()
        tokens.append(lid)

        if any(tag in tokens for tag in ["image", "visual", "seedream", "picture", "painting"]):
            return AIModelType.TEXT_TO_IMAGE
        if any(tag in tokens for tag in ["video", "vid", "movie"]):
            return AIModelType.TEXT_TO_VIDEO
        if any(tag in tokens for tag in ["tts", "speech", "voice", "audio"]):
            return AIModelType.TEXT_TO_SPEECH
        if any(tag in tokens for tag in ["stt", "asr"]):
            return AIModelType.SPEECH_TO_TEXT
        return AIModelType.TEXT_GENERATION

    def _infer_capabilities(
        self,
        model_type: AIModelType,
        item: Dict[str, Any],
    ) -> List[str]:
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
        # 去重保持顺序
        return list(dict.fromkeys(caps))

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """
        调用火山引擎 Ark /models 列表，结合本地白名单过滤，失败则回退静态列表。
        """
        fallback = self._fallback_models(model_type)
        client = await self.get_client()
        if client is None:
            return fallback

        try:
            resp = await client.get(f"{self.base_url}/models")
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("data") or payload.get("models") or payload
            models: List[ModelInfo] = []
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                mid = item.get("id") or item.get("model") or item.get("model_id")
                if not mid:
                    continue
                mtype = self._infer_model_type(mid, item)
                if mtype not in self.supported_model_types:
                    continue
                if model_type and mtype != model_type:
                    continue
                models.append(
                    ModelInfo(
                        model_id=mid,
                        name=item.get("name") or item.get("model_name") or mid,
                        description=item.get("description") or item.get("desc") or f"Volcengine model {mid}",
                        model_type=mtype,
                        capabilities=self._infer_capabilities(mtype, item),
                    )
                )
            return models or fallback
        except Exception:
            return fallback
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 如果有region信息，添加到头部
        if self.region:
            headers["X-Region"] = self.region
        
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers
        )

    async def _stream_chat_completion(self, payload: Dict[str, Any], model: str):
        """使用火山方舟流式接口拼接响应。"""
        client = await self.get_client()
        if client is None:
            raise RuntimeError("Volcengine client not initialized")

        url = f"{self.base_url}/chat/completions"
        content_parts: list[str] = []
        usage: Dict[str, Any] = {}
        finish_reason: Optional[str] = None

        async with client.stream("POST", url, json=payload) as resp:
            if resp.status_code >= 400:
                detail = await resp.aread()
                raise httpx.HTTPStatusError(
                    message=f"Volcengine stream status {resp.status_code} body={detail.decode(errors='ignore')}",
                    request=resp.request,
                    response=resp,
                )

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                except Exception:
                    continue
                if event.get("usage"):
                    usage = event["usage"]
                for choice in event.get("choices", []):
                    delta = choice.get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        content_parts.append(piece)
                    finish_reason = choice.get("finish_reason") or finish_reason

        return "".join(content_parts).strip(), usage, finish_reason
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "doubao-pro-4k",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        system_prompt: str = None,
        **kwargs
    ) -> AIResponse:
        """使用豆包生成文本"""
        try:
            client = await self.get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                **kwargs
            }

            stream = bool(request_data.pop("stream", True))
            
            if stream:
                try:
                    streamed_content, usage, finish_reason = await self._stream_chat_completion(
                        {**request_data, "stream": True},
                        model,
                    )
                    if streamed_content:
                        return AIResponse(
                            success=True,
                            data=streamed_content,
                            provider=self.name,
                            model=model,
                            task_type=AITaskType.STORY_GENERATION,
                            model_type=AIModelType.TEXT_GENERATION,
                            usage=usage,
                            metadata={
                                "finish_reason": finish_reason,
                                "stream": True,
                            }
                        )
                    logger.warning("Volcengine stream returned empty content; falling back to non-stream.")
                except Exception as stream_err:  # noqa: BLE001
                    logger.warning("Volcengine stream failed, falling back to non-stream: %s", stream_err, exc_info=True)

            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎API错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.STORY_GENERATION,
                    model_type=AIModelType.TEXT_GENERATION
                )
            
            content = data["choices"][0]["message"]["content"]
            
            return AIResponse(
                success=True,
                data=content,
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
                usage=data.get("usage", {}),
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0)
                }
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION
            )
    
    async def generate_image(
        self, 
        prompt: str, 
        model: str = "volcengine-visual-v1",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.5,
        style: str = "realistic",
        seed: int = -1,
        **kwargs
    ) -> AIResponse:
        """使用火山引擎生成图像（对齐方舟 Seedream 图片生成 API）"""
        try:
            client = await self.get_client()

            # Ark 图片生成 API 使用统一的 /images 入口，模型 ID 需要映射到真正的 Ark 模型名
            normalized = (model or "").lower()
            ark_model = model

            # Seedream 4.5 文生图模型（参考官方文档中的示例 model）
            if normalized.startswith("seedream") or "seedream-4.5" in normalized:
                ark_model = "doubao-seedream-4-5-251128"

            # 规格参数：Ark 使用 size 字符串而非宽高整数，官方示例为 \"2K\"
            # 为避免尺寸校验错误，这里默认使用 2K，如需其它规格可通过 kwargs.size 覆盖
            size = kwargs.pop("size", None) or "2K"

            request_data = {
                "model": ark_model,
                "prompt": prompt,
                "size": size,
                # 返回 URL，方便后续下载到本地 / 上传 OSS
                "response_format": "url",
                # 默认关闭水印，行为可以在调用层通过 kwargs 覆盖
                "watermark": kwargs.pop("watermark", False),
            }

            if seed != -1:
                request_data["seed"] = seed

            # 允许透传少量高级参数（如果未来文档有补充，例如 negative_prompt / n 等）
            for key in ("negative_prompt", "n"):
                if key in kwargs:
                    request_data[key] = kwargs[key]

            response = await client.post(
                f"{self.base_url}/images/generations",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()

            # Ark 错误响应通常包含 error 节点，优先检查并直接返回
            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎图像生成错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE
                )

            # 同步返回：data 数组中包含 url / size 等字段
            if "data" in data:
                images = data.get("data") or []
                image_urls = [img.get("url") for img in images if isinstance(img, dict) and img.get("url")]
                if image_urls:
                    return AIResponse(
                        success=True,
                        data={"images": image_urls},
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE,
                        usage=data.get("usage", {}),
                        metadata={
                            "size": size,
                            "style": style,
                            "raw_model": ark_model,
                            "count": len(image_urls),
                        },
                    )

            return AIResponse(
                success=False,
                error="图像生成响应格式错误",
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE
            )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str | None = None,
        model: str | None = None,
        n: int = 1,
        size: str | None = None,
        **kwargs,
    ) -> AIResponse:
        """
        使用火山 Seedream 图片生成 API 做图生图

        对齐 docs/api/volcengine-image.md 中 doubao-seedream-4.5 的说明：
        - 入口仍然是 POST /api/v3/images/generations
        - 通过 image 字段传入 data:image/...;base64,... 格式的参考图
        - 通过 sequential_image_generation / sequential_image_generation_options.max_images 控制多图输出
        """
        normalized = (model or "").lower()
        # 目前只对 Seedream 4.5 / 4.0 做图生图实现，其它模型沿用上层 fallback 逻辑
        if not (normalized.startswith("seedream") or "seedream-4.5" in normalized):
            return AIResponse(
                success=False,
                error="当前 Volcengine 图生图仅支持 Seedream 系列模型",
                provider=self.name,
                model=model or "unknown",
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        # 映射到 Ark 实际模型 ID（与 generate_image 保持一致）
        ark_model = model
        if normalized.startswith("seedream") or "seedream-4.5" in normalized:
            ark_model = "doubao-seedream-4-5-251128"

        try:
            client = await self.get_client()

            # 1) 下载一张或多张参考图并转成 data:image/...;base64,... 形式
            extra_images: list[str] = kwargs.pop("extra_images", []) or []
            base64_images: list[str] = kwargs.pop("base64_images", []) or []
            if base64_images:
                image_payloads = base64_images[:14]
            else:
                urls: list[str] = [image_url] + [u for u in extra_images if u]
                # Seedream 最多 14 张参考图
                urls = urls[:14]

                import base64

                image_payloads: list[str] = []
                for url in urls:
                    img_resp = await client.get(url)
                    img_resp.raise_for_status()
                    content_type = img_resp.headers.get("Content-Type", "image/png")
                    subtype = "png"
                    if "/" in content_type:
                        subtype = content_type.split("/")[-1] or "png"
                    b64_data = base64.b64encode(img_resp.content).decode("ascii")
                    image_payloads.append(f"data:image/{subtype.lower()};base64,{b64_data}")

            # 2) 组装 Ark 请求体（单图=字符串，多图=数组）
            effective_size = size or "2K"
            max_images = max(1, int(n) if n and n > 0 else 1)

            request_data: Dict[str, Any] = {
                "model": ark_model,
                "prompt": prompt or "",
                "image": image_payloads[0] if len(image_payloads) == 1 else image_payloads,
                "size": effective_size,
                "response_format": "url",
                "watermark": kwargs.pop("watermark", False),
            }

            # 多图时开启组图能力；单图保持 sequential_image_generation=disabled
            if max_images > 1:
                request_data["sequential_image_generation"] = "auto"
                request_data["sequential_image_generation_options"] = {
                    "max_images": max_images
                }
            else:
                request_data["sequential_image_generation"] = "disabled"

            response = await client.post(
                f"{self.base_url}/images/generations",
                json=request_data,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎图生图错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model or ark_model,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.IMAGE_TO_IMAGE,
                )

            if "data" in data:
                images = data.get("data") or []
                image_urls = [
                    img.get("url")
                    for img in images
                    if isinstance(img, dict) and img.get("url")
                ]
                if image_urls:
                    return AIResponse(
                        success=True,
                        data={"images": image_urls},
                        provider=self.name,
                        model=model or ark_model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.IMAGE_TO_IMAGE,
                        usage=data.get("usage", {}),
                        metadata={
                            "size": effective_size,
                            "raw_model": ark_model,
                            "count": len(image_urls),
                            "sequential_image_generation": request_data.get(
                                "sequential_image_generation"
                            ),
                        },
                    )

            return AIResponse(
                success=False,
                error="图生图响应格式错误",
                provider=self.name,
                model=model or ark_model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model or ark_model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )
    
    async def generate_video(
        self, 
        prompt: str, 
        model: str = "volcengine-video-v1",
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        style: str = "realistic",
        **kwargs
    ) -> AIResponse:
        """使用火山引擎生成视频"""
        try:
            client = await self.get_client()
            
            request_data = {
                "model": model,
                "prompt": prompt,
                "duration": duration,
                "fps": fps,
                "resolution": resolution,
                "style": style,
                **kwargs
            }
            
            response = await client.post(
                f"{self.base_url}/videos/generations",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                return AIResponse(
                    success=False,
                    error=f"火山引擎视频生成错误: {data['error'].get('message', 'Unknown error')}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.TEXT_TO_VIDEO
                )
            
            # 视频生成通常为异步任务
            task_id = data.get("task_id")
            if task_id:
                result = await self._poll_task_status(task_id, "video")
                if result:
                    return AIResponse(
                        success=True,
                        data={
                            "video_url": result.get("video_url"),
                            "thumbnail_url": result.get("thumbnail_url"),
                            "duration": duration
                        },
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.VIDEO_GENERATION,
                        model_type=AIModelType.TEXT_TO_VIDEO,
                        metadata={
                            "task_id": task_id,
                            "duration": duration,
                            "fps": fps,
                            "resolution": resolution,
                            "style": style
                        }
                    )
            
            return AIResponse(
                success=False,
                error="视频生成任务失败",
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO
            )
    
    async def text_to_speech(
        self, 
        text: str, 
        model: str = "volcengine-tts-v1",
        voice_type: str = "BV001_streaming",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 1.0,
        emotion: str = "neutral",
        format: str = "mp3",
        **kwargs
    ) -> AIResponse:
        """火山引擎文本转语音"""
        try:
            client = await self.get_client()
            
            request_data = {
                "app": {
                    "appid": "your_app_id",  # 需要在配置中提供
                    "token": self.config.api_key,
                    "cluster": "volcano_tts"
                },
                "user": {
                    "uid": "user_001"
                },
                "audio": {
                    "voice_type": voice_type,
                    "encoding": format,
                    "speed_ratio": speed,
                    "volume_ratio": volume,
                    "pitch_ratio": pitch,
                    "emotion": emotion
                },
                "request": {
                    "reqid": f"tts_{asyncio.get_event_loop().time()}",
                    "text": text,
                    "text_type": "plain",
                    "operation": "submit"
                }
            }
            
            response = await client.post(
                f"{self.base_url}/tts/submit",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 0:
                # 异步任务，需要轮询结果
                task_id = data.get("task_id")
                if task_id:
                    result = await self._poll_tts_status(task_id)
                    if result:
                        return AIResponse(
                            success=True,
                            data={
                                "audio_url": result.get("audio_url"),
                                "duration": result.get("duration")
                            },
                            provider=self.name,
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
                                "text_length": len(text)
                            }
                        )
            else:
                error_msg = data.get("message", "Unknown error")
                return AIResponse(
                    success=False,
                    error=f"火山引擎TTS错误: {error_msg}",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VOICE_GENERATION,
                    model_type=AIModelType.TEXT_TO_SPEECH
                )
            
            return AIResponse(
                success=False,
                error="语音生成任务失败",
                provider=self.name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
    
    async def _poll_task_status(
        self, 
        task_id: str,
        task_type: str,
        max_attempts: int = 60,
        delay: int = 3
    ) -> Optional[Dict[str, Any]]:
        """轮询任务状态"""
        client = await self.get_client()
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(
                    f"{self.base_url}/tasks/{task_id}",
                    params={"task_type": task_type}
                )
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status")
                
                if status == "success":
                    return data.get("result")
                elif status == "failed":
                    return None
                elif status in ["pending", "running", "processing"]:
                    await asyncio.sleep(delay)
                    continue
                else:
                    return None
                    
            except Exception as e:
                print(f"轮询火山引擎任务状态失败 (尝试 {attempt + 1}): {e}")
                await asyncio.sleep(delay)
        
        return None
    
    async def _poll_tts_status(
        self, 
        task_id: str,
        max_attempts: int = 30,
        delay: int = 2
    ) -> Optional[Dict[str, Any]]:
        """轮询TTS任务状态"""
        client = await self.get_client()
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{self.base_url}/tts/query/{task_id}")
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("code") == 0:
                    audio_info = data.get("data", {})
                    if audio_info.get("status") == "success":
                        return {
                            "audio_url": audio_info.get("audio_url"),
                            "duration": audio_info.get("duration")
                        }
                    elif audio_info.get("status") == "failed":
                        return None
                    else:
                        await asyncio.sleep(delay)
                        continue
                else:
                    return None
                    
            except Exception as e:
                print(f"轮询火山引擎TTS状态失败 (尝试 {attempt + 1}): {e}")
                await asyncio.sleep(delay)
        
        return None
    
    async def get_voice_types(self) -> AIResponse:
        """获取可用的声音类型列表"""
        try:
            # 火山引擎预定义的声音类型
            voice_types = [
                {"voice_type": "BV001_streaming", "name": "通用女声", "gender": "female", "language": "zh"},
                {"voice_type": "BV002_streaming", "name": "通用男声", "gender": "male", "language": "zh"},
                {"voice_type": "BV003_streaming", "name": "温暖女声", "gender": "female", "style": "warm"},
                {"voice_type": "BV004_streaming", "name": "阳光男声", "gender": "male", "style": "energetic"},
                {"voice_type": "BV005_streaming", "name": "知性女声", "gender": "female", "style": "intellectual"},
                {"voice_type": "BV006_streaming", "name": "成熟男声", "gender": "male", "style": "mature"},
                {"voice_type": "BV007_streaming", "name": "甜美女声", "gender": "female", "style": "sweet"},
                {"voice_type": "BV008_streaming", "name": "磁性男声", "gender": "male", "style": "magnetic"}
            ]
            
            return AIResponse(
                success=True,
                data=voice_types,
                provider=self.name,
                model="voice_types",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="voice_types",
                task_type=AITaskType.VOICE_GENERATION,
                model_type=AIModelType.TEXT_TO_SPEECH
            )
