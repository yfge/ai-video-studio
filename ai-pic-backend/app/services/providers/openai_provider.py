"""
OpenAI服务提供商

支持GPT系列文本生成和DALL-E系列图像生成
"""

import httpx
import json
from typing import List, Optional, Dict, Any
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig

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
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )
    
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
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            # 优先使用 OpenAI 的 response_format json_schema（如可用）
            if json_schema:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": json_schema.get("name", "response"),
                        "schema": json_schema.get("schema", json_schema)
                    }
                }
            else:
                # 尝试要求JSON对象（在不提供schema的情况下）
                # 注意：部分模型支持 {"type":"json_object"}
                if kwargs.get("force_json_object"):
                    payload["response_format"] = {"type": "json_object"}

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
            
            # 下载原图像
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            
            files = {
                "image": ("image.png", image_response.content, "image/png")
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
