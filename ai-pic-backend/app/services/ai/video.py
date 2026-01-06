from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.services.storage.oss_service import oss_service


class VideoGenerationMixin:
    async def generate_video(
        self,
        prompt: str = None,
        image_url: str = None,
        end_image_url: str = None,
        model: str | None = None,
        duration: int = 5,
        fps: int = 24,
        resolution: str = "1280x720",
        style: str = "realistic",
        prefer_provider: str = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """生成视频"""
        if not self.ai_manager:
            return {
                "success": False,
                "error": "AI管理器未初始化，无法生成视频（请检查 Celery worker 的环境变量/配置是否与 API 服务一致）",
            }
        try:
            # 默认请求返回尾帧，便于串联/展示，除非调用方显式关闭
            if "return_last_frame" not in kwargs:
                kwargs["return_last_frame"] = True

            response = await self.ai_manager.generate_video(
                prompt=prompt,
                image_url=image_url,
                end_image_url=end_image_url,
                model=model,
                duration=duration,
                fps=fps,
                resolution=resolution,
                prefer_provider=prefer_provider,
                **kwargs,
            )

            if response.success:
                original_video_url = response.data.get("video_url")
                original_thumbnail_url = response.data.get("thumbnail_url")
                original_last_frame_url = response.data.get("last_frame_url")

                # 自动上传视频到OSS
                video_oss_result = None
                thumbnail_oss_result = None
                last_frame_oss_result = None

                video_download_url = response.data.get("download_url") or original_video_url
                if video_download_url and oss_service:
                    try:
                        video_oss_result = await oss_service.upload_from_url(
                            url=video_download_url,
                            file_type="video",
                            prefix="ai-generated/videos",
                            metadata={
                                "prompt": prompt or "image_to_video",
                                "duration": str(duration),
                                "fps": str(fps),
                                "resolution": resolution,
                                "end_image_url": end_image_url or "",
                                "provider": response.provider,
                                "model": response.model,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as exc:
                        print(f"视频OSS上传失败: {exc}")

                if original_thumbnail_url and oss_service:
                    try:
                        thumbnail_oss_result = await oss_service.upload_from_url(
                            url=original_thumbnail_url,
                            file_type="image",
                            prefix="ai-generated/thumbnails",
                            metadata={
                                "type": "video_thumbnail",
                                "prompt": prompt or "image_to_video",
                                "provider": response.provider,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as exc:
                        print(f"缩略图OSS上传失败: {exc}")

                if original_last_frame_url and oss_service:
                    try:
                        last_frame_oss_result = await oss_service.upload_from_url(
                            url=original_last_frame_url,
                            file_type="image",
                            prefix="ai-generated/video-last-frames",
                            metadata={
                                "type": "video_last_frame",
                                "prompt": prompt or "image_to_video",
                                "provider": response.provider,
                                "generation_time": datetime.now().isoformat(),
                            },
                        )
                    except Exception as exc:
                        print(f"尾帧OSS上传失败: {exc}")

                return {
                    "video_url": (
                        video_oss_result.get("file_url")
                        if video_oss_result and video_oss_result.get("success")
                        else original_video_url
                    ),
                    "thumbnail_url": (
                        thumbnail_oss_result.get("file_url")
                        if thumbnail_oss_result
                        and thumbnail_oss_result.get("success")
                        else original_thumbnail_url
                    ),
                    "original_video_url": original_video_url,
                    "original_thumbnail_url": original_thumbnail_url,
                    "last_frame_url": (
                        last_frame_oss_result.get("file_url")
                        if last_frame_oss_result
                        and last_frame_oss_result.get("success")
                        else original_last_frame_url
                    ),
                    "original_last_frame_url": original_last_frame_url,
                    "video_oss_upload": video_oss_result,
                    "thumbnail_oss_upload": thumbnail_oss_result,
                    "last_frame_oss_upload": last_frame_oss_result,
                    "duration": response.data.get("duration", duration),
                    "prompt": prompt,
                    "image_url": image_url,
                    "end_image_url": end_image_url,
                    "generation_method": f"ai_{response.provider}",
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "metadata": response.metadata,
                }
            return {
                "success": False,
                "error": response.error or "视频生成失败",
                "provider_used": response.provider,
                "model_used": response.model,
                "metadata": response.metadata,
            }
        except Exception as exc:
            print(f"视频生成失败: {exc}")
            return {"success": False, "error": str(exc)}

        return {"success": False, "error": "视频生成失败（未知原因）"}
