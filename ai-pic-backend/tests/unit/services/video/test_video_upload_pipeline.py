from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.video.video_upload_pipeline import upload_video_with_optional_trim


@pytest.mark.asyncio
async def test_upload_video_with_optional_trim_trims_when_target_shorter() -> None:
    upload_side_effect = [
        {"success": True, "file_url": "https://cdn.example.com/untrimmed.mp4"},
        {"success": True, "file_url": "https://cdn.example.com/trimmed.mp4"},
    ]
    with (
        patch(
            "app.services.video.video_upload_pipeline.download_video_bytes",
            new=AsyncMock(return_value=b"raw-bytes"),
        ),
        patch(
            "app.services.video.video_upload_pipeline.trim_video_bytes",
            return_value=b"trimmed-bytes",
        ),
        patch(
            "app.services.video.video_upload_pipeline.upload_video_bytes_to_oss",
            new=AsyncMock(side_effect=upload_side_effect),
        ) as upload_mock,
    ):
        result = await upload_video_with_optional_trim(
            original_video_url="https://provider.example.com/video.mp4",
            video_download_url="https://provider.example.com/video.mp4",
            video_bytes_base64=None,
            video_mime_type="video/mp4",
            prompt="p",
            end_image_url="",
            provider="google",
            model="veo-3.1-generate-preview",
            fps=24,
            resolution="720p",
            provider_duration_seconds=6,
            target_duration_seconds=5.0,
            logger=MagicMock(),
        )

    assert result["video_url"] == "https://cdn.example.com/trimmed.mp4"
    assert result["untrimmed_video_url"] == "https://cdn.example.com/untrimmed.mp4"
    assert result["duration"] == 5.0
    assert upload_mock.await_count == 2

