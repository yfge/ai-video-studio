"""
Volcengine video generation module.

Contains video generation (Seedance) functionality with async polling.
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

from ..base import AIModelType, AIResponse, AITaskType

if TYPE_CHECKING:
    pass


def _contains_flag(text: str, flag: str) -> bool:
    """Check if text contains a specific flag."""
    return re.search(rf"(^|\\s){re.escape(flag)}(\\s|$)", text) is not None


def _normalize_resolution_flag(value: Optional[str]) -> Optional[str]:
    """Normalize resolution value to API format."""
    if not value:
        return None
    v = str(value).strip().lower()
    if v in {"480p", "720p", "1080p"}:
        return v
    # Handle common WxH inputs (e.g., 1280x720 / 1920x1080)
    if "1080" in v or "1088" in v:
        return "1080p"
    if "720" in v:
        return "720p"
    if "480" in v:
        return "480p"
    return None


def _normalize_model(model: Optional[str], has_image: bool) -> str:
    """Normalize model name to actual Ark model ID."""
    ark_model = (model or "").strip() or "doubao-seedance-1-0-pro-250528"
    normalized = ark_model.lower()

    if normalized.startswith("volcengine-video"):
        return "doubao-seedance-1-0-pro-250528"

    # Handle Seedream image-to-video aliases
    if normalized.startswith("seedream-i2v"):
        if normalized in {"seedream-i2v-fast", "seedream-i2v-pro-fast"}:
            return "doubao-seedance-1-0-pro-fast-251015"
        elif normalized in {"seedream-i2v-lite"}:
            return "doubao-seedance-1-0-lite-i2v-250428"
        else:
            return "doubao-seedance-1-0-pro-250528"

    return ark_model


def _build_prompt_with_flags(
    prompt: Optional[str],
    resolution: Optional[str],
    ratio: Optional[str],
    duration: int,
    fps: int,
    watermark: Optional[bool],
    seed: Optional[int],
    camera_fixed: Optional[bool],
) -> tuple[str, int, int, Optional[str], Optional[str]]:
    """Build prompt with Ark parameter flags."""
    base_prompt = (prompt or "").strip() or "生成一段符合描述的视频"
    flags: list[str] = []

    rs = _normalize_resolution_flag(resolution)
    if rs and not _contains_flag(base_prompt, "--rs"):
        flags.append(f"--rs {rs}")

    rt = (ratio or "").strip()
    if rt and not (
        _contains_flag(base_prompt, "--rt")
        or _contains_flag(base_prompt, "--ratio")
    ):
        flags.append(f"--rt {rt}")

    # Duration: 2~12 seconds per docs
    dur = int(duration or 5)
    dur = max(2, min(dur, 12))
    if not _contains_flag(base_prompt, "--dur"):
        flags.append(f"--dur {dur}")

    fps_int = int(fps or 24)
    if fps_int != 24:
        fps_int = 24
    if not _contains_flag(base_prompt, "--fps"):
        flags.append(f"--fps {fps_int}")

    if watermark is not None and not _contains_flag(base_prompt, "--wm"):
        flags.append(f"--wm {'true' if watermark else 'false'}")

    if seed is not None and not _contains_flag(base_prompt, "--seed"):
        flags.append(f"--seed {int(seed)}")

    if camera_fixed is not None and not _contains_flag(base_prompt, "--cf"):
        flags.append(f"--cf {'true' if camera_fixed else 'false'}")

    final_prompt = base_prompt
    if flags:
        final_prompt = f"{base_prompt} {' '.join(flags)}"

    return final_prompt, dur, fps_int, rs or resolution, rt or None


async def poll_task_status(
    client: httpx.AsyncClient,
    base_url: str,
    task_id: str,
    max_attempts: int = 60,
    delay: int = 3,
) -> Optional[Dict[str, Any]]:
    """Poll Volcengine content generation task status."""
    for attempt in range(max_attempts):
        try:
            response = await client.get(
                f"{base_url}/contents/generations/tasks/{task_id}",
            )
            response.raise_for_status()

            data = response.json() if response.content else {}
            if not isinstance(data, dict):
                return None

            status = str(data.get("status") or "").lower()

            if status == "succeeded":
                return data
            if status in {"failed", "canceled", "cancelled"}:
                return None
            if status in {"queued", "running", "processing", "pending"}:
                await asyncio.sleep(delay)
                continue

            # Unknown status: exit to avoid infinite loop
            return None

        except Exception as e:
            print(f"轮询火山引擎任务状态失败 (尝试 {attempt + 1}): {e}")
            await asyncio.sleep(delay)

    return None


async def generate_video(
    client: httpx.AsyncClient,
    base_url: str,
    provider_name: str,
    prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    model: Optional[str] = None,
    duration: int = 5,
    fps: int = 24,
    resolution: str = "720p",
    end_image_url: Optional[str] = None,
    ratio: Optional[str] = None,
    watermark: Optional[bool] = None,
    seed: Optional[int] = None,
    camera_fixed: Optional[bool] = None,
    service_tier: Optional[str] = None,
    execution_expires_after: Optional[int] = None,
    return_last_frame: Optional[bool] = None,
    format_error: callable = str,
    **kwargs,
) -> AIResponse:
    """Generate video using Volcengine Ark Video Generation API (Seedance)."""
    try:
        ark_model = _normalize_model(model, image_url is not None)

        final_prompt, dur, fps_int, rs, rt = _build_prompt_with_flags(
            prompt, resolution, ratio, duration, fps,
            watermark, seed, camera_fixed,
        )

        content: list[Dict[str, Any]] = [
            {"type": "text", "text": final_prompt},
        ]
        if image_url:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                    "role": "first_frame",
                }
            )
        if end_image_url:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": end_image_url},
                    "role": "last_frame",
                }
            )

        request_data: Dict[str, Any] = {"model": ark_model, "content": content}
        if service_tier:
            request_data["service_tier"] = service_tier
        if execution_expires_after is not None:
            request_data["execution_expires_after"] = int(execution_expires_after)
        if return_last_frame is not None:
            request_data["return_last_frame"] = bool(return_last_frame)

        # Allow passthrough of future parameters (don't override existing fields)
        for key, value in (kwargs or {}).items():
            if key in request_data:
                continue
            request_data[key] = value

        create_resp = await client.post(
            f"{base_url}/contents/generations/tasks",
            json=request_data,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json() if create_resp.content else {}

        if isinstance(create_data, dict) and create_data.get("error"):
            err = create_data.get("error") or {}
            return AIResponse(
                success=False,
                error=f"火山引擎视频生成错误: {err.get('message') or err.get('code') or 'Unknown error'}",
                provider=provider_name,
                model=ark_model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
            )

        # Extract task ID from various response formats
        task_id = (
            create_data.get("id") if isinstance(create_data, dict) else None
        ) or (create_data.get("task_id") if isinstance(create_data, dict) else None)
        if not task_id and isinstance(create_data, dict):
            nested = create_data.get("data")
            if isinstance(nested, dict):
                task_id = nested.get("id") or nested.get("task_id")

        if not task_id:
            return AIResponse(
                success=False,
                error="火山引擎视频生成响应缺少任务ID",
                provider=provider_name,
                model=ark_model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"raw": create_data},
            )

        result = await poll_task_status(
            client,
            base_url,
            str(task_id),
            max_attempts=120,
            delay=3,
        )
        if not result:
            return AIResponse(
                success=False,
                error="视频生成任务失败或超时",
                provider=provider_name,
                model=ark_model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"task_id": task_id},
            )

        content_out = result.get("content") or {}
        video_url = (
            content_out.get("video_url")
            or content_out.get("videoUrl")
            or content_out.get("url")
            or result.get("video_url")
            or result.get("videoUrl")
            or result.get("url")
        )
        thumbnail_url = (
            content_out.get("thumbnail_url")
            or content_out.get("cover_image_url")
            or content_out.get("cover_url")
            or content_out.get("poster_url")
        )
        last_frame_url = content_out.get("last_frame_url") or content_out.get(
            "lastFrameUrl"
        )

        if not video_url:
            return AIResponse(
                success=False,
                error="火山引擎视频生成成功但未返回视频URL",
                provider=provider_name,
                model=ark_model,
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=(
                    AIModelType.IMAGE_TO_VIDEO
                    if image_url
                    else AIModelType.TEXT_TO_VIDEO
                ),
                metadata={"task_id": task_id, "raw": result},
            )

        return AIResponse(
            success=True,
            data={
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "duration": dur,
                "last_frame_url": last_frame_url,
            },
            provider=provider_name,
            model=ark_model,
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=(
                AIModelType.IMAGE_TO_VIDEO
                if image_url
                else AIModelType.TEXT_TO_VIDEO
            ),
            metadata={
                "task_id": task_id,
                "prompt": final_prompt,
                "duration": dur,
                "fps": fps_int,
                "resolution": rs or resolution,
                "ratio": rt,
                "watermark": watermark,
                "seed": seed,
                "camera_fixed": camera_fixed,
                "service_tier": service_tier,
            },
        )

    except Exception as e:
        return AIResponse(
            success=False,
            error=format_error(e),
            provider=provider_name,
            model=(model or "doubao-seedance-1-0-pro-250528"),
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=(
                AIModelType.IMAGE_TO_VIDEO
                if image_url
                else AIModelType.TEXT_TO_VIDEO
            ),
        )
