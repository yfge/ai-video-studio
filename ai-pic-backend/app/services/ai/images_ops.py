from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class ImageOpsMixin:
    async def generate_image(
        self, prompt: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """生成图片（保持向后兼容）"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")

        payload = {"prompt": prompt, "parameters": parameters or {}}

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
            print(f"AI服务调用失败: {exc}")
            return None
