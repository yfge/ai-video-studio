"""
可灵(Kling)服务提供商

专注于视频生成和图像相关功能

Updated to align with official Keling AI API documentation:
- JWT authentication (HS256) with automatic token refresh
- New base URL: https://api-beijing.klingai.com
- V2 series models support (kling-v2-6, kling-v2-5-turbo, etc.)
- Updated endpoints for image and video generation
"""

from typing import Any, Dict, List, Optional

import httpx

from ..keling_auth import KelingAuthManager
from .base import (
    AIModelType,
    AIResponse,
    AITaskType,
    BaseProvider,
    ModelInfo,
    ProviderConfig,
)
from .polling_utils import TaskPoller, keling_status_mapper


class KelingProvider(BaseProvider):
    """可灵服务提供商 - Updated with JWT authentication"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        def _normalize_base_url(raw: Optional[str]) -> str:
            """Strip trailing version segments to avoid double /v1 when building URLs."""
            base = (raw or "https://api-beijing.klingai.com").strip()
            base = base.rstrip("/")
            if base.endswith("/v1"):
                base = base[: -len("/v1")]
            return base

        # Validate required credentials
        if not config.api_key:
            raise ValueError("Keling Provider requires api_key (AccessKey)")
        if not config.api_secret:
            raise ValueError("Keling Provider requires api_secret (SecretKey)")

        # New official base URL
        self.base_url = _normalize_base_url(config.base_url)

        # Initialize JWT authentication manager
        self.auth_manager = KelingAuthManager(
            access_key=config.api_key,
            secret_key=config.api_secret,
            token_ttl=1800,  # 30 minutes
            refresh_buffer=300,  # Refresh 5 minutes before expiry
        )

    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [
            AIModelType.TEXT_TO_VIDEO,
            AIModelType.IMAGE_TO_VIDEO,
            AIModelType.TEXT_TO_IMAGE,
            AIModelType.IMAGE_TO_IMAGE,
        ]

    @property
    def available_models(self) -> List[ModelInfo]:
        """Updated model list with V2 series support"""
        return [
            # V2 Series Models - Latest generation
            ModelInfo(
                model_id="kling-v2-6",
                name="可灵 V2.6",
                description="最新V2.6版本，支持声音控制，1080p高清输出",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=[
                    "image_to_video",
                    "sound_control",
                    "1080p",
                    "30fps",
                    "professional_mode",
                ],
                metadata={
                    "ui": {
                        "resolution_options": ["1080P", "720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "1080P",
                        "default_ratio": "16:9",
                        "supports_camera_control": True,
                        "supports_watermark": False,
                        "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                    }
                },
            ),
            ModelInfo(
                model_id="kling-v2-5-turbo",
                name="可灵 V2.5 Turbo",
                description="V2.5快速版本，生成速度更快",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["image_to_video", "fast_generation", "1080p", "30fps"],
                metadata={
                    "ui": {
                        "resolution_options": ["1080P", "720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "1080P",
                        "default_ratio": "16:9",
                        "supports_camera_control": True,
                        "supports_watermark": False,
                        "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                    }
                },
            ),
            ModelInfo(
                model_id="kling-v2-1-master",
                name="可灵 V2.1 Master",
                description="V2.1专业版，支持更多高级特性",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=[
                    "image_to_video",
                    "master_quality",
                    "1080p",
                    "30fps",
                    "advanced_controls",
                ],
                metadata={
                    "ui": {
                        "resolution_options": ["1080P", "720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "1080P",
                        "default_ratio": "16:9",
                        "supports_camera_control": True,
                        "supports_watermark": False,
                        "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                    }
                },
            ),
            ModelInfo(
                model_id="kling-v2-1",
                name="可灵 V2.1",
                description="V2.1标准版，平衡质量与速度",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["image_to_video", "1080p", "30fps"],
                metadata={
                    "ui": {
                        "resolution_options": ["1080P", "720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "1080P",
                        "default_ratio": "16:9",
                        "supports_camera_control": True,
                        "supports_watermark": False,
                        "camera_control_hint": "按可灵 image2video camera_control JSON 传参，例如轨迹/速度。",
                    }
                },
            ),
            # V1 Series Models - Legacy but still supported
            ModelInfo(
                model_id="kling-v1-6",
                name="可灵 V1.6",
                description="V1.6版本，支持多图生成视频",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["image_to_video", "multi_image", "720p", "24fps"],
                metadata={
                    "ui": {
                        "resolution_options": ["720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "720P",
                        "default_ratio": "16:9",
                        "supports_camera_control": False,
                        "supports_watermark": False,
                    }
                },
            ),
            ModelInfo(
                model_id="kling-v1-5",
                name="可灵 V1.5",
                description="V1.5版本，稳定可靠",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["image_to_video", "720p", "24fps"],
                metadata={
                    "ui": {
                        "resolution_options": ["720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "720P",
                        "default_ratio": "16:9",
                        "supports_camera_control": False,
                        "supports_watermark": False,
                    }
                },
            ),
            ModelInfo(
                model_id="kling-v1",
                name="可灵 V1",
                description="V1基础版本",
                model_type=AIModelType.IMAGE_TO_VIDEO,
                supported_formats=["mp4"],
                capabilities=["image_to_video", "720p", "24fps"],
                metadata={
                    "ui": {
                        "resolution_options": ["720P"],
                        "duration_options": [5, 10],
                        "supports_end_frame": True,
                        "supports_camera_fixed": False,
                        "ratio_options": ["16:9", "9:16", "1:1", "4:3"],
                        "default_resolution": "720P",
                        "default_ratio": "16:9",
                        "supports_camera_control": False,
                        "supports_watermark": False,
                    }
                },
            ),
            # Image Generation Models
            ModelInfo(
                model_id="kling-image-v2",
                name="可灵图像生成 V2",
                description="V2图像生成模型，支持2K分辨率和人物参考",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=[
                    "text_to_image",
                    "image_to_image",
                    "2k_resolution",
                    "character_reference",
                    "face_reference",
                ],
                metadata={
                    "ui": {
                        "size_options": ["2k", "1k"],
                        "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                        "supports_aspect_ratio": True,
                        "supports_reference_image": True,
                    }
                },
            ),
            ModelInfo(
                model_id="kling-image-v1",
                name="可灵图像生成 V1",
                description="V1图像生成模型，支持1K分辨率",
                model_type=AIModelType.TEXT_TO_IMAGE,
                supported_formats=["png", "jpg"],
                capabilities=["text_to_image", "image_to_image", "1k_resolution"],
                metadata={
                    "ui": {
                        "size_options": ["1k"],
                        "aspect_ratio_options": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                        "supports_aspect_ratio": True,
                        "supports_reference_image": True,
                    }
                },
            ),
        ]

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with JWT token"""
        auth_header = self.auth_manager.get_auth_header()
        return {
            **auth_header,
            "Content-Type": "application/json",
            "User-Agent": "ai-video-studio/2.0",
        }

    async def _initialize_client(self):
        """Initialize HTTP client with JWT authentication"""
        # Note: Headers will be updated dynamically per request to use fresh JWT tokens
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0),  # Video generation requires longer timeout
            headers=self._get_auth_headers(),
        )

    async def generate_text(
        self, prompt: str, model: str = None, **kwargs
    ) -> AIResponse:
        """可灵不支持文本生成"""
        return AIResponse(
            success=False,
            error="可灵不支持纯文本生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    async def generate_image(
        self,
        prompt: str,
        model: str = "kling-image-v2",
        negative_prompt: Optional[str] = None,
        image: Optional[str] = None,  # Reference image URL or base64
        image_reference: Optional[str] = None,  # character/face reference mode
        image_fidelity: Optional[float] = None,  # 0.5-1.0
        human_fidelity: Optional[float] = None,  # 0.5-1.0
        resolution: str = "1k",  # 1k or 2k
        n: int = 1,  # Number of images to generate
        aspect_ratio: Optional[str] = None,  # e.g., "16:9", "1:1", "9:16"
        **kwargs,
    ) -> AIResponse:
        """
        Generate images using Keling AI (new API endpoint).

        Endpoint: POST /v1/images/generations
        Polling: GET /v1/images/generations/{task_id}

        Args:
            prompt: Text prompt for image generation
            model: Model name (kling-image-v2 or kling-image-v1)
            negative_prompt: Negative prompt to avoid certain elements
            image: Reference image (URL or base64 data URL)
            image_reference: Reference mode ("character" or "face")
            image_fidelity: Image similarity (0.5-1.0)
            human_fidelity: Human feature fidelity (0.5-1.0)
            resolution: Output resolution ("1k" or "2k")
            n: Number of images to generate (1-4)
            aspect_ratio: Aspect ratio like "16:9", "1:1", etc.

        Returns:
            AIResponse with generated images
        """
        try:
            client = await self.get_client()

            # Build request payload according to API spec
            request_data = {"model_name": model, "prompt": prompt, "n": n}

            # Add optional parameters
            if negative_prompt:
                request_data["negative_prompt"] = negative_prompt
            if image:
                request_data["image"] = image
            if image_reference:
                request_data["image_reference"] = image_reference
            if image_fidelity is not None:
                request_data["image_fidelity"] = image_fidelity
            if human_fidelity is not None:
                request_data["human_fidelity"] = human_fidelity
            if aspect_ratio:
                request_data["aspect_ratio"] = aspect_ratio

            # Resolution is part of model capabilities, not a request param
            # but we keep it for metadata

            # Create image generation task
            response = await client.post(
                f"{self.base_url}/v1/images/generations",
                json=request_data,
                headers=self._get_auth_headers(),  # Fresh JWT token
            )
            response.raise_for_status()
            data = response.json()

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return AIResponse(
                    success=False,
                    error="No task_id in response",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                )

            # Poll task status using TaskPoller
            result = await self._poll_image_task(task_id)

            if result and "images" in result:
                return AIResponse(
                    success=True,
                    data={"images": result["images"]},
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                    metadata={
                        "task_id": task_id,
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio,
                        "prompt": prompt,
                        "n": n,
                    },
                )
            else:
                return AIResponse(
                    success=False,
                    error="Image generation task failed or timed out",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.PORTRAIT_GENERATION,
                    model_type=AIModelType.TEXT_TO_IMAGE,
                )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.PORTRAIT_GENERATION,
                model_type=AIModelType.TEXT_TO_IMAGE,
            )

    async def _poll_image_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll image generation task status.

        Endpoint: GET /v1/images/generations/{task_id}
        """
        client = await self.get_client()

        async def poll_fn() -> Dict[str, Any]:
            response = await client.get(
                f"{self.base_url}/v1/images/generations/{task_id}",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            return response.json().get("data", {})

        def extract_result(data: Dict[str, Any]) -> Dict[str, Any]:
            """Extract images from response"""
            task_result = data.get("task_result", {})
            images = task_result.get("images", [])
            return {"images": images}

        poller = TaskPoller(
            poll_fn=poll_fn,
            status_mapper=keling_status_mapper,
            result_extractor=extract_result,
            max_attempts=60,  # 5 minutes with 5s interval
            initial_delay=5.0,
            task_id=task_id,
            task_type="image",
        )

        return await poller.poll()

    async def generate_video(
        self,
        prompt: Optional[str] = None,
        image: Optional[str] = None,  # First frame image (URL or base64)
        image_url: Optional[
            str
        ] = None,  # Alias for first frame to match AIServiceManager
        image_tail: Optional[str] = None,  # Last frame image (URL or base64)
        end_image_url: Optional[str] = None,  # Alias for last frame
        model: str = "kling-v2-1",
        mode: str = "std",  # std or pro
        duration: int = 5,  # 5 or 10 seconds
        resolution: Optional[str] = None,  # e.g., 720P/1080P
        ratio: Optional[str] = None,  # e.g., 16:9, 9:16
        negative_prompt: Optional[str] = None,
        cfg_scale: Optional[float] = None,  # 0.0-1.0, not supported by V2-x models
        camera_control: Optional[Dict[str, Any]] = None,  # Camera movement config
        **kwargs,
    ) -> AIResponse:
        """
        Generate video from image using Keling AI (new API endpoint).

        Endpoint: POST /v1/videos/image2video
        Polling: GET /v1/videos/image2video/{task_id}

        Args:
            prompt: Text description for video generation
            image: First frame image (required, URL or base64)
            image_tail: Last frame image (optional, for first-last frame mode)
            model: Model name (kling-v2-6, kling-v2-5-turbo, kling-v2-1-master, kling-v2-1, etc.)
            mode: Generation mode ("std" standard or "pro" professional)
            duration: Video duration in seconds (5 or 10)
            negative_prompt: Negative prompt to avoid certain elements
            cfg_scale: Prompt relevance (0.0-1.0), V1 models only
            camera_control: Camera movement configuration (mutually exclusive with motion_brush)
            **kwargs: Additional parameters (dynamic_masks, static_mask, voice_list, sound, etc.)

        Returns:
            AIResponse with generated video URL
        """
        primary_image = image or image_url
        tail_image = image_tail or end_image_url

        if not primary_image:
            return AIResponse(
                success=False,
                error="image parameter is required for video generation",
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

        try:
            client = await self.get_client()

            # Keling video only supports 5s/10s; clamp to nearest allowed.
            try:
                dur_int = int(duration)
            except (TypeError, ValueError):
                dur_int = 5
            allowed_durations = [5, 10]
            if dur_int not in allowed_durations:
                dur_int = min(allowed_durations, key=lambda d: abs(d - dur_int))

            # Build request payload
            request_data = {
                "model_name": model,
                "image": primary_image,
                "mode": mode,
                "duration": dur_int,
            }

            # Add optional parameters
            if tail_image:
                request_data["image_tail"] = tail_image
            if prompt:
                request_data["prompt"] = prompt
            if negative_prompt:
                request_data["negative_prompt"] = negative_prompt
            if cfg_scale is not None and not model.startswith("kling-v2"):
                # cfg_scale only supported by V1 models
                request_data["cfg_scale"] = cfg_scale
            if camera_control:
                request_data["camera_control"] = camera_control
            # Newer API variants expect resolution/aspect ratio; pass through when provided.
            resolved_resolution = (
                resolution
                or kwargs.get("resolution")
                or kwargs.get("rs")
                or kwargs.get("output_resolution")
            )
            if resolved_resolution:
                request_data["resolution"] = str(resolved_resolution).upper()

            resolved_ratio = ratio or kwargs.get("ratio") or kwargs.get("aspect_ratio")
            if resolved_ratio:
                request_data["aspect_ratio"] = str(resolved_ratio)

            # Add any additional parameters from kwargs
            for key in ["dynamic_masks", "static_mask", "voice_list", "sound"]:
                if key in kwargs:
                    request_data[key] = kwargs[key]

            # Create video generation task
            response = await client.post(
                f"{self.base_url}/v1/videos/image2video",
                json=request_data,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data = response.json()

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return AIResponse(
                    success=False,
                    error="No task_id in response",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                )

            # Poll task status
            result = await self._poll_video_task(task_id)

            if result and "video_url" in result:
                return AIResponse(
                    success=True,
                    data={"video_url": result["video_url"], "duration": duration},
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                    metadata={
                        "task_id": task_id,
                        "duration": duration,
                        "mode": mode,
                        "prompt": prompt,
                    },
                )
            else:
                return AIResponse(
                    success=False,
                    error="Video generation task failed or timed out",
                    provider=self.name,
                    model=model,
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

    async def generate_video_from_multiple_images(
        self,
        image_list: List[str],  # 2-4 images (URL or base64)
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        mode: str = "std",
        duration: int = 5,
        aspect_ratio: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate video from multiple images (kling-v1-6 only).

        Endpoint: POST /v1/videos/multi-image2video

        Args:
            image_list: List of 2-4 images (URLs or base64)
            prompt: Text description
            negative_prompt: Negative prompt
            mode: Generation mode ("std" or "pro")
            duration: Video duration (5 or 10 seconds)
            aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")

        Returns:
            AIResponse with generated video URL
        """
        if not image_list or len(image_list) < 2 or len(image_list) > 4:
            return AIResponse(
                success=False,
                error="image_list must contain 2-4 images",
                provider=self.name,
                model="kling-v1-6",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

        try:
            client = await self.get_client()

            request_data = {
                "model_name": "kling-v1-6",  # Only supported by v1-6
                "image_list": image_list,
                "mode": mode,
                "duration": duration,
            }

            if prompt:
                request_data["prompt"] = prompt
            if negative_prompt:
                request_data["negative_prompt"] = negative_prompt
            if aspect_ratio:
                request_data["aspect_ratio"] = aspect_ratio

            response = await client.post(
                f"{self.base_url}/v1/videos/multi-image2video",
                json=request_data,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            data = response.json()

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return AIResponse(
                    success=False,
                    error="No task_id in response",
                    provider=self.name,
                    model="kling-v1-6",
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                )

            # Poll task status (uses same endpoint as image2video)
            result = await self._poll_video_task(task_id)

            if result and "video_url" in result:
                return AIResponse(
                    success=True,
                    data={"video_url": result["video_url"], "duration": duration},
                    provider=self.name,
                    model="kling-v1-6",
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                    metadata={
                        "task_id": task_id,
                        "duration": duration,
                        "mode": mode,
                        "image_count": len(image_list),
                    },
                )
            else:
                return AIResponse(
                    success=False,
                    error="Multi-image video generation failed or timed out",
                    provider=self.name,
                    model="kling-v1-6",
                    task_type=AITaskType.VIDEO_GENERATION,
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="kling-v1-6",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            )

    async def _poll_video_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll video generation task status.

        Endpoint: GET /v1/videos/image2video/{task_id}
        """
        client = await self.get_client()

        async def poll_fn() -> Dict[str, Any]:
            response = await client.get(
                f"{self.base_url}/v1/videos/image2video/{task_id}",
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            return response.json().get("data", {})

        def extract_result(data: Dict[str, Any]) -> Dict[str, Any]:
            """Extract video URL from response"""
            task_result = data.get("task_result", {})
            videos = task_result.get("videos", [])
            if videos and len(videos) > 0:
                return {"video_url": videos[0].get("url")}
            return {}

        poller = TaskPoller(
            poll_fn=poll_fn,
            status_mapper=keling_status_mapper,
            result_extractor=extract_result,
            max_attempts=120,  # 20 minutes with 10s interval
            initial_delay=10.0,
            task_id=task_id,
            task_type="video",
        )

        return await poller.poll()

    async def get_task_status(
        self, task_id: str, task_type: str = "video"
    ) -> AIResponse:
        """
        Get task status for a given task ID (public method).

        Args:
            task_id: Task ID to query
            task_type: Type of task ("image" or "video")

        Returns:
            AIResponse with task status information
        """
        try:
            client = await self.get_client()

            # Use appropriate endpoint based on task type
            if task_type == "image":
                endpoint = f"{self.base_url}/v1/images/generations/{task_id}"
            else:  # video
                endpoint = f"{self.base_url}/v1/videos/image2video/{task_id}"

            response = await client.get(endpoint, headers=self._get_auth_headers())
            response.raise_for_status()

            data = response.json().get("data", {})

            return AIResponse(
                success=True,
                data=data,
                provider=self.name,
                model="task_status",
                task_type=(
                    AITaskType.VIDEO_GENERATION
                    if task_type == "video"
                    else AITaskType.PORTRAIT_GENERATION
                ),
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if task_type == "video"
                    else AIModelType.TEXT_TO_IMAGE
                ),
                metadata={"task_id": task_id, "task_type": task_type},
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model="task_status",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.TEXT_TO_VIDEO,
            )
