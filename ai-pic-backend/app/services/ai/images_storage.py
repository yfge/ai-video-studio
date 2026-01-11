from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

import httpx
from app.core.config import settings
from app.services.storage.oss_service import oss_service


class ImageStorageMixin:
    async def _download_image(
        self, image_data: Any, ip_name: str, category: str
    ) -> str:
        """处理图像数据（URL或base64）并保存到本地，失败抛异常并保留原因。"""
        import base64
        import uuid
        from urllib.parse import unquote

        import aiofiles
        from app.utils.url_utils import normalize_presigned_url

        # 生成唯一文件名
        file_extension = ".png"  # OpenAI DALL-E默认返回PNG
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # 确保目录存在
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        local_file_path = os.path.join(upload_dir, unique_filename)

        if not isinstance(image_data, str):
            resolved: str | None = None
            if isinstance(image_data, dict):
                for key in ("url", "image_url", "image", "src"):
                    value = image_data.get(key)
                    if isinstance(value, str) and value:
                        resolved = value
                        break
            if resolved is None:
                raise TypeError(
                    f"image_data must be a string URL or data URL, got {type(image_data).__name__}"
                )
            image_data = resolved

        # 判断是base64数据还是URL
        if image_data.startswith("data:image"):
            # 处理base64数据
            self.logger.info("处理base64图像数据")
            base64_data = image_data.split(",")[1]  # 移除data:image/png;base64,前缀
            image_bytes = base64.b64decode(base64_data)

            # 直接保存base64数据
            async with aiofiles.open(local_file_path, "wb") as f:
                await f.write(image_bytes)
            self.logger.info("base64 图像已保存到: %s", local_file_path)
            return local_file_path

        # 处理URL，增加重试并输出具体错误
        normalized_url = unquote(image_data) if "%25" in image_data else image_data
        normalized_url = normalize_presigned_url(normalized_url)
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                self.logger.info(
                    "下载图像URL (attempt %s): %s...",
                    attempt + 1,
                    normalized_url[:100],
                )
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(normalized_url, timeout=60.0)
                    response.raise_for_status()

                async with aiofiles.open(local_file_path, "wb") as f:
                    await f.write(response.content)

                self.logger.info("图像已保存到: %s", local_file_path)
                return local_file_path
            except Exception as exc:  # pragma: no cover - network failures
                last_error = exc
                self.logger.warning(
                    "图像下载失败 attempt=%s url=%s err=%s",
                    attempt + 1,
                    normalized_url,
                    exc,
                )
                if attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))

        raise RuntimeError(f"图像处理失败: {last_error}")

    async def _upload_local_image_to_oss(
        self,
        local_file_path: str,
        *,
        prefix: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """将本地已下载的图片上传至 OSS，失败则抛出异常。"""
        if not oss_service:
            raise RuntimeError("OSS 服务未配置，无法上传图像")

        try:
            with open(local_file_path, "rb") as f:
                file_content = f.read()
        except Exception as exc:  # pragma: no cover - IO guard
            raise RuntimeError(f"读取本地图像失败: {exc}") from exc

        filename = os.path.basename(local_file_path)
        oss_result = await oss_service.upload_file_content(
            file_content=file_content,
            filename=filename,
            file_type="image",
            prefix=prefix,
            metadata=metadata,
        )
        if not oss_result or not oss_result.get("success"):
            raise RuntimeError(f"OSS 上传失败: {oss_result}")
        return oss_result

    async def _persist_local_image(
        self,
        local_file_path: str,
        *,
        prefix: str,
        metadata: Optional[Dict[str, Any]] = None,
        require_upload: bool = False,
    ) -> Dict[str, Any]:
        """
        将已存在的本地图像文件持久化（计算相对路径、可选上传 OSS）。

        供不同来源的图像复用：包括 AI 生成后下载到本地的文件，以及用户直接上传落盘的文件。
        """
        file_size = os.path.getsize(local_file_path)
        filename = os.path.basename(local_file_path)
        relative_path = f"/uploads/{filename}"

        oss_result = None
        oss_url = None
        if oss_service:
            try:
                oss_result = await self._upload_local_image_to_oss(
                    local_file_path,
                    prefix=prefix,
                    metadata=metadata or {},
                )
                # 当 require_upload 为 True 时，任何非成功结果都视为失败并抛出异常；
                # 否则记录告警并回退到本地路径。
                success = bool(oss_result.get("success"))
                file_url = oss_result.get("file_url")
                if success and file_url:
                    oss_url = file_url
                    self.logger.info(
                        "CDN 上传成功 | filename=%s object_key=%s url=%s prefix=%s",
                        filename,
                        oss_result.get("object_key"),
                        file_url,
                        prefix,
                    )
                elif require_upload:
                    raise RuntimeError(f"OSS 上传失败: {oss_result}")
                else:
                    self.logger.warning(
                        "OSS 上传未返回可用URL，使用本地路径 | filename=%s result=%s",
                        filename,
                        oss_result,
                    )
            except Exception as exc:
                if require_upload:
                    raise
                self.logger.warning("OSS 上传异常，使用本地路径: %s", exc)
        elif require_upload:
            raise RuntimeError("OSS 未配置，无法上传图像")
        else:
            self.logger.info(
                "OSS/CDN 未配置，使用本地路径 | filename=%s path=%s",
                filename,
                relative_path,
            )

        return {
            "local_file_path": local_file_path,
            "relative_path": relative_path,
            "file_size": file_size,
            "filename": filename,
            "oss_url": oss_url,
            "oss_upload": oss_result,
        }

    async def _persist_generated_image(
        self,
        image_data: str,
        *,
        ip_name: str,
        category: str,
        prefix: str,
        metadata: Optional[Dict[str, Any]] = None,
        require_upload: bool = False,
    ) -> Dict[str, Any]:
        """下载/保存生成图像，并在配置 OSS 时上传，返回路径与元数据。"""
        local_file_path = await self._download_image(image_data, ip_name, category)

        return await self._persist_local_image(
            local_file_path,
            prefix=prefix,
            metadata=metadata,
            require_upload=require_upload,
        )

    async def persist_uploaded_image(
        self,
        file_bytes: bytes,
        original_filename: str,
        *,
        prefix: str,
        metadata: Optional[Dict[str, Any]] = None,
        require_upload: bool = False,
    ) -> Dict[str, Any]:
        """
        持久化用户上传的图像文件：先写入本地 uploads，再根据配置上传到 OSS。

        返回结构与 _persist_generated_image 保持一致，便于上层统一处理。
        """
        import uuid
        from pathlib import Path

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        ext = Path(original_filename).suffix or ".png"
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        local_file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        with open(local_file_path, "wb") as f:
            f.write(file_bytes)

        return await self._persist_local_image(
            local_file_path,
            prefix=prefix,
            metadata=metadata,
            require_upload=require_upload,
        )
