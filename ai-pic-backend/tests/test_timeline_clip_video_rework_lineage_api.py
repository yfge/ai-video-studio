import json

from app.models.user import User
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.services.video.video_task_timeline_rework_updater import (
    apply_timeline_rework_result,
)
from tests.test_timeline_clip_video_rework_api import (
    _append_video_clip,
    _bootstrap_episode,
    _create_timeline,
    _media_asset,
    _timeline_spec,
)


def test_timeline_clip_video_rework_rejects_non_video_clip(client, db_session):
    ep, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(client, ep, script, _timeline_spec(ep, script))
    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/"
        "dialogue_scene_001_beat_001_001/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "prompt": "Regenerate as video.",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "video rework requires a video clip"


def test_video_task_success_records_provider_rework_lineage(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    episode, script = _bootstrap_episode(db_session)
    original_video = _media_asset(
        db_session,
        asset_type="video",
        origin="upload",
        file_url="https://example.com/generated-v1.mp4",
        mime_type="video/mp4",
    )
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clip(
            _timeline_spec(episode, script),
            clip_id=clip_id,
            video_asset=original_video,
        ),
    )
    original_link = client.get(
        f"/api/v1/timelines/{timeline['id']}/clip-assets",
        params={"clip_id": clip_id},
    ).json()["items"][0]
    params = {
        "timeline_rework": {
            "timeline_id": timeline["id"],
            "timeline_version": timeline["version"],
            "clip_id": clip_id,
            "action": "re_cut",
            "asset_role": "generated_video",
            "reason": "steadier motion",
        }
    }
    video_task = VideoGenerationTask(
        task_id=None,
        script_id=None,
        frame_index=None,
        user_id=user.id,
        provider="mock-provider",
        provider_task_id="provider-task-1",
        model="mock-video",
        model_type="image_to_video",
        prompt="Regenerate the clip",
        parameters=json.dumps(params),
        status=VideoGenerationTaskStatus.SUCCEEDED,
    )
    db_session.add(video_task)
    db_session.commit()
    db_session.refresh(video_task)
    apply_timeline_rework_result(
        db_session,
        video_task,
        {"video_url": "https://example.com/generated-v2.mp4", "duration": 1.2},
        params,
    )
    lineage = client.get(
        f"/api/v1/timelines/{timeline['id']}/clip-assets",
        params={"clip_id": clip_id},
    ).json()["items"]
    replacement = [item for item in lineage if item["source"] == "provider_rework"][0]
    assert replacement["clip_id"] == clip_id
    assert replacement["asset_role"] == "generated_video"
    assert replacement["replacement_of_id"] == original_link["id"]
    assert replacement["media_asset"]["file_url"] == "https://example.com/generated-v2.mp4"
    assert replacement["source_ref"]["preserves_clip_id"] is True
