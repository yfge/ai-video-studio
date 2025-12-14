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
            AIModelType.IMAGE_TO_VIDEO,
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
                capabilities=["text_to_image", "image_to_image", "high_resolution"]
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
            # Seedream 图生视频（内部走 Ark Video Generation / Seedance）
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
            ),
            # 视频生成模型（Volcengine Ark / Seedance）
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
        max_tokens: Optional[int] = None,
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
                "temperature": temperature,
                "top_p": top_p,
                **kwargs,
            }
            if max_tokens is not None:
                request_data["max_tokens"] = max_tokens

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
        last_error: Exception | None = None
        for attempt in range(2):
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
                last_error = e
                if "handler is closed" in str(e).lower() and attempt == 0:
                    # 连接已被底层关闭，重建客户端重试一次
                    await self._initialize_client()
                    continue
                break

        return AIResponse(
            success=False,
            error=self.format_error(last_error) if last_error else "图像生成失败",
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

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                client = await self.get_client()

                # 1) 下载一张或多张参考图并转成 data:image/...;base64,... 形式
                extra_images: list[str] = kwargs.pop("extra_images", []) or []
                base64_images: list[str] = kwargs.pop("base64_images", []) or []
                if base64_images:
                    # 上游已将所有参考图转为 data:image/...;base64,... 形式，这里直接复用
                    image_payloads = base64_images[:14]
                else:
                    # 兼容直接传入 URL 的调用路径，此时在 Provider 内部逐个下载并容忍部分失败
                    urls_raw: list[str] = [image_url] + [u for u in extra_images if u]
                    urls: list[str] = []
                    for u in urls_raw:
                        if not u:
                            continue
                        if u not in urls:
                            urls.append(u)

                    # Seedream 最多 14 张参考图
                    urls = urls[:14]

                    import base64

                    image_payloads: list[str] = []
                    for url in urls:
                        try:
                            download_url = url
                            if isinstance(download_url, str) and download_url.lower().startswith("https://"):
                                download_url = "http://" + download_url[len("https://"):]
                            img_resp = await client.get(download_url)
                            img_resp.raise_for_status()
                        except Exception as e:
                            logger.warning(
                                "Volcengine image_to_image skip bad ref url=%s error=%s",
                                download_url,
                                e,
                            )
                            continue

                        content_type = img_resp.headers.get("Content-Type", "image/png")
                        subtype = "png"
                        if "/" in content_type:
                            subtype = content_type.split("/")[-1] or "png"
                        b64_data = base64.b64encode(img_resp.content).decode("ascii")
                        image_payloads.append(
                            f"data:image/{subtype.lower()};base64,{b64_data}"
                        )

                # 如果所有参考图都不可用，则显式返回失败，让上层根据配置决定是否走纯文生图兜底
                if not image_payloads:
                    return AIResponse(
                        success=False,
                        error="没有可用的参考图用于图生图",
                        provider=self.name,
                        model=model or ark_model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.IMAGE_TO_IMAGE,
                    )

                # 2) 组装 Ark 请求体（单图=字符串，多图=数组）
                #    对齐官方文档：参考图数量 + 最终生成图片数量 ≤ 15
                effective_size = size or "2K"
                max_images = max(1, int(n) if n and n > 0 else 1)
                try:
                    total_refs = len(image_payloads)
                    remaining = 15 - total_refs
                    if remaining < 1:
                        # 参考图已经占满或超出上限时，强制只生成 1 张，交由模型内部裁剪
                        max_images = 1
                    else:
                        max_images = min(max_images, remaining)
                except Exception:
                    # 计算失败时保持原始 max_images，交由服务端做进一步约束
                    pass

                request_data: Dict[str, Any] = {
                    "model": ark_model,
                    "prompt": prompt or "",
                    "image": image_payloads[0] if len(image_payloads) == 1 else image_payloads,
                    "size": effective_size,
                    "response_format": "url",
                    "watermark": kwargs.pop("watermark", False),
                    # 图生图场景下统一使用非流式输出，简化上游处理逻辑
                    "stream": False,
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
                last_error = e
                if "handler is closed" in str(e).lower() and attempt == 0:
                    await self._initialize_client()
                    continue
                break

        return AIResponse(
            success=False,
            error=self.format_error(last_error) if last_error else "图生图失败",
            provider=self.name,
            model=model or ark_model,
            task_type=AITaskType.SCENE_GENERATION,
            model_type=AIModelType.IMAGE_TO_IMAGE,
        )
    
    async def generate_video(
        self,
        prompt: str | None = None,
        image_url: str | None = None,
        model: str | None = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "720p",
        end_image_url: str | None = None,
        ratio: str | None = None,
        watermark: bool | None = None,
        seed: int | None = None,
        camera_fixed: bool | None = None,
        service_tier: str | None = None,
        execution_expires_after: int | None = None,
        return_last_frame: bool | None = None,
        **kwargs,
    ) -> AIResponse:
        """使用火山方舟 Video Generation API（Seedance）生成视频（异步轮询）"""
        try:
            client = await self.get_client()

            ark_model = (model or "").strip() or "doubao-seedance-1-0-pro-250528"
            normalized = ark_model.lower()
            if normalized.startswith("volcengine-video"):
                ark_model = "doubao-seedance-1-0-pro-250528"
            # 兼容业务侧使用 Seedream 图生视频别名（内部仍调用 Seedance 视频生成 API）
            if normalized.startswith("seedream-i2v"):
                if normalized in {"seedream-i2v-fast", "seedream-i2v-pro-fast"}:
                    ark_model = "doubao-seedance-1-0-pro-fast-251015"
                elif normalized in {"seedream-i2v-lite"}:
                    ark_model = "doubao-seedance-1-0-lite-i2v-250428"
                else:
                    ark_model = "doubao-seedance-1-0-pro-250528"

            # Ark 支持通过在提示词后追加 --[parameters] 控制输出规格
            # 参考 docs/api/volcengine-video.md：--rs/--rt/--dur/--fps/--wm/--seed/--cf
            import re

            def _contains_flag(text: str, flag: str) -> bool:
                return re.search(rf"(^|\\s){re.escape(flag)}(\\s|$)", text) is not None

            def _normalize_resolution_flag(value: str | None) -> str | None:
                if not value:
                    return None
                v = str(value).strip().lower()
                if v in {"480p", "720p", "1080p"}:
                    return v
                # 兼容常见的 WxH 输入（例如 1280x720 / 1920x1080）
                if "1080" in v or "1088" in v:
                    return "1080p"
                if "720" in v:
                    return "720p"
                if "480" in v:
                    return "480p"
                return None

            base_prompt = (prompt or "").strip() or "生成一段符合描述的视频"
            flags: list[str] = []

            rs = _normalize_resolution_flag(resolution)
            if rs and not _contains_flag(base_prompt, "--rs"):
                flags.append(f"--rs {rs}")

            rt = (ratio or "").strip()
            if rt and not (_contains_flag(base_prompt, "--rt") or _contains_flag(base_prompt, "--ratio")):
                flags.append(f"--rt {rt}")

            # duration: 2~12 秒（参考文档）
            dur = int(duration or 5)
            dur = max(2, min(dur, 12))
            if not _contains_flag(base_prompt, "--dur"):
                flags.append(f"--dur {dur}")

            fps_int = int(fps or 24)
            if fps_int != 24:
                fps_int = 24
            if not _contains_flag(base_prompt, "--fps"):
                flags.append(f"--fps {fps_int}")

            if watermark is not None and not _contains_flag(base_prompt, "--wm"):
                flags.append(f"--wm {'true' if watermark else 'false'}")

            if seed is not None and not _contains_flag(base_prompt, "--seed"):
                flags.append(f"--seed {int(seed)}")

            if camera_fixed is not None and not _contains_flag(base_prompt, "--cf"):
                flags.append(f"--cf {'true' if camera_fixed else 'false'}")

            final_prompt = base_prompt
            if flags:
                final_prompt = f"{base_prompt} {' '.join(flags)}"

            content: list[dict[str, Any]] = [
                {"type": "text", "text": final_prompt},
            ]
            if image_url:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                        "role": "first_frame",
                    }
                )
            if end_image_url:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": end_image_url},
                        "role": "last_frame",
                    }
                )

            request_data: dict[str, Any] = {"model": ark_model, "content": content}
            if service_tier:
                request_data["service_tier"] = service_tier
            if execution_expires_after is not None:
                request_data["execution_expires_after"] = int(execution_expires_after)
            if return_last_frame is not None:
                request_data["return_last_frame"] = bool(return_last_frame)
            # 兜底：允许透传未来新增参数（不覆盖已有字段）
            for key, value in (kwargs or {}).items():
                if key in request_data:
                    continue
                request_data[key] = value

            create_resp = await client.post(
                f"{self.base_url}/contents/generations/tasks",
                json=request_data,
            )
            create_resp.raise_for_status()
            create_data = create_resp.json() if create_resp.content else {}
            if isinstance(create_data, dict) and create_data.get("error"):
                err = create_data.get("error") or {}
                return AIResponse(
                    success=False,
                    error=f"火山引擎视频生成错误: {err.get('message') or err.get('code') or 'Unknown error'}",
                    provider=self.name,
                    model=ark_model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO,
                )

            task_id = (
                (create_data.get("id") if isinstance(create_data, dict) else None)
                or (create_data.get("task_id") if isinstance(create_data, dict) else None)
            )
            if not task_id and isinstance(create_data, dict):
                nested = create_data.get("data")
                if isinstance(nested, dict):
                    task_id = nested.get("id") or nested.get("task_id")

            if not task_id:
                return AIResponse(
                    success=False,
                    error="火山引擎视频生成响应缺少任务ID",
                    provider=self.name,
                    model=ark_model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO,
                    metadata={"raw": create_data},
                )

            result = await self._poll_task_status(
                str(task_id),
                max_attempts=120,
                delay=3,
            )
            if not result:
                return AIResponse(
                    success=False,
                    error="视频生成任务失败或超时",
                    provider=self.name,
                    model=ark_model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO,
                    metadata={"task_id": task_id},
                )

            content_out = result.get("content") or {}
            video_url = (
                content_out.get("video_url")
                or content_out.get("videoUrl")
                or content_out.get("url")
                or result.get("video_url")
                or result.get("videoUrl")
                or result.get("url")
            )
            thumbnail_url = (
                content_out.get("thumbnail_url")
                or content_out.get("cover_image_url")
                or content_out.get("cover_url")
                or content_out.get("poster_url")
            )
            last_frame_url = content_out.get("last_frame_url") or content_out.get(
                "lastFrameUrl"
            )

            if not video_url:
                return AIResponse(
                    success=False,
                    error="火山引擎视频生成成功但未返回视频URL",
                    provider=self.name,
                    model=ark_model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO,
                    metadata={"task_id": task_id, "raw": result},
                )

            return AIResponse(
                success=True,
                data={
                    "video_url": video_url,
                    "thumbnail_url": thumbnail_url,
                    "duration": dur,
                    "last_frame_url": last_frame_url,
                },
                provider=self.name,
                model=ark_model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO
                if image_url
                else AIModelType.TEXT_TO_VIDEO,
                metadata={
                    "task_id": task_id,
                    "prompt": final_prompt,
                    "duration": dur,
                    "fps": fps_int,
                    "resolution": rs or resolution,
                    "ratio": rt or None,
                    "watermark": watermark,
                    "seed": seed,
                    "camera_fixed": camera_fixed,
                    "service_tier": service_tier,
                },
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=(model or "doubao-seedance-1-0-pro-250528"),
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO
                if image_url
                else AIModelType.TEXT_TO_VIDEO,
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
        task_type: str | None = None,
        max_attempts: int = 60,
        delay: int = 3
    ) -> Optional[Dict[str, Any]]:
        """轮询火山方舟内容生成任务状态（Video Generation API）"""
        client = await self.get_client()

        for attempt in range(max_attempts):
            try:
                response = await client.get(
                    f"{self.base_url}/contents/generations/tasks/{task_id}",
                )
                response.raise_for_status()

                data = response.json() if response.content else {}
                if not isinstance(data, dict):
                    return None

                status = str(data.get("status") or "").lower()

                if status == "succeeded":
                    return data
                if status in {"failed", "canceled", "cancelled"}:
                    return None
                if status in {"queued", "running", "processing", "pending"}:
                    await asyncio.sleep(delay)
                    continue

                # 未知状态：直接退出，避免死循环
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
