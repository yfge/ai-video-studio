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


def test_timeline_clip_video_rework_uses_storyboard_grid_panel_reference(
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
    _, episode, script = _bootstrap_episode(db_session)
    grid_asset = _media_asset(
        db_session,
        asset_type="image",
        origin="generated",
        file_url="https://example.com/storyboard-grid.png",
        mime_type="image/png",
    )
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _timeline_spec_with_grid_panel(episode, script, clip_id, grid_asset),
    )

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "reference_mode": "storyboard_grid_panel",
            "use_storyboard_grid": True,
            "model": "volcengine:doubao-seedance-2-0-260128",
        },
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["reference_mode"] == "storyboard_grid_panel"
    assert params["reference_images"] == ["https://example.com/storyboard-grid.png"]
    assert params["storyboard_grid"]["panel_index"] == 4
    assert params["storyboard_grid"]["sheet_media_asset_id"] == grid_asset.id
    assert params.get("image_url") is None
    assert "Use panel 4 only" in params["prompt"]
    assert "Generate only this shot" in params["prompt"]
    assert dispatched["payload"]["reference_images"] == [
        "https://example.com/storyboard-grid.png"
    ]


def test_video_task_success_preserves_grid_storyboard_reference_metadata(
    client, db_session
):
    user, episode, script = _bootstrap_episode(db_session)
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _timeline_spec_with_video_clip(episode, script, clip_id),
    )
    params = {
        "timeline_rework": {
            "timeline_id": timeline["id"],
            "timeline_version": timeline["version"],
            "clip_id": clip_id,
            "action": "re_cut",
            "asset_role": "generated_video",
            "reference_mode": "storyboard_grid_panel",
            "storyboard_grid": {
                "panel_id": "grid_panel_004",
                "panel_index": 4,
                "sheet_media_asset_id": 501,
            },
        }
    }
    video_task = VideoGenerationTask(
        task_id=None,
        script_id=None,
        frame_index=None,
        user_id=user.id,
        provider="mock-provider",
        provider_task_id="provider-task-grid",
        model="mock-video",
        model_type="text_to_video",
        prompt="Use panel 4 only",
        parameters=json.dumps(params),
        status=VideoGenerationTaskStatus.SUCCEEDED,
    )
    db_session.add(video_task)
    db_session.commit()
    db_session.refresh(video_task)

    apply_timeline_rework_result(
        db_session,
        video_task,
        {"video_url": "https://example.com/generated-grid.mp4", "duration": 1.2},
        params,
    )

    lineage = client.get(
        f"/api/v1/timelines/{timeline['id']}/clip-assets",
        params={"clip_id": clip_id},
    ).json()["items"]
    replacement = [item for item in lineage if item["source"] == "provider_rework"][0]
    assert replacement["source_ref"]["reference_mode"] == "storyboard_grid_panel"
    assert replacement["source_ref"]["storyboard_grid"]["panel_index"] == 4
    assert replacement["media_asset"]["metadata"]["reference_mode"] == (
        "storyboard_grid_panel"
    )
    assert replacement["media_asset"]["metadata"]["storyboard_grid"]["panel_id"] == (
        "grid_panel_004"
    )


def _bootstrap_episode(db: Session) -> tuple[User, Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(title="Video Grid Rework Story", genre="short_drama", user_id=user.id)
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
    return user, episode, script


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
        json={"script_id": script.id, "title": "Video Rework Timeline", "spec": spec},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _timeline_spec_with_grid_panel(
    episode: Episode,
    script: Script,
    clip_id: str,
    grid_asset: MediaAsset,
) -> dict:
    spec = _timeline_spec_with_video_clip(episode, script, clip_id)
    clip = spec["tracks"][-1]["clips"][0]
    clip["source_refs"]["grid_storyboard_panel"] = {
        "panel_id": "grid_panel_004",
        "panel_index": 4,
        "sheet_media_asset_id": grid_asset.id,
        "source_timeline_version": 2,
    }
    clip["storyboard_grid_sheet_asset_ref"] = {
        "kind": "storyboard_grid_sheet",
        "media_asset_id": grid_asset.id,
        "file_url": grid_asset.file_url,
        "panel_id": "grid_panel_004",
        "panel_index": 4,
    }
    spec["support_views"] = {
        "storyboard_grid": {
            "mode": "grid_storyboard.v1",
            "sheet": {"media_asset_id": grid_asset.id, "file_url": grid_asset.file_url},
            "panels": [
                {
                    "panel_id": "grid_panel_004",
                    "panel_index": 4,
                    "clip_id": clip_id,
                    "video_prompt": "镜头保持静止，只捕捉他的犹豫表情",
                }
            ],
        }
    }
    return spec


def _timeline_spec_with_video_clip(
    episode: Episode,
    script: Script,
    clip_id: str,
) -> dict:
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
                "track_type": "video",
                "clips": [
                    {
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
                        "source_refs": {"scene_beat_id": "beat_001"},
                        "text": "A rainy close-up of the lead character.",
                    }
                ],
            }
        ],
    }
