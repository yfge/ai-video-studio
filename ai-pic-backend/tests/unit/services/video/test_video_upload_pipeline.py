from unittest.mock import ANY, AsyncMock, MagicMock, patch

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
        ) as trim_mock,
        patch(
            "app.services.video.video_upload_pipeline.probe_video_duration_bytes",
            return_value=6.0,
        ),
        patch(
            "app.services.video.video_upload_pipeline.extract_video_frame_bytes",
            return_value=b"last-frame-bytes",
        ),
        patch(
            "app.services.video.video_upload_pipeline.upload_video_last_frame_bytes_to_oss",
            new=AsyncMock(
                return_value={
                    "success": True,
                    "file_url": "https://cdn.example.com/trimmed-last-frame.png",
                }
            ),
        ) as last_frame_upload_mock,
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
    assert result["actual_trim_duration_seconds"] == 5.0
    assert result["trimmed_video_frame_count"] == 120
    assert result["trimmed_last_frame_oss_upload"]["success"] is True
    assert upload_mock.await_count == 2
    last_frame_upload_mock.assert_awaited_once_with(
        image_bytes=b"last-frame-bytes",
        provider="google",
        logger=ANY,
    )
    assert trim_mock.call_args.kwargs["target_fps"] == 24


@pytest.mark.asyncio
async def test_upload_trims_provider_overshoot_when_requested_duration_matches_target():
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
            "app.services.video.video_upload_pipeline.probe_video_duration_bytes",
            return_value=15.093,
        ),
        patch(
            "app.services.video.video_upload_pipeline.trim_video_bytes",
            return_value=b"trimmed-bytes",
        ) as trim_mock,
        patch(
            "app.services.video.video_upload_pipeline.extract_video_frame_bytes",
            return_value=b"last-frame-bytes",
        ),
        patch(
            "app.services.video.video_upload_pipeline.upload_video_last_frame_bytes_to_oss",
            new=AsyncMock(return_value={"success": True}),
        ),
        patch(
            "app.services.video.video_upload_pipeline.upload_video_bytes_to_oss",
            new=AsyncMock(side_effect=upload_side_effect),
        ),
    ):
        result = await upload_video_with_optional_trim(
            original_video_url="https://provider.example.com/video.mp4",
            video_download_url="https://provider.example.com/video.mp4",
            video_bytes_base64=None,
            video_mime_type="video/mp4",
            prompt="p",
            end_image_url="",
            provider="volcengine",
            model="seedance-2.0",
            fps=24,
            resolution="720p",
            provider_duration_seconds=15,
            target_duration_seconds=15.0,
            logger=MagicMock(),
        )

    assert result["video_url"] == "https://cdn.example.com/trimmed.mp4"
    assert result["actual_trim_duration_seconds"] == 15.0
    assert result["trimmed_video_frame_count"] == 360
    trim_mock.assert_called_once()
