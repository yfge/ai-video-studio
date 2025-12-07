"""
Google AI / Gemini 文本生成提供商

当前只接入文本生成能力，接口示例参考 docs/api/google-text-api.md：
- Endpoint: https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:{method}
- 默认模型: gemini-3-pro-preview
"""

from typing import Any, Dict, List, Optional

import httpx

from .base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)


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
        return [
            ModelInfo(
                model_id=self.default_model,
                name="Gemini 3 Pro (preview)",
                description="Google Gemini 3 Pro 文本与推理模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=65535,
                capabilities=["text_generation", "analysis", "reasoning"],
            )
        ]

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """
        Google Vertex AI 上的模型列表API依赖项目配置，当前仅使用 docs/api/google-text-api.md 中的推荐模型。

        因此 remote 与 static 一致，调用方仍然可以通过统一接口访问。
        """
        return await super().fetch_remote_models(model_type=model_type)

    async def _initialize_client(self):
        """初始化 HTTP 客户端"""
        if not self.config.api_key:
            # 没有配置 key 时，让调用方走 fallback
            self._client = None  # type: ignore[assignment]
            return

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-client": "ai-video-studio-gemini",
        }
        self._client = httpx.AsyncClient(timeout=self.config.timeout, headers=headers)

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
        method = "generateContent"
        endpoint = (
            f"{self.base_url}/v1/publishers/google/models/{model_id}:{method}"
            f"?key={self.config.api_key}"
        )

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
            resp = await client.post(endpoint, json=body)
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
