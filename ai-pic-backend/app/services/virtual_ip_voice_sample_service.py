"""
Virtual IP voice sample service.

Uploads preview audio to OSS and persists the sample URL to voice_config.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.exceptions import ConfigurationError, ExternalServiceError, ValidationError
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.services.storage.oss_service import oss_service


class VirtualIPVoiceSampleService:
    """Service for persisting voice preview samples for Virtual IPs."""

    def __init__(self, repository: VirtualIPRepository):
        self.repository = repository

    async def save_sample_by_id(
        self,
        ip_id: int,
        current_user: User,
        source_url: str,
        preview_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        virtual_ip = self.repository.get_owned_by_id(ip_id, current_user)
        return await self._save_sample(
            virtual_ip=virtual_ip,
            source_url=source_url,
            preview_text=preview_text,
        )

    async def save_sample_by_business_id(
        self,
        business_id: str,
        current_user: User,
        source_url: str,
        preview_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        virtual_ip = self.repository.get_owned_by_business_id(business_id, current_user)
        return await self._save_sample(
            virtual_ip=virtual_ip,
            source_url=source_url,
            preview_text=preview_text,
        )

    async def _save_sample(
        self,
        virtual_ip: VirtualIP,
        source_url: str,
        preview_text: Optional[str],
    ) -> Dict[str, Any]:
        if not source_url:
            raise ValidationError("试听URL不能为空", field="source_url")
        if not oss_service:
            raise ConfigurationError("OSS服务未配置")

        voice_config = (
            virtual_ip.voice_config if isinstance(virtual_ip.voice_config, dict) else {}
        )
        provider = voice_config.get("provider") or ""
        model = voice_config.get("model") or voice_config.get("tts_model") or ""
        voice_id = voice_config.get("voice_id") or ""

        prefix = f"virtual-ips/{virtual_ip.business_id or virtual_ip.id}/voice-samples"
        upload_result = await oss_service.upload_from_url(
            url=source_url,
            file_type="audio",
            prefix=prefix,
            metadata={
                "virtual_ip_id": str(virtual_ip.id),
                "virtual_ip_business_id": virtual_ip.business_id or "",
                "voice_provider": provider,
                "voice_model": model,
                "voice_id": voice_id,
            },
        )
        if not upload_result.get("success"):
            raise ExternalServiceError("OSS", upload_result.get("error") or "上传失败")

        sample_url = upload_result.get("file_url")
        if not sample_url:
            raise ExternalServiceError("OSS", "未返回文件地址")

        sample_payload = {
            "sample_url": sample_url,
            "sample_source_url": source_url,
            "sample_object_key": upload_result.get("object_key"),
            "sample_updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if preview_text is not None:
            sample_payload["sample_text"] = preview_text
        voice_config.update(sample_payload)
        virtual_ip.voice_config = voice_config
        self.repository.session.add(virtual_ip)
        self.repository.session.commit()
        self.repository.session.refresh(virtual_ip)

        return {
            "sample_url": sample_url,
            "sample_source_url": source_url,
            "voice_config": voice_config,
        }
