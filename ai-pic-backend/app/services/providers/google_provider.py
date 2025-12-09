"""
Google AI / Gemini 文本生成提供商

当前只接入文本生成能力，接口示例参考 docs/api/google-text-api.md：
- Endpoint: https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:{method}
- 默认模型: gemini-3-pro-preview
"""

import json
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
        # aiplatform.googleapis.com
        self.base_url = config.base_url or "https://aiplatform.googleapis.com"
        # publishers/google/models/{model_id}:{method}
        self.default_model = config.default_model or "gemini-3-pro-preview"
        # text 模型只需要 API key

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [AIModelType.TEXT_GENERATION]

    @property
    def available_models(self) -> List[ModelInfo]:
        # 提供一组静态兜底模型，确保在远端列表不可用时前端仍可选择多个 Google 文生文模型
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
        ]

    def _fallback_models(self, model_type: Optional[AIModelType]) -> List[ModelInfo]:
        models = self.available_models
        if model_type:
            models = [m for m in models if m.model_type == model_type]
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
            if model_type and mtype != model_type:
                continue
            models.append(
                ModelInfo(
                    model_id=mid,
                    name=item.get("displayName") or item.get("title") or mid,
                    description=item.get("description") or f"Google model {mid}",
                    model_type=mtype,
                    capabilities=self._infer_capabilities(item),
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

    async def _fetch_openai_style_models(
        self,
        model_type: Optional[AIModelType],
    ) -> List[ModelInfo]:
        """
        参考用户提供的实现：当 base_url 指向自定义代理时，使用 OpenAI 兼容的 /v1/models 拉取。
        """
        if not self.base_url:
            return []

        url = f"{self.base_url.rstrip('/')}/v1/models"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout, headers=headers) as client:
                resp = await client.get(url)
                body_preview = resp.text[:500]
                if resp.status_code >= 400:
                    logger.warning("GoogleProvider proxy list models failed status=%s body=%s", resp.status_code, body_preview)
                resp.raise_for_status()
                payload = resp.json()
        except Exception:
            return []

        items = payload.get("data") or payload.get("models") or []
        models: List[ModelInfo] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            mid = item.get("id") or item.get("model") or item.get("name")
            if not mid:
                continue
            mtype = self._infer_model_type({"supportedGenerationMethods": ["generateContent"]})
            if model_type and mtype != model_type:
                continue
            if mtype not in self.supported_model_types:
                continue
            models.append(
                ModelInfo(
                    model_id=mid,
                    name=item.get("displayName") or item.get("title") or item.get("name") or mid,
                    description=item.get("description") or f"Google model {mid}",
                    model_type=mtype,
                    capabilities=self._infer_capabilities({"supportedGenerationMethods": ["generateContent"]}),
                )
            )
        return models

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """调用 Vertex AI / Generative Language / 自定义代理模型列表，失败时回退静态列表。"""
        fallback = self._fallback_models(model_type)
        if not self.config.api_key:
            return fallback

        client = await self.get_client()
        if client is None:
            return fallback

        models: List[ModelInfo] = []

        # 0) 自定义代理：OpenAI 兼容 /v1/models（参考用户提供的实现）
        if self.base_url and "generativelanguage.googleapis.com" not in self.base_url and "aiplatform.googleapis.com" not in self.base_url:
            try:
                models.extend(await self._fetch_openai_style_models(model_type))
            except Exception:
                pass
            if models:
                return self._dedupe(models)

        # 1) Vertex AI (aiplatform)
        try:
            resp = await client.get(
                f"{self.base_url}/v1/models",
                params={"key": self.config.api_key},
            )
            body_preview = resp.text[:500]
            if resp.status_code >= 400:
                logger.warning("GoogleProvider Vertex list models failed status=%s body=%s", resp.status_code, body_preview)
            resp.raise_for_status()
            payload = resp.json()
            server_models = payload.get("models") or payload.get("data") or []
            models.extend(self._from_payload(server_models, model_type))
        except Exception:
            pass

        # 2) Generative Language API (generativelanguage.googleapis.com)
        try:
            google_base = self.base_url or "https://generativelanguage.googleapis.com"
            resp = await client.get(
                f"{google_base.rstrip('/')}/v1beta/models",
                params={"key": self.config.api_key},
            )
            body_preview = resp.text[:500]
            if resp.status_code >= 400:
                logger.warning("GoogleProvider GLM list models failed status=%s body=%s", resp.status_code, body_preview)
            resp.raise_for_status()
            payload = resp.json()
            server_models = payload.get("models") or []
            models.extend(self._from_payload(server_models, model_type))
        except Exception:
            pass

        return self._dedupe(models) or fallback

    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        **kwargs: Any,
    ) -> AIResponse:
        """GoogleProvider 当前未实现图像生成，返回未实现错误。"""
        return AIResponse(
            success=False,
            error="GoogleProvider does not support text-to-image",
            provider=self.name,
            model=model or (self.default_model if hasattr(self, "default_model") else "unknown"),
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def _initialize_client(self):
        """初始化 HTTP 客户端"""
        if not self.config.api_key:
            # 没有配置 key 时，让调用方走 fallback
            self._client = None  # type: ignore[assignment]
            return

        headers = {"Content-Type": "application/json"}
        # 自定义代理走 Bearer，其余走 Google API Key
        if self.base_url and "generativelanguage.googleapis.com" not in self.base_url and "aiplatform.googleapis.com" not in self.base_url:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        else:
            headers["x-goog-api-key"] = self.config.api_key
            headers["x-goog-api-client"] = "ai-video-studio-gemini"
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
        max_tokens: int = 2048,
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
            f"{self.base_url}/v1/publishers/google/models/{model_id}:{method}"
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

        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

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
