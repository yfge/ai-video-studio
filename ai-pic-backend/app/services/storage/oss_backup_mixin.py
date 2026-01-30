from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class OSSBackupMixin:
    async def copy_and_backup(
        self,
        source_urls: list[str],
        backup_prefix: str = "backup",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """复制并备份文件"""
        results: dict[str, Any] = {"success_count": 0, "failed_count": 0, "results": []}

        for url in source_urls:
            try:
                parsed_url = urlparse(url)
                path = Path(parsed_url.path)
                file_ext = path.suffix.lower()

                if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                    file_type = "image"
                elif file_ext in [".mp4", ".avi", ".mov", ".wmv"]:
                    file_type = "video"
                elif file_ext in [".mp3", ".wav", ".flac", ".aac"]:
                    file_type = "audio"
                else:
                    file_type = "other"

                result = await self.upload_from_url(
                    url=url,
                    file_type=file_type,
                    prefix=backup_prefix,
                    metadata=metadata,
                )

                if result.get("success"):
                    results["success_count"] += 1
                else:
                    results["failed_count"] += 1

                results["results"].append(result)
            except Exception as exc:  # noqa: BLE001
                results["failed_count"] += 1
                results["results"].append(
                    {
                        "success": False,
                        "error": f"处理失败: {exc}",
                        "original_url": url,
                    }
                )

        return results
