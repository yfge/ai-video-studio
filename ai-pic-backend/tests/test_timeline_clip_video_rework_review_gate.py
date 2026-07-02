from tests.test_timeline_clip_video_rework_api import (
    _append_video_clip,
    _bootstrap_episode,
    _create_timeline,
    _media_asset,
    _timeline_spec,
)


def test_timeline_clip_video_rework_requires_operator_review_when_gate_is_pending(
    client, db_session, monkeypatch
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["payload"] = payload

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_queue_service."
        "dispatch_timeline_clip_video_rework_task",
        fake_dispatch,
    )
    episode, script = _bootstrap_episode(db_session)
    start_asset = _media_asset(
        db_session,
        asset_type="image",
        origin="upload",
        file_url="https://example.com/start.png",
        mime_type="image/png",
    )
    clip_id = "video_scene_001_beat_001_001"
    spec = _append_video_clip(
        _timeline_spec(episode, script),
        clip_id=clip_id,
        start_asset=start_asset,
    )
    spec["tracks"][1]["clips"][0]["source_refs"]["human_review"] = {
        "required": True,
        "status": "pending",
    }
    timeline = _create_timeline(client, episode, script, spec)

    blocked = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "resolution": "720p",
        },
    )

    assert blocked.status_code == 400
    assert blocked.json()["detail"] == "operator review required before video generation"

    allowed = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "resolution": "720p",
            "operator_reviewed": True,
        },
    )

    assert allowed.status_code == 200, allowed.text
    assert dispatched["payload"]["operator_reviewed"] is True
