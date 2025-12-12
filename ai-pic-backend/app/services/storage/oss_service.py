"""
阿里云OSS存储服务

提供文件上传、下载、管理等功能
"""

import asyncio
import logging
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx
import oss2

from app.core.config import settings


class OSSService:
    """阿里云OSS存储服务"""

    def __init__(self):
        # 基本配置，统一做strip去掉可能的空白字符，避免签名失败
        raw_access_key_id = getattr(settings, "ALIYUN_ACCESS_KEY_ID", None)
        raw_access_key_secret = getattr(settings, "ALIYUN_ACCESS_KEY_SECRET", None)
        raw_endpoint = getattr(settings, "ALIYUN_OSS_ENDPOINT", None)
        raw_bucket = getattr(settings, "ALIYUN_OSS_BUCKET", None)
        raw_domain = getattr(settings, "ALIYUN_OSS_DOMAIN", None)

        self.access_key_id = (
            raw_access_key_id.strip() if isinstance(raw_access_key_id, str) else raw_access_key_id
        )
        self.access_key_secret = (
            raw_access_key_secret.strip() if isinstance(raw_access_key_secret, str) else raw_access_key_secret
        )
        self.endpoint = raw_endpoint.strip() if isinstance(raw_endpoint, str) else raw_endpoint
        self.bucket_name = raw_bucket.strip() if isinstance(raw_bucket, str) else raw_bucket
        self.domain = raw_domain.strip() if isinstance(raw_domain, str) else raw_domain
        self.logger = logging.getLogger(__name__)

        if not all([self.access_key_id, self.access_key_secret, self.endpoint, self.bucket_name]):
            raise ValueError("阿里云OSS配置不完整，请检查环境变量")

        # 规范化 endpoint，保证后续 SDK 使用一致
        parsed = urlparse(self.endpoint)
        if parsed.scheme:
            endpoint_host = parsed.netloc or parsed.path
        else:
            endpoint_host = parsed.path or parsed.netloc
        self._endpoint_host = endpoint_host

        # 使用官方 SDK 负责签名，避免手写签名出错导致 403
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(auth, f"https://{self._endpoint_host}", self.bucket_name)

        # 设置默认访问域名
        if not self.domain:
            self.domain = f"https://{self.bucket_name}.{self._endpoint_host}"
    
    def _generate_object_key(self, file_type: str, original_filename: str = None, prefix: str = None) -> str:
        """生成OSS对象键名"""
        timestamp = datetime.now().strftime("%Y%m%d/%H%M%S")
        
        # 生成随机字符串
        import uuid
        random_str = str(uuid.uuid4())[:8]
        
        # 确定文件扩展名
        if original_filename:
            file_ext = Path(original_filename).suffix
        elif file_type == "image":
            file_ext = ".png"
        elif file_type == "video":
            file_ext = ".mp4"
        elif file_type == "audio":
            file_ext = ".mp3"
        else:
            file_ext = ""
        
        # 构建对象键
        if prefix:
            return f"{prefix}/{file_type}/{timestamp}/{random_str}{file_ext}"
        else:
            return f"ai-generated/{file_type}/{timestamp}/{random_str}{file_ext}"
    
    def _get_content_type(self, filename: str) -> str:
        """获取文件MIME类型"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    async def upload_from_url(
        self,
        url: str,
        file_type: str = "image",
        prefix: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        从URL下载文件并上传到OSS。

        仍然使用 httpx 下载远端内容，但真正上传交给官方 SDK，
        避免手写签名导致 SignatureDoesNotMatch。
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
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
        except Exception as e:
            return {
                "success": False,
                "error": f"上传失败: {str(e)}",
                "original_url": url,
            }
    
    async def upload_file_content(
        self,
        file_content: bytes,
        filename: str,
        file_type: str = "image",
        prefix: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        上传文件内容到OSS。

        使用 oss2.Bucket.put_object，由 SDK 负责签名，避免 403 SignatureDoesNotMatch。
        """
        try:
            # 生成对象键
            object_key = self._generate_object_key(file_type, filename, prefix)

            # 获取内容类型（目前不直接写入 Content-Type 头，避免部分环境下签名不一致）
            content_type = self._get_content_type(filename)

            # 准备 headers（仅 ASCII 的自定义元数据）
            headers: Dict[str, str] = {}
            if metadata:
                for key, value in metadata.items():
                    value_str = str(value)
                    try:
                        value_str.encode("ascii")
                        # OSS 对 header 名有一些约束，这里统一把 metadata key 中的下划线替换为短横线，
                        # 避免客户端和服务端在 canonicalization 上出现差异。
                        safe_key = str(key).replace("_", "-")
                        headers[f"x-oss-meta-{safe_key}"] = value_str
                    except UnicodeEncodeError:
                        self.logger.warning("跳过包含非ASCII字符的metadata: %s=%s", key, value_str)

            # oss2 是同步接口，这里放到线程池里避免阻塞事件循环
            def _put():
                return self.bucket.put_object(object_key, file_content, headers=headers)

            result = await asyncio.to_thread(_put)

            # 理论上 put_object 异常会直接抛出，这里双保险检查一下 status
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

        except Exception as e:
            return {
                "success": False,
                "error": f"上传失败: {str(e)}",
                "filename": filename,
            }
    
    async def upload_multiple_urls(
        self,
        urls: List[str],
        file_type: str = "image",
        prefix: str = None,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """批量上传URL文件"""
        tasks = []
        for url in urls:
            task = self.upload_from_url(url, file_type, prefix, metadata)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": f"上传失败: {str(result)}",
                    "original_url": urls[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def delete_object(self, object_key: str) -> Dict[str, Any]:
        """删除OSS对象"""
        try:
            self.bucket.delete_object(object_key)
            return {
                "success": True,
                "object_key": object_key,
                "message": "删除成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"删除失败: {str(e)}",
                "object_key": object_key
            }
    
    def get_signed_url(
        self, 
        object_key: str, 
        expires: int = 3600,
        method: str = 'GET'
    ) -> str:
        """生成签名URL"""
        try:
            signed_url = self.bucket.sign_url(method, object_key, expires)
            return signed_url
        except Exception as e:
            raise Exception(f"生成签名URL失败: {str(e)}")
    
    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 100,
        marker: str = ""
    ) -> Dict[str, Any]:
        """列出对象"""
        try:
            result = self.bucket.list_objects(prefix=prefix, max_keys=max_keys, marker=marker)
            
            objects = []
            for obj in result.object_list:
                objects.append({
                    "key": obj.key,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat(),
                    "etag": obj.etag,
                    "url": f"{self.domain}/{obj.key}"
                })
            
            return {
                "success": True,
                "objects": objects,
                "is_truncated": result.is_truncated,
                "next_marker": result.next_marker
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"列出对象失败: {str(e)}"
            }
    
    def get_object_info(self, object_key: str) -> Dict[str, Any]:
        """获取对象信息"""
        try:
            head_result = self.bucket.head_object(object_key)
            
            return {
                "success": True,
                "object_key": object_key,
                "size": head_result.content_length,
                "content_type": head_result.content_type,
                "last_modified": head_result.last_modified.isoformat(),
                "etag": head_result.etag,
                "metadata": {k.replace('x-oss-meta-', ''): v for k, v in head_result.headers.items() if k.startswith('x-oss-meta-')},
                "url": f"{self.domain}/{object_key}"
            }
            
        except oss2.exceptions.NoSuchKey:
            return {
                "success": False,
                "error": "对象不存在",
                "object_key": object_key
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取对象信息失败: {str(e)}",
                "object_key": object_key
            }
    
    async def copy_and_backup(
        self,
        source_urls: List[str],
        backup_prefix: str = "backup",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """复制并备份文件"""
        results = {
            "success_count": 0,
            "failed_count": 0,
            "results": []
        }
        
        for url in source_urls:
            try:
                # 确定文件类型
                parsed_url = urlparse(url)
                path = Path(parsed_url.path)
                file_ext = path.suffix.lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    file_type = "image"
                elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                    file_type = "video"
                elif file_ext in ['.mp3', '.wav', '.flac', '.aac']:
                    file_type = "audio"
                else:
                    file_type = "other"
                
                # 上传文件
                result = await self.upload_from_url(
                    url=url,
                    file_type=file_type,
                    prefix=backup_prefix,
                    metadata=metadata
                )
                
                if result["success"]:
                    results["success_count"] += 1
                else:
                    results["failed_count"] += 1
                
                results["results"].append(result)
                
            except Exception as e:
                results["failed_count"] += 1
                results["results"].append({
                    "success": False,
                    "error": f"处理失败: {str(e)}",
                    "original_url": url
                })
        
        return results


# 创建全局OSS服务实例
try:
    oss_service = OSSService()
except ValueError as e:
    print(f"OSS服务初始化失败: {e}")
    oss_service = None
