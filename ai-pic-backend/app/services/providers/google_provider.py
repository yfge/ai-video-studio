"""
Google AI / Gemini 文本与图像生成提供商

文档参考：
- 文本生成：docs/api/google-text-api.md
- 图像生成（文/图生图）：https://ai.google.dev/gemini-api/docs/image-generation
"""

import json
import base64
from typing import Any, Dict, List, Optional

import httpx
from app.core.logging import get_logger

from .base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)

logger = get_logger(__name__)


class GoogleProvider(BaseProvider):
    """Google Gemini 文本生成"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # aiplatform.googleapis.com 或代理网关，通过 base_url 支持自定义
        # 统一去掉末尾 /，避免后续拼接路径出现 //
        self.base_url = (config.base_url or "https://generativelanguage.googleapis.com").rstrip("/")
        # publishers/google/models/{model_id}:{method}
        self.default_model = config.default_model or "gemini-3-pro-preview"
        # text 模型只需要 API key

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
        ]

    @property
    def available_models(self) -> List[ModelInfo]:
        # 提供一组静态兜底模型，确保远端列表不可用时仍可选择 Google 文生文模型
        return [
            ModelInfo(
                model_id=self.default_model,
                name="Gemini 3 Pro (preview)",
                description="Google Gemini 3 Pro 文本与推理模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=65535,
                capabilities=["text_generation", "analysis", "reasoning"],
            ),
            ModelInfo(
                model_id="gemini-1.5-pro-latest",
                name="Gemini 1.5 Pro (stable)",
                description="Gemini 1.5 Pro 通用推理模型（稳定版兜底）",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=1048576,
                capabilities=["text_generation", "analysis", "reasoning"],
            ),
            ModelInfo(
                model_id="gemini-1.5-flash-latest",
                name="Gemini 1.5 Flash (fast)",
                description="Gemini 1.5 Flash 高速通用模型（稳定版兜底）",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=2097152,
                capabilities=["text_generation", "analysis"],
            ),
            ModelInfo(
                model_id="gemini-1.0-pro",
                name="Gemini 1.0 Pro",
                description="Gemini 1.0 Pro 文本模型（兼容旧配置）",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=30720,
                capabilities=["text_generation", "analysis"],
            ),
            ModelInfo(
                model_id="gemini-2.0-flash-exp",
                name="Gemini 2.0 Flash (image exp)",
                description="Gemini Flash 试验性图片生成模型，支持文生图与图生图能力",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpeg"],
                capabilities=["text_to_image", "image_to_image"],
            ),
            ModelInfo(
                model_id="gemini-2.5-flash-image",
                name="Gemini 2.5 Flash Image",
                description="Gemini 2.5 Flash 快速图片生成模型，支持文/图生图",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpeg"],
                capabilities=["text_to_image", "image_to_image"],
            ),
            ModelInfo(
                model_id="gemini-3-pro-image-preview",
                name="Gemini 3 Pro Image Preview",
                description="Gemini 3 Pro 专业级图片生成模型（预览版），支持文/图生图",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpeg"],
                capabilities=["text_to_image", "image_to_image"],
            ),
        ]

    def _supports_type(self, model: ModelInfo, model_type: Optional[AIModelType]) -> bool:
        if not model_type:
            return True
        if model.model_type == model_type:
            return True
        caps = [c.lower() for c in (model.capabilities or [])]
        if model_type == AIModelType.IMAGE_TO_IMAGE and "image_to_image" in caps:
            return True
        return False

    def _fallback_models(self, model_type: Optional[AIModelType]) -> List[ModelInfo]:
        models = self.available_models
        if model_type:
            models = [m for m in models if self._supports_type(m, model_type)]
        return models

    def _normalize_model_id(self, raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        return raw.split("/")[-1]

    def _supported_methods(self, item: Dict[str, Any]) -> List[str]:
        methods = item.get("supportedGenerationMethods") or item.get("supported_generation_methods") or []
        return [m.lower() for m in methods if isinstance(m, str)]

    def _infer_model_type(self, item: Dict[str, Any]) -> AIModelType:
        methods = self._supported_methods(item)
        if "generateimage" in methods:
            return AIModelType.TEXT_TO_IMAGE
        return AIModelType.TEXT_GENERATION

    def _infer_capabilities(self, item: Dict[str, Any]) -> List[str]:
        methods = self._supported_methods(item)
        caps: List[str] = []
        if any(m in methods for m in ["generatecontent", "generatetext"]):
            caps.append("text_generation")
        if "generateimage" in methods:
            caps.append("text_to_image")
            caps.append("image_to_image")
        if not caps:
            caps.append("text_generation")
        return caps

    def _from_payload(
        self,
        server_models: List[Dict[str, Any]],
        model_type: Optional[AIModelType],
    ) -> List[ModelInfo]:
        models: List[ModelInfo] = []
        for item in server_models:
            if not isinstance(item, dict):
                continue
            mid = self._normalize_model_id(item.get("name") or item.get("id"))
            if not mid:
                continue
            mtype = self._infer_model_type(item)
            if mtype not in self.supported_model_types:
                continue
            caps = self._infer_capabilities(item)
            if model_type and not (
                mtype == model_type
                or (model_type == AIModelType.IMAGE_TO_IMAGE and "image_to_image" in caps)
            ):
                continue
            models.append(
                ModelInfo(
                    model_id=mid,
                    name=item.get("displayName") or item.get("title") or mid,
                    description=item.get("description") or f"Google model {mid}",
                    model_type=mtype,
                    capabilities=caps,
                )
            )
        return models

    def _dedupe(self, models: List[ModelInfo]) -> List[ModelInfo]:
        """Remove duplicate model_ids while preserving order."""
        seen = set()
        unique: List[ModelInfo] = []
        for m in models:
            if m.model_id in seen:
                continue
            seen.add(m.model_id)
            unique.append(m)
        return unique

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """仅调用官方 Generative Language models 列表，失败时回退静态列表。"""
        fallback = self._fallback_models(model_type)
        if not self.config.api_key:
            return fallback

        client = await self.get_client()
        if client is None:
            return fallback

        # 始终尊重配置的 base_url（可为官方域名或代理网关）
        google_base = self.base_url or "https://generativelanguage.googleapis.com"
        try:
            resp = await client.get(
                f"{google_base.rstrip('/')}/v1beta/models",
                params={"key": self.config.api_key},
            )
            body_preview = resp.text[:500]
            if resp.status_code >= 400:
                logger.debug(
                    "GoogleProvider GLM list models failed status=%s url=%s body=%s",
                    resp.status_code,
                    f"{google_base.rstrip('/')}/v1beta/models",
                    body_preview,
                )
                return fallback
            payload = resp.json()
            server_models = payload.get("models") or []
            models = self._from_payload(server_models, model_type)
            return self._dedupe(models) or fallback
        except Exception as exc:
            # 避免在未正确配置或网络异常时大量刷屏，记录为调试信息并回退静态列表
            logger.debug("GoogleProvider list models exception: %s", exc)
            return fallback

    def _clean_model_id(self, model: Optional[str]) -> Optional[str]:
        """清理模型 ID，去掉可能的 provider 前缀（如 'google:'）"""
        if not model:
            return None
        # 去掉 provider 前缀（例如 "google:gemini-3-pro-image-preview" -> "gemini-3-pro-image-preview"）
        if ":" in model:
            return model.split(":", 1)[1]
        return model

    def _parse_images(self, payload: Dict[str, Any]) -> List[str]:
        """从 generateContent 响应中提取 inlineData 图片，统一输出 data:image/...;base64,..."""
        images: List[str] = []
        for cand in payload.get("candidates") or []:
            if not isinstance(cand, dict):
                continue
            content = cand.get("content") or {}
            parts = content.get("parts") or []
            for part in parts:
                if not isinstance(part, dict):
                    continue
                inline = part.get("inlineData") or part.get("inline_data")
                if not isinstance(inline, dict):
                    continue
                data = inline.get("data")
                if not data:
                    continue
                mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                prefix = f"data:{mime};base64,"
                if data.startswith(prefix):
                    images.append(data)
                else:
                    images.append(prefix + data)
        return images

    def _prefer_http_for_download(self, url: str) -> str:
        """下载参考图时优先使用 http，规避 HTTPS 证书校验失败。"""
        if isinstance(url, str) and url.lower().startswith("https://"):
            return "http://" + url[len("https://"):]
        return url

    async def _fetch_inline_image(self, image_url: str) -> Dict[str, str]:
        """下载参考图并转换为 inlineData 结构，供 generateImage 使用。"""
        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            trust_env=False,
            follow_redirects=True,
        ) as client:
            download_url = self._prefer_http_for_download(image_url)
            resp = await client.get(download_url)
            resp.raise_for_status()
            mime = resp.headers.get("Content-Type", "image/png")
            b64 = base64.b64encode(resp.content).decode("ascii")
            return {"mimeType": mime, "data": b64}

    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        **kwargs: Any,
    ) -> AIResponse:
        """调用 Gemini 图像生成 API（文生图）。"""
        if not self.config.api_key:
            return AIResponse(
                success=False,
                error="GoogleProvider 未配置 API Key",
                provider=self.name,
                model=model or self.default_model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        # 默认优先使用正式的图片模型，其次回退到实验模型
        # 清理模型 ID，去掉可能的 provider 前缀
        model_id = self._clean_model_id(model) or "gemini-2.5-flash-image"
        endpoint = f"{self.base_url.rstrip('/')}/v1beta/models/{model_id}:generateContent"

        client = await self.get_client()
        if client is None:
            return AIResponse(
                success=False,
                error="Google 客户端未初始化",
                provider=self.name,
                model=model_id,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        body = {
            "model": model_id,
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }
        # 根据文档，将图片配置放在 generationConfig.imageConfig 下
        # 必须包含 responseModalities 来启用图像生成
        aspect_ratio = kwargs.get("aspect_ratio")
        image_size = kwargs.get("image_size") or kwargs.get("size")
        image_config: Dict[str, Any] = {}
        if aspect_ratio:
            image_config["aspectRatio"] = aspect_ratio
        if image_size:
            image_config["imageSize"] = image_size

        generation_config: Dict[str, Any] = {
            # 使用 ["TEXT", "IMAGE"] 以兼容所有 Gemini 图像生成模型
            "responseModalities": ["TEXT", "IMAGE"]
        }
        if image_config:
            generation_config["imageConfig"] = image_config
        body["generationConfig"] = generation_config

        try:
            resp = await client.post(endpoint, json=body)
            resp.raise_for_status()
            payload = resp.json()
            images = self._parse_images(payload)
            if not images:
                return AIResponse(
                    success=False,
                    error="GoogleProvider 图像生成响应为空",
                    provider=self.name,
                    model=model_id,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                )
            return AIResponse(
                success=True,
                data={"images": images},
                provider=self.name,
                model=model_id,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
                metadata={"aspect_ratio": aspect_ratio},
            )
        except Exception as exc:
            return AIResponse(
                success=False,
                error=self.format_error(exc),
                provider=self.name,
                model=model_id,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str = None,
        model: str = None,
        **kwargs: Any,
    ) -> AIResponse:
        """调用 Gemini 图像生成 API（图生图，使用参考图 inlineData）。"""
        if not self.config.api_key:
            return AIResponse(
                success=False,
                error="GoogleProvider 未配置 API Key",
                provider=self.name,
                model=model or "gemini-2.5-flash-image",
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        # 清理模型 ID，去掉可能的 provider 前缀
        model_id = self._clean_model_id(model) or "gemini-2.5-flash-image"
        endpoint = f"{self.base_url.rstrip('/')}/v1beta/models/{model_id}:generateContent"

        client = await self.get_client()
        if client is None:
            return AIResponse(
                success=False,
                error="Google 客户端未初始化",
                provider=self.name,
                model=model_id,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        try:
            # 优先使用上游预加载好的 base64_images（data:image/...;base64,...），
            # 这样可以支持多张参考图且避免在 Provider 内部重复下载。
            base64_images: List[str] = kwargs.pop("base64_images", []) or []
            parts: List[Dict[str, Any]] = []
            if prompt:
                parts.append({"text": prompt})

            if base64_images:
                # 最多支持 14 张参考图，超出的在上游已被截断
                for data_url in base64_images[:14]:
                    if not isinstance(data_url, str) or not data_url:
                        continue
                    mime_type = "image/png"
                    b64_data = data_url
                    if data_url.startswith("data:"):
                        # 形如 data:image/png;base64,AAAA...
                        try:
                            header, b64_data = data_url.split(",", 1)
                            header = header[5:]  # 去掉 "data:"
                            if ";" in header:
                                mime_type = header.split(";", 1)[0] or "image/png"
                            elif header:
                                mime_type = header
                        except ValueError:
                            # 回退到原始字符串
                            b64_data = data_url
                    parts.append(
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_data,
                            }
                        }
                    )
            else:
                # 兼容直接传入 URL 的调用路径（例如未经过 AIServiceManager 预加载的场景）
                inline_image = await self._fetch_inline_image(image_url)
                parts.append({"inlineData": inline_image})

            body: Dict[str, Any] = {
                "model": model_id,
                "contents": [{"role": "user", "parts": parts}],
            }
            aspect_ratio = kwargs.get("aspect_ratio")
            image_size = kwargs.get("image_size") or kwargs.get("size")
            image_config: Dict[str, Any] = {}
            if aspect_ratio:
                image_config["aspectRatio"] = aspect_ratio
            if image_size:
                image_config["imageSize"] = image_size

            generation_config: Dict[str, Any] = {
                # 使用 ["TEXT", "IMAGE"] 以兼容所有 Gemini 图像生成模型
                "responseModalities": ["TEXT", "IMAGE"]
            }
            if image_config:
                generation_config["imageConfig"] = image_config
            body["generationConfig"] = generation_config

            resp = await client.post(endpoint, json=body)
            resp.raise_for_status()
            payload = resp.json()
            images = self._parse_images(payload)
            if not images:
                return AIResponse(
                    success=False,
                    error="GoogleProvider 图生图响应为空",
                    provider=self.name,
                    model=model_id,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.IMAGE_TO_IMAGE,
                )
            return AIResponse(
                success=True,
                data={"images": images},
                provider=self.name,
                model=model_id,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
                metadata={"reference_image": image_url},
            )
        except Exception as exc:
            return AIResponse(
                success=False,
                error=self.format_error(exc),
                provider=self.name,
                model=model_id,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

    async def _initialize_client(self):
        """初始化 HTTP 客户端"""
        if not self.config.api_key:
            # 没有配置 key 时，让调用方走 fallback
            self._client = None  # type: ignore[assignment]
            return

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.config.api_key,
            "x-goog-api-client": "ai-video-studio-gemini",
        }
        self._client = httpx.AsyncClient(timeout=self.config.timeout, headers=headers)

    async def _stream_generate_content(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        body: Dict[str, Any],
    ):
        """使用 Gemini 流式接口并拼接文本。"""
        text_parts: List[str] = []
        usage: Dict[str, Any] = {}

        async with client.stream("POST", endpoint, json=body) as resp:
            if resp.status_code >= 400:
                detail = await resp.aread()
                raise httpx.HTTPStatusError(
                    message=f"Google stream status {resp.status_code} body={detail.decode(errors='ignore')}",
                    request=resp.request,
                    response=resp,
                )

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                except Exception:
                    continue
                for candidate in event.get("candidates", []):
                    content = candidate.get("content") or {}
                    for part in content.get("parts", []):
                        t = part.get("text")
                        if isinstance(t, str):
                            text_parts.append(t)
                if event.get("usageMetadata"):
                    usage = event["usageMetadata"]

        return "".join(text_parts).strip(), usage

    async def generate_text(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: str | None = None,
        json_schema: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AIResponse:
        """使用 Gemini 生成文本（非流式）"""
        if not self.config.api_key:
            return AIResponse(
                success=False,
                error="Google API key 未配置",
                provider=self.name,
                model=model or self.default_model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

        client = await self.get_client()
        if client is None:
            return AIResponse(
                success=False,
                error="Google 客户端未初始化",
                provider=self.name,
                model=model or self.default_model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )

        model_id = model or self.default_model
        stream = bool(kwargs.pop("stream", True))
        method = "streamGenerateContent" if stream else "generateContent"
        endpoint = (
            f"{self.base_url.rstrip('/')}/v1/publishers/google/models/{model_id}:{method}"
            f"?key={self.config.api_key}"
        )
        if stream:
            endpoint = f"{endpoint}&alt=sse"

        # 组装 request.json，简化版参考 docs/api/google-text-api.md
        contents: List[Dict[str, Any]] = [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
        if system_prompt:
            contents.insert(
                0,
                {
                    "role": "system",
                    "parts": [{"text": system_prompt}],
                },
            )

        generation_config: Dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens

        if json_schema:
            # 暂不强行映射 json_schema，交由上层按文本解析
            generation_config["responseMimeType"] = "application/json"

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
            # safetySettings 可以后续按需要透传，先留空
        }

        try:
            if stream:
                try:
                    full_text, usage_meta = await self._stream_generate_content(client, endpoint, body)
                    if full_text:
                        return AIResponse(
                            success=True,
                            data=full_text,
                            provider=self.name,
                            model=model_id,
                            task_type=AITaskType.STORY_GENERATION,
                            model_type=AIModelType.TEXT_GENERATION,
                            usage={
                                "prompt_tokens": usage_meta.get("promptTokenCount") if usage_meta else None,
                                "completion_tokens": usage_meta.get("candidatesTokenCount") if usage_meta else None,
                                "total_tokens": usage_meta.get("totalTokenCount") if usage_meta else None,
                            },
                            metadata={"raw": usage_meta, "stream": True},
                        )
                    logger.warning("Google stream returned empty content; falling back to non-stream.")
                except Exception as stream_err:  # noqa: BLE001
                    logger.warning("Google stream failed, falling back to non-stream: %s", stream_err, exc_info=True)

            resp = await client.post(endpoint.replace("&alt=sse", "") if stream else endpoint, json=body)
            resp.raise_for_status()
            data = resp.json()

            # 解析 candidates[0].content.parts[*].text
            text_parts: List[str] = []
            for candidate in data.get("candidates", []):
                content = candidate.get("content") or {}
                for part in content.get("parts", []):
                    t = part.get("text")
                    if isinstance(t, str):
                        text_parts.append(t)
            full_text = "\n".join(text_parts).strip()

            if not full_text:
                return AIResponse(
                    success=False,
                    error="Gemini 返回为空",
                    provider=self.name,
                    model=model_id,
                    task_type=AITaskType.STORY_GENERATION,
                    model_type=AIModelType.TEXT_GENERATION,
                )

            usage = data.get("usageMetadata", {})

            return AIResponse(
                success=True,
                data=full_text,
                provider=self.name,
                model=model_id,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
                usage={
                    "prompt_tokens": usage.get("promptTokenCount"),
                    "completion_tokens": usage.get("candidatesTokenCount"),
                    "total_tokens": usage.get("totalTokenCount"),
                },
                metadata={"raw": data},
            )
        except Exception as e:  # noqa: BLE001
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model or self.default_model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
            )
