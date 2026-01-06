from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.services.storage.oss_service import oss_service


class SpeechGenerationMixin:
    async def generate_speech(
        self,
        text: str,
        voice_type: str = None,
        speed: float = 1.0,
        prefer_provider: str = None,
    ) -> Optional[Dict[str, Any]]:
        """生成语音"""
        try:
            response = await self.ai_manager.text_to_speech(
                text=text,
                voice_type=voice_type,
                speed=speed,
                prefer_provider=prefer_provider,
            )

            if response.success:
                original_audio_url = response.data.get("audio_url")

                # 自动上传音频到OSS
                audio_oss_result = None
                if original_audio_url and oss_service:
                    try:
                        audio_oss_result = await oss_service.upload_from_url(
                            url=original_audio_url,
                            file_type="audio",
                            prefix="ai-generated/audio",
                            metadata={
                                "text": (
                                    text[:100] + "..." if len(text) > 100 else text
                                ),  # 限制长度
                                "voice_type": voice_type or "default",
                                "speed": str(speed),
                                "provider": response.provider,
                                "model": response.model,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as exc:
                        print(f"音频OSS上传失败: {exc}")

                return {
                    "audio_url": (
                        audio_oss_result.get("file_url")
                        if audio_oss_result and audio_oss_result.get("success")
                        else original_audio_url
                    ),
                    "original_audio_url": original_audio_url,
                    "audio_oss_upload": audio_oss_result,
                    "duration": response.data.get("duration"),
                    "text": text,
                    "voice_type": voice_type,
                    "speed": speed,
                    "generation_method": f"ai_{response.provider}",
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "metadata": response.metadata,
                }
        except Exception as exc:
            print(f"语音生成失败: {exc}")

        return None
