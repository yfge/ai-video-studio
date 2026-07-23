from datetime import datetime
from types import SimpleNamespace
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


def test_persist_success_completes_linked_invocation(monkeypatch):
    import app.services.video.video_task_polling_service as polling_module

    complete = MagicMock()
    monkeypatch.setattr(polling_module, "complete_llm_invocation", complete)
    monkeypatch.setattr(
        polling_module,
        "refresh_parent_task_status",
        MagicMock(),
    )
    db = MagicMock()
    service = VideoTaskPollingService(db=db, ai_manager=MagicMock())
    item = SimpleNamespace(
        llm_invocation_id=42,
        provider="google",
        model="veo-3",
        provider_task_id="provider-task-1",
        model_type="image_to_video",
        task_id=9,
        script_id=None,
        frame_index=None,
        result=None,
        generation_metadata=None,
        status=None,
        completed_at=None,
    )
    result_payload = {
        "video_url": "https://cdn.example.com/final.mp4",
        "original_video_url": "https://provider.example.com/final.mp4",
        "video_oss_upload": {
            "success": True,
            "file_url": "https://cdn.example.com/final.mp4",
            "object_key": "videos/final.mp4",
            "file_size": 100,
            "content_type": "video/mp4",
            "metadata": {"sha256": "abc"},
        },
    }

    service._persist_success(
        item,
        result_payload,
        {"duration": 5, "fps": 24, "resolution": "720p"},
        datetime.utcnow(),
    )

    assert complete.call_args.args[0] == 42
    assert complete.call_args.kwargs["status"] == "succeeded"
    assert complete.call_args.kwargs["output_assets"][0]["object_key"] == (
        "videos/final.mp4"
    )
