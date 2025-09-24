"""
存储服务模块

提供各种云存储服务的统一接口
"""

from .oss_service import oss_service, OSSService

__all__ = [
    "oss_service",
    "OSSService"
]