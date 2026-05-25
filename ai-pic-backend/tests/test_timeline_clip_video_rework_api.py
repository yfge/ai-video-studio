import json

from app.models.script import Episode, Script, Story
from app.models.task import Task
from app.models.timeline import MediaAsset
from app.models.user import User
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.services.video.video_task_timeline_rework_updater import (
    apply_timeline_rework_result,
)
from sqlalchemy.orm import Session


def _bootstrap_episode(db: Session) -> tuple[Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(title="Video Rework Story", genre="short_drama", user_id=user.id)
    episode = Episode(story=story, episode_number=1, title="Pilot")
    script = Script(
        episode=episode,
        title="Pilot Script",
        content="A: hello",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
    )
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _timeline_spec(episode: Episode, script: Script) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 1200,
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    {
                        "clip_id": "dialogue_scene_001_beat_001_001",
                        "track_type": "dialogue",
                        "scene_id": "scene_001",
                        "beat_id": "beat_001",
                        "ordinal": 1,
                        "start_ms": 0,
                        "end_ms": 1200,
                        "duration_ms": 1200,
                        "source": {
                            "kind": "audio_timeline_beat",
                            "scene_id": "scene_001",
                            "beat_id": "beat_001",
                            "audio_timeline_version": 1,
                        },
                        "source_refs": {
                            "scene_beat_id": "beat_001",
                            "audio_timeline_version": 1,
                        },
                    }
                ],
            }
        ],
    }


def _append_video_clip(
    spec: dict,
    *,
    clip_id: str,
    start_asset: MediaAsset | None = None,
    video_asset: MediaAsset | None = None,
) -> dict:
    clip = {
        "clip_id": clip_id,
        "track_type": "video",
        "scene_id": "scene_001",
        "beat_id": "beat_001",
        "ordinal": 1,
        "start_ms": 0,
        "end_ms": 1200,
        "duration_ms": 1200,
        "source": {
            "kind": "audio_timeline_beat",
            "scene_id": "scene_001",
            "beat_id": "beat_001",
            "audio_timeline_version": 1,
        },
        "source_refs": {
            "scene_beat_id": "beat_001",
            "audio_timeline_version": 1,
        },
        "text": "A rainy close-up of the lead character.",
    }
    if start_asset is not None:
        clip["start_frame_asset_ref"] = {
            "kind": "start_frame",
            "media_asset_id": start_asset.id,
        }
    if video_asset is not None:
        clip["asset_ref"] = {
            "kind": "generated_video",
            "media_asset_id": video_asset.id,
        }
    spec["tracks"].append({"track_type": "video", "clips": [clip]})
    return spec


def _media_asset(
    db: Session,
    *,
    asset_type: str,
    origin: str,
    file_url: str,
    mime_type: str,
) -> MediaAsset:
    asset = MediaAsset(
        asset_type=asset_type,
        origin=origin,
        file_url=file_url,
        mime_type=mime_type,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def _create_timeline(client, episode: Episode, script: Script, spec: dict) -> dict:
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Video Rework Timeline",
            "spec": spec,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_timeline_clip_video_rework_queues_provider_task(
    client, db_session, monkeypatch
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["task_id"] = task.id
        dispatched["payload"] = payload
        dispatched["user_id"] = current_user.id

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
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clip(
            _timeline_spec(episode, script),
            clip_id=clip_id,
            start_asset=start_asset,
        ),
    )

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "prompt": "Regenerate the rainy close-up with steadier motion.",
            "model": "keling:kling-v2",
            "duration": 1.2,
            "resolution": "720p",
        },
    )

    assert response.status_code == 200
    task_id = response.json()["task_id"]
    task = db_session.get(Task, task_id)
    assert task is not None
    params = json.loads(task.parameters)
    assert params["timeline_id"] == timeline["id"]
    assert params["timeline_version"] == timeline["version"]
    assert params["clip_id"] == clip_id
    assert params["image_url"] == "https://example.com/start.png"
    assert params["asset_role"] == "generated_video"
    assert params["auto_render"] is True
    assert params["render_type"] == "final"
    assert params["render_preset"] == {"fps": 24, "resolution": "1080x1920"}
    assert dispatched["task_id"] == task_id
    assert dispatched["payload"]["clip_id"] == clip_id


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
    media_url = replacement["media_asset"]["file_url"]
    assert media_url == "https://example.com/generated-v2.mp4"
    assert replacement["source_ref"]["preserves_clip_id"] is True
