import json

from app.models.task import Task
from tests.test_timeline_clip_video_grid_rework_api import (
    _bootstrap_episode,
    _create_timeline,
    _media_asset,
    _timeline_spec_with_clip_storyboard,
)


def test_timeline_clip_video_rework_uses_full_storyboard_sheet_as_sequence(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["payload"] = payload

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_queue_service."
        "dispatch_timeline_clip_video_rework_task",
        fake_dispatch,
    )
    _, episode, script = _bootstrap_episode(db_session)
    sheet_asset = _media_asset(
        db_session,
        asset_type="image",
        origin="generated",
        file_url="https://example.com/clip-storyboard.png",
        mime_type="image/png",
    )
    clip_id = "video_scene_001_beat_001_001"
    spec = _timeline_spec_with_clip_storyboard(
        episode,
        script,
        clip_id,
        sheet_asset,
    )
    spec["support_views"]["clip_storyboards"][clip_id]["panels"] = [
        _clip_storyboard_panel(clip_id, index) for index in range(1, 5)
    ]
    timeline = _create_timeline(client, episode, script, spec)

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "use_clip_storyboard": True,
            "model": "volcengine:doubao-seedance-2-0-260128",
        },
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["reference_mode"] == "clip_storyboard_sheet"
    assert params["reference_images"] == ["https://example.com/clip-storyboard.png"]
    assert params["clip_storyboard"] == {
        "mode": "sheet_sequence",
        "panel_count": 4,
        "panel_ids": [f"clip_storyboard_panel_{index:03d}" for index in range(1, 5)],
        "sheet_media_asset_id": sheet_asset.id,
        "source_timeline_version": 2,
        "reading_order": "left_to_right_top_to_bottom",
        "duration_seconds": 1.2,
    }
    assert params["duration"] == 1.2
    assert params["ratio"] == "9:16"
    assert params.get("image_url") is None
    assert "entire clip storyboard sheet" in params["prompt"]
    assert "left-to-right, top-to-bottom" in params["prompt"]
    assert "Panel 1 at 0.000s" in params["prompt"]
    assert "Panel 4 at 1.100s" in params["prompt"]
    assert "Use panel" not in params["prompt"]
    assert dispatched["payload"]["clip_storyboard"]["mode"] == "sheet_sequence"


def _clip_storyboard_panel(clip_id: str, index: int) -> dict:
    actions = [
        "主角抬头注意到来人",
        "主角向前递出手机",
        "手指点亮手机屏幕",
        "两人一起看向手机",
    ]
    return {
        "panel_id": f"clip_storyboard_panel_{index:03d}",
        "panel_index": index,
        "clip_id": clip_id,
        "start_ms": 0,
        "end_ms": 1200,
        "panel_moment": actions[index - 1],
        "shot_type": ["wide", "medium", "insert", "two-shot"][index - 1],
        "composition_geometry": "maintain left-to-right screen direction",
        "video_prompt": "两人从发现彼此连续行动到共同查看手机",
        "motion_timeline": [
            {"at_ms": at_ms, "action": action}
            for at_ms, action in zip((0, 400, 800, 1100), actions, strict=True)
        ],
    }
