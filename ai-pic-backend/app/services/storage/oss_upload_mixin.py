from __future__ import annotations

import asyncio
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


class OSSUploadMixin:
    def _generate_object_key(
        self,
        file_type: str,
        original_filename: str | None = None,
        prefix: str | None = None,
    ) -> str:
        """生成OSS对象键名"""
        timestamp = datetime.now().strftime("%Y%m%d/%H%M%S")
        random_str = str(uuid.uuid4())[:8]

        if original_filename:
            file_ext = Path(original_filename).suffix
            if not file_ext:
                file_ext = self._default_extension_for_type(file_type)
        elif file_type == "image":
            file_ext = ".png"
        else:
            file_ext = self._default_extension_for_type(file_type)

        if prefix:
            return f"{prefix}/{file_type}/{timestamp}/{random_str}{file_ext}"
        return f"ai-generated/{file_type}/{timestamp}/{random_str}{file_ext}"

    @staticmethod
    def _default_extension_for_type(file_type: str) -> str:
        if file_type == "video":
            return ".mp4"
        if file_type == "audio":
            return ".mp3"
        return ""

    def _get_content_type(self, filename: str) -> str:
        """获取文件MIME类型"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    async def upload_from_url(
        self,
        url: str,
        file_type: str = "image",
        prefix: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        从URL下载文件并上传到OSS。

        仍然使用 httpx 下载远端内容，但真正上传交给官方 SDK，
        避免手写签名导致 SignatureDoesNotMatch。
        """
        try:
            timeout = 180.0 if file_type == "video" else 60.0
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                file_content = response.content

            filename = Path(urlparse(url).path).name or None
            return await self.upload_file_content(
                file_content=file_content,
                filename=filename or "remote_file",
                file_type=file_type,
                prefix=prefix,
                metadata=metadata,
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "error": f"上传失败: {exc}",
                "original_url": url,
            }

    async def upload_file_content(
        self,
        file_content: bytes,
        filename: str,
        file_type: str = "image",
        prefix: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        上传文件内容到OSS。

        使用 oss2.Bucket.put_object，由 SDK 负责签名，避免 403 SignatureDoesNotMatch。
        """
        try:
            object_key = self._generate_object_key(file_type, filename, prefix)
            content_type = self._get_content_type(filename)

            headers: dict[str, str] = {}
            if metadata:
                for key, value in metadata.items():
                    value_str = str(value)
                    try:
                        value_str.encode("ascii")
                        safe_key = str(key).replace("_", "-")
                        headers[f"x-oss-meta-{safe_key}"] = value_str
                    except UnicodeEncodeError:
                        self.logger.warning(
                            "跳过包含非ASCII字符的metadata: %s=%s", key, value_str
                        )

            def _put():
                return self.bucket.put_object(object_key, file_content, headers=headers)

            result = await asyncio.to_thread(_put)

            status = getattr(result, "status", 200)
            if status >= 300:
                self.logger.warning(
                    "OSS 上传失败 | status=%s bucket=%s endpoint=%s object_key=%s",
                    status,
                    self.bucket_name,
                    self._endpoint_host,
                    object_key,
                )
                return {
                    "success": False,
                    "error": f"上传失败: status={status}",
                    "filename": filename,
                }

            file_url = f"{self.domain}/{object_key}"
            self.logger.info(
                "CDN 上传成功 | object_key=%s url=%s bytes=%s prefix=%s",
                object_key,
                file_url,
                len(file_content),
                prefix or "",
            )

            return {
                "success": True,
                "object_key": object_key,
                "file_url": file_url,
                "file_size": len(file_content),
                "content_type": content_type,
                "upload_time": datetime.now().isoformat(),
                "metadata": metadata or {},
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "error": f"上传失败: {exc}",
                "filename": filename,
            }

    async def upload_multiple_urls(
        self,
        urls: list[str],
        file_type: str = "image",
        prefix: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """批量上传URL文件"""
        tasks = [self.upload_from_url(url, file_type, prefix, metadata) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results: list[dict[str, Any]] = []
        for index, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "success": False,
                        "error": f"上传失败: {result}",
                        "original_url": urls[index],
                    }
                )
            else:
                processed_results.append(result)

        return processed_results
