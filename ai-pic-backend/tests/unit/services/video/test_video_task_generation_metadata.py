from app.services.video.video_task_generation_metadata import build_video_generation_metadata


def test_build_video_generation_metadata_parses_720p_landscape_dimensions():
    meta = build_video_generation_metadata(
        "google",
        "veo",
        "task-1",
        "image_to_video",
        {"resolution": "720p", "ratio": "16:9", "fps": 24, "duration": 8},
        {
            "duration": 8,
            "video_oss_upload": {
                "success": True,
                "object_key": "ai-generated/videos/video/20260129/000000/abcd.mp4",
                "file_url": "https://cdn.example.com/video.mp4",
                "file_size": 123,
                "content_type": "video/mp4",
                "metadata": {"sha256": "deadbeef"},
            },
        },
    )
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["assets"]["video"]["sha256"] == "deadbeef"


def test_build_video_generation_metadata_parses_720p_portrait_dimensions():
    meta = build_video_generation_metadata(
        "google",
        "veo",
        "task-1",
        "image_to_video",
        {"resolution": "720p", "ratio": "9:16"},
        {},
    )
    assert meta["width"] == 720
    assert meta["height"] == 1280


def test_build_video_generation_metadata_falls_back_to_original_url_when_no_oss_upload():
    meta = build_video_generation_metadata(
        "google",
        "veo",
        "task-1",
        "image_to_video",
        {"resolution": "1280x720"},
        {"original_video_url": "https://origin.example.com/video.mp4"},
    )
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["assets"]["video"]["url"] == "https://origin.example.com/video.mp4"

