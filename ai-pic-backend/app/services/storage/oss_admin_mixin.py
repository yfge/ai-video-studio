from __future__ import annotations

from typing import Any

import oss2


class OSSAdminMixin:
    def delete_object(self, object_key: str) -> dict[str, Any]:
        """删除OSS对象"""
        try:
            self.bucket.delete_object(object_key)
            return {
                "success": True,
                "object_key": object_key,
                "message": "删除成功",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "error": f"删除失败: {exc}",
                "object_key": object_key,
            }

    def get_signed_url(self, object_key: str, expires: int = 3600, method: str = "GET") -> str:
        """生成签名URL"""
        try:
            return self.bucket.sign_url(method, object_key, expires)
        except Exception as exc:  # noqa: BLE001
            raise Exception(f"生成签名URL失败: {exc}") from exc

    def list_objects(
        self, prefix: str = "", max_keys: int = 100, marker: str = ""
    ) -> dict[str, Any]:
        """列出对象"""
        try:
            result = self.bucket.list_objects(prefix=prefix, max_keys=max_keys, marker=marker)
            objects = []
            for obj in result.object_list:
                objects.append(
                    {
                        "key": obj.key,
                        "size": obj.size,
                        "last_modified": obj.last_modified.isoformat(),
                        "etag": obj.etag,
                        "url": f"{self.domain}/{obj.key}",
                    }
                )
            return {
                "success": True,
                "objects": objects,
                "is_truncated": result.is_truncated,
                "next_marker": result.next_marker,
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"列出对象失败: {exc}"}

    def get_object_info(self, object_key: str) -> dict[str, Any]:
        """获取对象信息"""
        try:
            head_result = self.bucket.head_object(object_key)
            metadata = {
                key.replace("x-oss-meta-", ""): value
                for key, value in head_result.headers.items()
                if key.startswith("x-oss-meta-")
            }
            return {
                "success": True,
                "object_key": object_key,
                "size": head_result.content_length,
                "content_type": head_result.content_type,
                "last_modified": head_result.last_modified.isoformat(),
                "etag": head_result.etag,
                "metadata": metadata,
                "url": f"{self.domain}/{object_key}",
            }
        except oss2.exceptions.NoSuchKey:
            return {"success": False, "error": "对象不存在", "object_key": object_key}
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "error": f"获取对象信息失败: {exc}",
                "object_key": object_key,
            }

