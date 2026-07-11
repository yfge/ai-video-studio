from app.models.timeline import Timeline
from app.models.user import User
from tests.integration.test_production_canvas_api import _create_script_context


def test_timeline_skill_reuses_existing_video_clips_without_provider(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script_context(db_session, user)
    timeline = Timeline(
        episode_id=script.episode_id,
        script_id=script.id,
        title="Reusable Timeline",
        status="draft",
        version=3,
        spec={},
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(timeline)
    db_session.commit()
    db_session.refresh(timeline)
    timeline.spec = {
        "spec_version": "timeline.v1",
        "timeline_id": timeline.id,
        "episode_id": script.episode_id,
        "script_id": script.id,
        "version": timeline.version,
        "tracks": [
            {
                "track_type": "video",
                "clips": [
                    {
                        "clip_id": "video_scene_1_beat_1_001",
                        "track_type": "video",
                        "scene_id": 1,
                        "scene_number": 1,
                        "beat_id": 1,
                        "beat_type": "dialogue",
                        "text": "主角推开办公室的门。",
                        "start_ms": 0,
                        "end_ms": 3000,
                        "duration_ms": 3000,
                    }
                ],
            }
        ],
    }
    db_session.commit()
    monkeypatch.setattr(
        "app.services.script.timeline_pipeline_queue."
        "timeline_pipeline_generate_task.delay",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("existing Timeline should not dispatch provider pipeline")
        ),
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "复用现有时间线",
            "skill": "timeline.assemble",
            "script_id": script.id,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["task_id"] is None
    assert payload["skill_result"]["status"] == "review"
    assert payload["skill_result"]["outputs"]["timeline_id"] == timeline.id
    assert payload["skill_result"]["outputs"]["storyboard_frame_count"] == 1
    db_session.refresh(script)
    frame = script.extra_metadata["storyboard"]["frames"][0]
    assert frame["source"] == {
        "kind": "timeline_clip",
        "clip_id": "video_scene_1_beat_1_001",
        "track_type": "video",
        "scene_id": 1,
        "beat_id": 1,
        "timeline_id": timeline.id,
        "timeline_version": 3,
    }
