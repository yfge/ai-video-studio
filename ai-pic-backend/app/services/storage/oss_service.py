import logging
from urllib.parse import urlparse

import oss2

from app.core.config import settings

from .oss_admin_mixin import OSSAdminMixin
from .oss_backup_mixin import OSSBackupMixin
from .oss_upload_mixin import OSSUploadMixin


class OSSService(OSSUploadMixin, OSSAdminMixin, OSSBackupMixin):
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


# 创建全局OSS服务实例
try:
    oss_service = OSSService()
except ValueError as e:
    print(f"OSS服务初始化失败: {e}")
    oss_service = None
