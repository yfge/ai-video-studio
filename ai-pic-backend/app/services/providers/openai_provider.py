"""
OpenAI服务提供商

支持GPT系列文本生成和DALL-E系列图像生成
"""

import httpx
import json
from typing import List, Optional
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig
from app.core.logging import get_logger
from typing import Dict, Any

logger = get_logger(__name__)



def _reload_openai_params(model_id: str, temperature: float) -> Dict[str, Any]:
    if model_id.startswith("gpt-5.1"):
        return {
            "reasoning_effort": "none",
            "temperature": 1,
        }
    if model_id.startswith("gpt-5-pro"):
        return {
            "reasoning_effort": "none",
        }

    if model_id.startswith("gpt-5"):
        return {
            "reasoning_effort": "minimal",
            "temperature": 1,
        }
    return {
        "temperature": temperature,
    }


def _supports_structured_outputs(model_id: str) -> bool:
    """判断模型是否支持 response_format.json_schema 严格模式"""
    lid = (model_id or "").lower()
    prefixes = [
        "gpt-4.1",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-audio",
        "gpt-4o-realtime",
        "o3",
        "o1",
    ]
    return any(lid.startswith(p) for p in prefixes)
class OpenAIProvider(BaseProvider):
    """OpenAI服务提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
    
    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_GENERATION,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_UNDERSTANDING,
            AIModelType.IMAGE_TO_IMAGE,
        ]
    
    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            # GPT模型
            ModelInfo(
                model_id="gpt-4o",
                name="GPT-4o",
                description="最新的GPT-4优化版本，支持多模态",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=128000,
                supported_formats=["text", "image"],
                capabilities=["text_generation", "image_understanding", "code_generation"]
            ),
            ModelInfo(
                model_id="gpt-4-turbo",
                name="GPT-4 Turbo",
                description="GPT-4的增强版本，更快更便宜",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=128000,
                capabilities=["text_generation", "code_generation", "analysis"]
            ),
            ModelInfo(
                model_id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                description="快速且经济的文本生成模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=16385,
                capabilities=["text_generation", "conversation", "summarization"]
            ),
            # DALL-E模型
            ModelInfo(
                model_id="dall-e-3",
                name="DALL-E 3",
                description="最新的图像生成模型，高质量输出",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpeg"],
                capabilities=["text_to_image", "high_resolution", "detailed"]
            ),
            ModelInfo(
                model_id="dall-e-2",
                name="DALL-E 2",
                description="经典的图像生成模型，快速生成",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpeg"],
                capabilities=["text_to_image", "variations", "inpainting", "image_to_image"]
            )
        ]

    def _fallback_models(self, model_type: Optional[AIModelType]) -> List[ModelInfo]:
        models = self.available_models
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        return models

    def _infer_model_type(self, model_id: str) -> AIModelType:
        """粗略推断模型类型，优先识别 DALL-E 图像模型，其余视为文本模型。"""
        lid = model_id.lower()
        if "dall-e" in lid or "image" in lid:
            return AIModelType.TEXT_TO_IMAGE
        return AIModelType.TEXT_GENERATION

    def _infer_capabilities(self, model_id: str) -> List[str]:
        lid = model_id.lower()
        if "dall-e" in lid or "image" in lid:
            return ["text_to_image"]
        caps = ["text_generation"]
        if "gpt" in lid or "o" in lid:
            caps.append("analysis")
        return caps

    async def fetch_remote_models(
        self,
        model_type: Optional[AIModelType] = None,
    ) -> List[ModelInfo]:
        """
        使用 OpenAI 官方 /v1/models 列表作为信息源，结合当前维护的白名单。

        - 先调用 /v1/models 拿到所有模型 id
        - 直接根据模型 id 粗略推断类型，尽量返回官方最新列表
        """
        fallback = self._fallback_models(model_type)
        try:
            client = await self.get_client()
            if client is None:
                return fallback
            resp = await client.get(f"{self.base_url}/models")
            resp.raise_for_status()
            data = resp.json()
            server_models = data.get("data", []) if isinstance(data, dict) else []
            models: List[ModelInfo] = []
            for item in server_models:
                if not isinstance(item, dict):
                    continue
                mid = item.get("id")
                if not mid:
                    continue
                mtype = self._infer_model_type(mid)
                if model_type and mtype != model_type:
                    continue
                models.append(
                    ModelInfo(
                        model_id=mid,
                        name=item.get("name") or mid,
                        description=item.get("description") or f"OpenAI model {mid}",
                        model_type=mtype,
                        capabilities=self._infer_capabilities(mid),
                    )
                )
            return models or fallback
        except Exception:
            # 出错时退回到静态列表
            return fallback
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def _stream_chat_completion(self, payload: Dict[str, Any], model: str):
        """使用OpenAI流式接口，逐步拼接内容。"""
        client = await self.get_client()
        if client is None:
            raise RuntimeError("OpenAI client not initialized")

        url = f"{self.base_url}/chat/completions"
        content_parts: list[str] = []
        usage: Dict[str, Any] = {}
        finish_reason: Optional[str] = None

        async with client.stream("POST", url, json=payload) as resp:
            if resp.status_code >= 400:
                detail = await resp.aread()
                raise httpx.HTTPStatusError(
                    message=f"OpenAI stream status {resp.status_code} body={detail.decode(errors='ignore')}",
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

        full_content = "".join(content_parts).strip()
        return full_content, usage, finish_reason
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "gpt-4o",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: str = None,
        json_schema: dict | None = None,
        **kwargs
    ) -> AIResponse:
        """使用GPT生成文本"""
        try:
            client = await self.get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                # "max_tokens": max_tokens,
                **kwargs
            }

            # 允许外部控制是否使用流式；默认开启
            stream = bool(payload.pop("stream", True))
            payload.update(_reload_openai_params(model, temperature))

            # 优先使用 OpenAI 的 response_format json_schema（如可用）
            if json_schema:
                if _supports_structured_outputs(model):
                    payload["response_format"] = {
                        "type": "json_schema",
                        "strict": True,
                        "json_schema": {
                            "name": json_schema.get("name", "response"),
                            "schema": json_schema.get("schema", json_schema),
                        },
                    }
                else:
                    payload["response_format"] = {"type": "json_object"}
            else:
                # 尝试要求JSON对象（在不提供schema的情况下）
                # 注意：部分模型支持 {"type":"json_object"}
                if kwargs.get("force_json_object"):
                    payload["response_format"] = {"type": "json_object"}

            # 流式优先，失败回落到普通请求
            if stream:
                try:
                    streamed_content, usage, finish_reason = await self._stream_chat_completion(
                        {**payload, "stream": True},
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
                            },
                        )
                    logger.warning("OpenAI stream returned empty content; falling back to non-stream.")
                except Exception as stream_err:  # noqa: BLE001
                    logger.warning("OpenAI stream failed, falling back to non-stream: %s", stream_err, exc_info=True)

            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
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
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0)
                }
            )
            
        except httpx.HTTPStatusError as e:
            detail = None
            try:
                detail = e.response.text
            except Exception:
                detail = None
            msg = self.format_error(e)
            if detail:
                msg = f"{msg}; body={detail}"
            logger.error("OpenAI generate_text HTTP %s: %s", e.response.status_code, detail, exc_info=True)
            return AIResponse(
                success=False,
                error=msg,
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION
            )
        except Exception as e:
            logger.error(f"OpenAI generate_text error: {e}", exc_info=True)
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
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
        **kwargs
    ) -> AIResponse:
        """使用DALL-E生成图像"""
        try:
            client = await self.get_client()
            
            # DALL-E 3参数
            request_data = {
                "model": model,
                "prompt": prompt,
                "n": n,
                "size": size
            }
            
            # DALL-E 3特有参数
            if model == "dall-e-3":
                request_data.update({
                    "quality": quality,
                    "style": style
                })
            
            response = await client.post(
                f"{self.base_url}/images/generations",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            images = data["data"]
            
            return AIResponse(
                success=True,
                data={
                    "images": [img["url"] for img in images],
                    "revised_prompt": images[0].get("revised_prompt") if model == "dall-e-3" else None
                },
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
                metadata={
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "count": len(images)
                }
            )
            
        except httpx.HTTPStatusError as e:
            detail = None
            try:
                detail = e.response.text
            except Exception:
                detail = None
            msg = self.format_error(e)
            if detail:
                msg = f"{msg}; body={detail}"
            logger.error("OpenAI generate_image HTTP %s: %s", e.response.status_code, detail, exc_info=True)
            return AIResponse(
                success=False,
                error=msg,
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
    
    async def understand_image(
        self, 
        image_url: str, 
        question: str = "请描述这张图片",
        model: str = "gpt-4o",
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """使用GPT-4V理解图像"""
        try:
            client = await self.get_client()
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ]
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return AIResponse(
                success=True,
                data=content,
                provider=self.name,
                model=model,
                task_type=AITaskType.CHARACTER_CREATION,
                model_type=AIModelType.IMAGE_UNDERSTANDING,
                usage=data.get("usage", {}),
                metadata={
                    "image_url": image_url,
                    "question": question
                }
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.CHARACTER_CREATION,
                model_type=AIModelType.IMAGE_UNDERSTANDING
            )
    
    async def image_to_image(
        self, 
        image_url: str, 
        prompt: str = None,
        model: str = "dall-e-2",
        size: str = "1024x1024",
        n: int = 1,
        **kwargs
    ) -> AIResponse:
        """DALL-E图像变换（仅DALL-E 2支持）"""
        if model != "dall-e-2":
            return AIResponse(
                success=False,
                error="图像变换仅DALL-E 2支持",
                provider=self.name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE
        )
        
        try:
            client = await self.get_client()
            
            # 支持 data:image;base64 或 URL
            image_bytes = None
            content_type = "image/png"
            base64_images: list[str] = kwargs.pop("base64_images", []) or []
            if base64_images and base64_images[0].startswith("data:image"):
                import base64

                header, b64_data = base64_images[0].split(",", 1)
                content_type = header.split(";")[0].split(":")[1] if ":" in header else "image/png"
                image_bytes = base64.b64decode(b64_data)
            else:
                image_response = await client.get(image_url)
                image_response.raise_for_status()
                content_type = image_response.headers.get("Content-Type", "image/png")
                image_bytes = image_response.content
            
            files = {
                "image": ("image.png", image_bytes, content_type or "image/png")
            }
            
            data = {
                "n": n,
                "size": size
            }
            
            if prompt:
                data["prompt"] = prompt
            
            # 创建新的客户端用于multipart请求
            form_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"Authorization": f"Bearer {self.config.api_key}"}
            )
            
            response = await form_client.post(
                f"{self.base_url}/images/variations",
                files=files,
                data=data
            )
            response.raise_for_status()
            
            result = response.json()
            images = result["data"]
            
            await form_client.aclose()
            
            return AIResponse(
                success=True,
                data={"images": [img["url"] for img in images]},
                provider=self.name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
                metadata={
                    "original_image": image_url,
                    "size": size,
                    "count": len(images)
                }
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE
            )
