from unittest.mock import AsyncMock, patch

import pytest
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_generation_service import VideoGenerationService


@pytest.mark.asyncio
async def test_trimmed_video_uses_its_own_last_frame() -> None:
    trimmed_last_frame = {
        "success": True,
        "file_url": "https://cdn.example.com/trimmed-last-frame.png",
    }
    response = AIResponse(
        success=True,
        data={
            "video_url": "https://provider.example.com/video.mp4",
            "last_frame_url": "https://provider.example.com/provider-last-frame.png",
            "duration": 7,
        },
        provider="volcengine",
        model="doubao-seedance-2-0-260128",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=AIModelType.TEXT_TO_VIDEO,
    )
    with (
        patch(
            "app.services.video.video_generation_service.upload_video_with_optional_trim",
            new=AsyncMock(
                return_value={
                    "video_url": "https://cdn.example.com/trimmed.mp4",
                    "duration": 6.26,
                    "trimmed_last_frame_oss_upload": trimmed_last_frame,
                }
            ),
        ),
        patch(
            "app.services.video.video_generation_service.upload_video_thumbnail_to_oss",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.services.video.video_generation_service.upload_video_last_frame_to_oss",
            new=AsyncMock(return_value=None),
        ) as provider_last_frame_upload,
    ):
        result = await VideoGenerationService()._process_successful_response(
            response=response,
            prompt="storyboard sequence",
            image_url=None,
            end_image_url=None,
            duration=7,
            fps=24,
            resolution="720p",
            target_duration_seconds=6.26,
        )

    assert result["last_frame_url"] == trimmed_last_frame["file_url"]
    assert result["last_frame_oss_upload"] == trimmed_last_frame
    assert "trimmed_last_frame_oss_upload" not in result
    provider_last_frame_upload.assert_not_awaited()
