from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Optional

import httpx
from app.core.config import settings
from app.utils.model_utils import (
    DEFAULT_OPENAI_IMAGE_MODEL,
    canonicalize_openai_image_model,
    is_gpt_image_model,
)


class ImageProviderMixin:
    async def _generate_with_keling_image(
        self,
        prompt: str,
        style: str,
        category: str,
        model: str = "kling-v2-1",
        *,
        style_preset_id: str | None = None,
        style_spec: Any | None = None,
        aspect_ratio: str | None = None,
    ) -> Optional[str]:
        """使用可灵AI生成图像"""
        if not self.ai_manager:
            self.logger.warning("AI管理器未初始化，无法使用可灵AI")
            return None

        try:
            self.logger.info(f"使用可灵AI生成图像: {model}")

            response = await self.ai_manager.generate_image(
                prompt=prompt,
                width=1024,
                height=1024,
                style=style,
                style_preset_id=style_preset_id,
                style_spec=style_spec,
                model=model,
                prefer_provider="keling",
                aspect_ratio=aspect_ratio,
            )

            if response.success:
                images = response.data.get("images", [])
                if images:
                    image_url = images[0]
                    self.logger.info(
                        "可灵AI图像生成成功: %s...",
                        (
                            image_url[:100]
                            if isinstance(image_url, str)
                            else str(image_url)[:100]
                        ),
                    )
                    return image_url
                self.logger.error("可灵AI返回了空的图像列表")
                return None
            self.logger.error(f"可灵AI图像生成失败: {response.error}")
            return None

        except Exception as exc:
            self.logger.error(f"可灵AI图像生成异常: {exc}")
            return None

    async def _generate_with_openai_dalle(
        self,
        prompt: str,
        style: str,
        category: str,
        size: str | None = None,
        model: str | None = None,
        reference_images: list[str] | None = None,
    ) -> Optional[str]:
        """使用 OpenAI 图像模型生成图像"""
        if not self.openai_api_key:
            return None
        base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
        model_id = canonicalize_openai_image_model(model) or DEFAULT_OPENAI_IMAGE_MODEL

        try:
            async with httpx.AsyncClient() as client:
                if reference_images and is_gpt_image_model(model_id):
                    files = await self._build_openai_edit_files(
                        client, reference_images
                    )
                    response = await client.post(
                        f"{base_url.rstrip('/')}/images/edits",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        data={
                            "model": model_id,
                            "prompt": prompt[:32000],
                            "n": 1,
                            "size": size or "1024x1024",
                            "quality": "auto",
                        },
                        files=files,
                        timeout=120.0,
                    )
                    response.raise_for_status()
                    return self._first_openai_image_result(response.json())

                payload = {
                    "model": model_id,
                    "prompt": (
                        prompt[:32000]
                        if is_gpt_image_model(model_id)
                        else prompt[:4000]
                    ),
                    "n": 1,
                    "size": size or "1024x1024",
                }
                if is_gpt_image_model(model_id):
                    payload["quality"] = "auto"
                elif model_id == "dall-e-3":
                    payload.update(
                        {
                            "quality": "hd",
                            "style": (
                                style
                                if style in {"vivid", "natural"}
                                else ("natural" if style == "realistic" else "vivid")
                            ),
                            "response_format": "b64_json",
                        }
                    )
                else:
                    payload["response_format"] = "b64_json"

                response = await client.post(
                    f"{base_url.rstrip('/')}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=120.0 if is_gpt_image_model(model_id) else 60.0,
                )
                response.raise_for_status()
                result = response.json()

                image_result = self._first_openai_image_result(result)
                if image_result and image_result.startswith("data:image"):
                    self.logger.info(
                        "获取到OpenAI base64图像数据，长度: %s",
                        len(image_result),
                    )
                elif image_result:
                    self.logger.info(f"获取到OpenAI图像URL: {image_result[:100]}...")
                return image_result
        except Exception as exc:
            self.logger.error(f"OpenAI图像生成失败: {exc}")
            if hasattr(exc, "response"):
                try:
                    error_detail = exc.response.json()
                    self.logger.error(f"OpenAI API错误详情: {error_detail}")
                except Exception:
                    self.logger.error(f"OpenAI API响应: {exc.response.text}")
            return None

    async def _build_openai_edit_files(
        self,
        client: httpx.AsyncClient,
        reference_images: list[str],
    ) -> list[tuple[str, tuple[str, bytes, str]]]:
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for index, source in enumerate(reference_images):
            if not source:
                continue
            if source.startswith("data:image"):
                header, b64_data = source.split(",", 1)
                content_type = (
                    header.split(";")[0].split(":")[1] if ":" in header else "image/png"
                )
                image_bytes = base64.b64decode(b64_data)
            else:
                download_url = source
                if download_url.lower().startswith("https://"):
                    download_url = "http://" + download_url[len("https://") :]
                response = await client.get(download_url)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "image/png")
                image_bytes = response.content
            ext = (
                content_type.split("/", 1)[1].split(";", 1)[0]
                if "/" in content_type
                else "png"
            )
            files.append(
                ("image[]", (f"image-{index}.{ext}", image_bytes, content_type))
            )
        return files

    @staticmethod
    def _first_openai_image_result(result: dict[str, Any]) -> Optional[str]:
        data = result.get("data") or []
        if not data:
            return None
        first = data[0]
        if first.get("b64_json"):
            return f"data:image/png;base64,{first['b64_json']}"
        return first.get("url")

    async def _generate_with_stability(
        self, prompt: str, style: str, category: str
    ) -> Optional[str]:
        """使用Stability AI生成图像"""
        if not self.stability_api_key:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={
                        "Authorization": f"Bearer {self.stability_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "text_prompts": [{"text": prompt, "weight": 1}],
                        "cfg_scale": 7,
                        "height": 1024,
                        "width": 1024,
                        "samples": 1,
                        "steps": 30,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                # Stability AI返回base64编码的图像
                image_data = result["artifacts"][0]["base64"]
                # 这里需要将base64转换为文件并保存
                return await self._save_base64_image(image_data, "stability")
        except Exception as exc:
            print(f"Stability AI生成失败: {exc}")
            return None

    async def _generate_with_custom_image_service(
        self, prompt: str, style: str, category: str
    ) -> Optional[str]:
        """使用自定义AI服务生成图像"""
        if not self.base_url or not self.api_key:
            return None

        payload = {
            "prompt": prompt,
            "parameters": {
                "style": style,
                "category": category,
                "width": 1024,
                "height": 1024,
                "quality": "high",
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("image_url")
        except Exception as exc:
            print(f"自定义AI服务生成失败: {exc}")
            return None

    async def _save_base64_image(self, base64_data: str, source: str) -> str:
        """保存base64编码的图像"""
        import os

        # 解码base64数据
        image_bytes = base64.b64decode(base64_data)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_{source}_{timestamp}.png"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)

        # 保存文件
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # 返回相对路径
        return f"/uploads/{filename}"
