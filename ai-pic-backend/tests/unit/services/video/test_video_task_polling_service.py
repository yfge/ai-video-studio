from unittest.mock import MagicMock

from app.services.video.video_task_polling_service import VideoTaskPollingService


def test_build_ai_response_includes_download_url():
    service = VideoTaskPollingService(db=MagicMock(), ai_manager=MagicMock())
    item = MagicMock()
    item.model_type = "image_to_video"
    item.provider = "google"
    item.model = "veo-3.1-generate-preview"
    item.provider_task_id = "models/veo/operations/abc"

    response = MagicMock()
    response.data = {
        "video_url": "https://generativelanguage.googleapis.com/v1beta/files/abc:download?alt=media",
        "download_url": "https://generativelanguage.googleapis.com/v1beta/files/abc:download?alt=media&key=test",
        "thumbnail_url": None,
        "last_frame_url": None,
    }

    built = service._build_ai_response(item, response)

    assert built.data["download_url"] == response.data["download_url"]
