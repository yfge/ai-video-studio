import json

from app.models.task import Task
from app.models.timeline import Timeline, TimelineClipAsset
from tests.test_timeline_clip_video_rework_api import (
    _append_video_clip,
    _bootstrap_episode,
    _create_timeline,
    _media_asset,
    _timeline_spec,
)


def test_timeline_clip_video_rework_uses_storyboard_image_lineage(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_queue_service."
        "dispatch_timeline_clip_video_rework_task",
        lambda *_args, **_kwargs: None,
    )
    episode, script = _bootstrap_episode(db_session)
    clip_id = "video_scene_001_beat_001_001"
    timeline_payload = _create_timeline(
        client,
        episode,
        script,
        _append_video_clip(_timeline_spec(episode, script), clip_id=clip_id),
    )
    timeline = db_session.get(Timeline, timeline_payload["id"])
    image_asset = _media_asset(
        db_session,
        asset_type="image",
        origin="generated",
        file_url="https://example.com/storyboard-start.png",
        mime_type="image/png",
    )
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            track_type="video",
            asset_role="storyboard_image",
            media_asset_id=image_asset.id,
            source="storyboard_image_generation",
            created_by=timeline.created_by,
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/timelines/{timeline.id}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline.version,
            "action": "re_cut",
            "resolution": "720p",
        },
    )

    assert response.status_code == 200, response.text
    task = db_session.get(Task, response.json()["task_id"])
    params = json.loads(task.parameters)
    assert params["image_url"] == "https://example.com/storyboard-start.png"
