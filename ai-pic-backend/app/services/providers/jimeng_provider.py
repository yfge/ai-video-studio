"""
即梦(JiMeng)服务提供商

专注于图像生成和图像处理功能
"""

import asyncio
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
from .image_param_utils import normalize_image_params, size_to_dimensions


class JimengProvider(BaseProvider):
    """即梦服务提供商"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.jimeng.ai/v1"

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [AIModelType.TEXT_TO_IMAGE, AIModelType.IMAGE_TO_IMAGE]

    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                model_id="jimeng-sd-v1.5",
                name="即梦 Stable Diffusion 1.5",
                description="基于SD1.5的高质量图像生成",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "style_control", "high_detail"],
                metadata={
                    "ui": {
                        "size_options": ["1024x1024"],
                        "aspect_ratio_options": ["1:1", "3:4", "4:3", "16:9", "9:16"],
                        "supports_aspect_ratio": False,
                        "supports_reference_image": False,
                    }
                },
            ),
            ModelInfo(
                model_id="jimeng-sdxl",
                name="即梦 SDXL",
                description="更大模型，更高质量输出",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "ultra_high_quality", "realistic"],
                metadata={
                    "ui": {
                        "size_options": ["1024x1024"],
                        "aspect_ratio_options": ["1:1", "3:4", "4:3", "16:9", "9:16"],
                        "supports_aspect_ratio": False,
                        "supports_reference_image": False,
                    }
                },
            ),
            ModelInfo(
                model_id="jimeng-anime",
                name="即梦动漫风格",
                description="专门优化的动漫风格图像生成",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "anime_style", "character_design"],
                metadata={
                    "ui": {
                        "size_options": ["1024x1024"],
                        "aspect_ratio_options": ["1:1", "3:4", "4:3", "16:9", "9:16"],
                        "supports_aspect_ratio": False,
                        "supports_reference_image": False,
                    }
                },
            ),
            ModelInfo(
                model_id="jimeng-img2img",
                name="即梦图生图",
                description="基于参考图像的风格转换",
                model_type=AIModelType.IMAGE_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["image_to_image", "style_transfer", "inpainting"],
                metadata={
                    "ui": {
                        "size_options": ["1024x1024"],
                        "aspect_ratio_options": ["1:1", "3:4", "4:3", "16:9", "9:16"],
                        "supports_aspect_ratio": False,
                        "supports_reference_image": True,
                    }
                },
            ),
        ]

    async def _initialize_client(self):
        """初始化HTTP客户端"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate_text(
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """即梦不支持文本生成"""
        return AIResponse(
            success=False,
            error="即梦不支持纯文本生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    async def generate_image(
        self,
        prompt: str,
        model: str = "jimeng-sdxl",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.5,
        seed: int = -1,
        negative_prompt: str = "",
        style: str = "realistic",
        **kwargs,
    ) -> AIResponse:
        """使用即梦生成图像"""
        try:
            size_value = kwargs.pop("size", None)
            try:
                normalized_size, _, _ = normalize_image_params(
                    self.name, model, size_value, None
                )
            except ValueError as exc:
                return AIResponse(
                    success=False,
                    error=str(exc),
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                )
            if normalized_size:
                dims = size_to_dimensions(normalized_size)
                if dims:
                    width, height = dims

            client = await self.get_client()

            request_data = {
                "model": model,
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": cfg_scale,
                "style": style,
                **kwargs,
            }

            if negative_prompt:
                request_data["negative_prompt"] = negative_prompt

            if seed != -1:
                request_data["seed"] = seed

            response = await client.post(
                f"{self.base_url}/images/generations", json=request_data
            )
            response.raise_for_status()

            data = response.json()

            # 即梦可能返回任务ID需要轮询，或直接返回结果
            if "task_id" in data:
                # 异步任务，需要轮询
                task_id = data["task_id"]
                result = await self._poll_task_status(task_id)
                if result:
                    return AIResponse(
                        success=True,
                        data={"images": result.get("images", [])},
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.PORTRAIT_GENERATION,
                        model_type=AIModelType.TEXT_TO_IMAGE,
                        metadata={
                            "task_id": task_id,
                            "width": width,
                            "height": height,
                            "steps": steps,
                            "cfg_scale": cfg_scale,
                            "seed": result.get("seed"),
                            "style": style,
                        },
                    )
            elif "images" in data:
                # 直接返回结果
                return AIResponse(
                    success=True,
                    data={"images": data["images"]},
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                    metadata={
                        "width": width,
                        "height": height,
                        "steps": steps,
                        "cfg_scale": cfg_scale,
                        "seed": data.get("seed"),
                        "style": style,
                    },
                )

            return AIResponse(
                success=False,
                error="图像生成响应格式错误",
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

    async def image_to_image(
        self,
        image_url: str,
        prompt: str = None,
        model: str = "jimeng-img2img",
        strength: float = 0.75,
        steps: int = 20,
        cfg_scale: float = 7.5,
        seed: int = -1,
        **kwargs,
    ) -> AIResponse:
        """即梦图生图"""
        try:
            client = await self.get_client()

            request_data = {
                "model": model,
                "init_image": image_url,
                "strength": strength,
                "steps": steps,
                "cfg_scale": cfg_scale,
                **kwargs,
            }

            if prompt:
                request_data["prompt"] = prompt

            if seed != -1:
                request_data["seed"] = seed

            response = await client.post(
                f"{self.base_url}/images/img2img", json=request_data
            )
            response.raise_for_status()

            data = response.json()

            if "task_id" in data:
                task_id = data["task_id"]
                result = await self._poll_task_status(task_id)
                if result:
                    return AIResponse(
                        success=True,
                        data={"images": result.get("images", [])},
                        provider=self.name,
                        model=model,
                        task_type=AITaskType.SCENE_GENERATION,
                        model_type=AIModelType.IMAGE_TO_IMAGE,
                        metadata={
                            "task_id": task_id,
                            "init_image": image_url,
                            "strength": strength,
                            "steps": steps,
                            "cfg_scale": cfg_scale,
                            "seed": result.get("seed"),
                        },
                    )
            elif "images" in data:
                return AIResponse(
                    success=True,
                    data={"images": data["images"]},
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.SCENE_GENERATION,
                    model_type=AIModelType.IMAGE_TO_IMAGE,
                    metadata={
                        "init_image": image_url,
                        "strength": strength,
                        "steps": steps,
                        "cfg_scale": cfg_scale,
                        "seed": data.get("seed"),
                    },
                )

            return AIResponse(
                success=False,
                error="图生图响应格式错误",
                provider=self.name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.SCENE_GENERATION,
                model_type=AIModelType.IMAGE_TO_IMAGE,
            )

    async def _poll_task_status(
        self, task_id: str, max_attempts: int = 30, delay: int = 2
    ) -> Optional[Dict[str, Any]]:
        """轮询任务状态"""
        client = await self.get_client()

        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{self.base_url}/tasks/{task_id}")
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                if status == "completed":
                    return data.get("result")
                elif status == "failed":
                    return None
                elif status in ["pending", "running"]:
                    await asyncio.sleep(delay)
                    continue
                else:
                    return None

            except Exception as e:
                print(f"轮询即梦任务状态失败 (尝试 {attempt + 1}): {e}")
                await asyncio.sleep(delay)

        return None

    async def get_styles(self) -> AIResponse:
        """获取可用的风格列表"""
        try:
            client = await self.get_client()

            response = await client.get(f"{self.base_url}/styles")
            response.raise_for_status()

            data = response.json()

            return AIResponse(
                success=True,
                data=data.get("styles", []),
                provider=self.name,
                model="styles",
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="styles",
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )
