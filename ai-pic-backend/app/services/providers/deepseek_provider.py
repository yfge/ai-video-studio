"""DeepSeek provider."""

from __future__ import annotations

from typing import List, Optional

import httpx

from .base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from .deepseek_models import (
    DEEPSEEK_BASE_URL,
    DEEPSEEK_DEFAULT_MODEL,
    DEEPSEEK_V4_PRO_MODEL,
    get_static_models,
    infer_capabilities,
    infer_model_type,
)
from .deepseek_text import generate_text as generate_deepseek_text


class DeepSeekProvider(BaseProvider):
    """DeepSeek service provider."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = _normalize_base_url(config.base_url)

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [AIModelType.TEXT_GENERATION]

    @property
    def available_models(self) -> List[ModelInfo]:
        return get_static_models()

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """Fetch DeepSeek models from /models, falling back to static V4 data."""
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
                model_info = self._model_info_from_remote(item, model_type)
                if model_info:
                    models.append(model_info)
            return models or fallback
        except Exception:
            return fallback

    async def _initialize_client(self):
        """Initialize the DeepSeek HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate_text(
        self,
        prompt: str,
        model: str = DEEPSEEK_DEFAULT_MODEL,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        system_prompt: str = None,
        **kwargs,
    ) -> AIResponse:
        """Generate text using DeepSeek V4."""
        client = await self.get_client()
        if client is None:
            return self._failure("DeepSeek client not initialized", model)
        return await generate_deepseek_text(
            client=client,
            base_url=self.base_url,
            provider_name=self.name,
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            system_prompt=system_prompt,
            format_error=self.format_error,
            **kwargs,
        )

    async def generate_image(
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """DeepSeek does not support image generation in this provider."""
        return AIResponse(
            success=False,
            error="DeepSeek不支持图像生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE,
        )

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        model: str = DEEPSEEK_V4_PRO_MODEL,
        **kwargs,
    ) -> AIResponse:
        """Generate code with DeepSeek V4 Pro."""
        system_prompt = f"""你是一个专业的{language}程序员。请根据用户的要求生成高质量的代码。
代码应该：
1. 遵循最佳实践
2. 包含必要的注释
3. 具有良好的可读性
4. 处理边界情况和错误"""
        return await self.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def solve_math(
        self,
        problem: str,
        model: str = DEEPSEEK_V4_PRO_MODEL,
        **kwargs,
    ) -> AIResponse:
        """Solve math problems with DeepSeek V4 Pro."""
        system_prompt = """你是一个数学专家。请仔细分析数学问题，提供详细的解题步骤和最终答案。
解答应该包括：
1. 问题分析
2. 解题思路
3. 详细步骤
4. 最终答案
5. 验证过程（如果适用）"""
        return await self.generate_text(
            prompt=problem,
            model=model,
            system_prompt=system_prompt,
            **kwargs,
        )

    async def analyze_text(
        self,
        text: str,
        analysis_type: str = "sentiment",
        model: str = DEEPSEEK_DEFAULT_MODEL,
        **kwargs,
    ) -> AIResponse:
        """Analyze text with DeepSeek."""
        analysis_prompts = {
            "sentiment": "请分析以下文本的情感倾向，包括积极、消极、中性程度：",
            "summary": "请总结以下文本的主要内容：",
            "keywords": "请提取以下文本的关键词和主题：",
            "structure": "请分析以下文本的结构和逻辑：",
            "style": "请分析以下文本的写作风格和特点：",
        }
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["sentiment"])
        return await self.generate_text(
            prompt=f"{prompt}\n\n{text}",
            model=model,
            **kwargs,
        )

    async def stream_generate_text(
        self,
        prompt: str,
        model: str = DEEPSEEK_DEFAULT_MODEL,
        **kwargs,
    ) -> AIResponse:
        """Generate text using the streaming DeepSeek path."""
        return await self.generate_text(prompt=prompt, model=model, **kwargs)

    def _fallback_models(
        self,
        model_type: Optional[AIModelType],
    ) -> List[ModelInfo]:
        models = self.available_models
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        return models

    def _model_info_from_remote(
        self,
        item: object,
        model_type: Optional[AIModelType],
    ) -> Optional[ModelInfo]:
        if not isinstance(item, dict):
            return None
        model_id = item.get("id") or item.get("model") or item.get("model_id")
        if not model_id:
            return None
        inferred_type = infer_model_type(str(model_id))
        if inferred_type not in self.supported_model_types:
            return None
        if model_type and inferred_type != model_type:
            return None
        return ModelInfo(
            model_id=str(model_id),
            name=item.get("name") or str(model_id),
            description=item.get("description") or f"DeepSeek model {model_id}",
            model_type=inferred_type,
            capabilities=infer_capabilities(str(model_id)),
        )

    def _failure(self, message: str, model: Optional[str]) -> AIResponse:
        return AIResponse(
            success=False,
            error=message,
            provider=self.name,
            model=model or DEEPSEEK_DEFAULT_MODEL,
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )


def _normalize_base_url(base_url: Optional[str]) -> str:
    normalized = (base_url or DEEPSEEK_BASE_URL).rstrip("/")
    if normalized == f"{DEEPSEEK_BASE_URL}/v1":
        return DEEPSEEK_BASE_URL
    return normalized
