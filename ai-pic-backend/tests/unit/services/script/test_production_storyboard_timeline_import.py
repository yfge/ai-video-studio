from __future__ import annotations

import pytest
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene, SceneBeat
from app.models.task import Task, TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.services.script.production_pipeline import run_auto_timeline_placeholders


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auto_timeline_placeholders_imports_timeline_spec_and_checks_audio(
    db_session, monkeypatch
):
    user = User(
        username="timeline_auto_user",
        email="timeline_auto_user@example.com",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    story = Story(title="Auto Timeline Story", genre="drama", user_id=user.id)
    episode = Episode(title="Episode 1", episode_number=1, story=story)
    script = Script(title="Script 1", content="", episode=episode)
    ready_scene = Scene(
        script=script,
        scene_number="1",
        slug_line="INT. ROOM - DAY",
        extra_metadata={
            "dialogue_audio": {
                "script_id": 1,
                "oss_url": "https://cdn.example.com/scene-1.mp3",
            }
        },
    )
    missing_audio_scene = Scene(
        script=script,
        scene_number="2",
        slug_line="EXT. STREET - NIGHT",
    )
    db_session.add_all([story, episode, script, ready_scene, missing_audio_scene])
    db_session.commit()
    db_session.refresh(script)
    db_session.refresh(ready_scene)
    db_session.refresh(missing_audio_scene)

    ready_scene.extra_metadata = {
        "dialogue_audio": {
            "script_id": script.id,
            "oss_url": "https://cdn.example.com/scene-1.mp3",
        }
    }
    beats = [
        SceneBeat(
            scene_id=ready_scene.id,
            order_index=1,
            beat_type="dialogue",
            dialogue_excerpt="hello",
            duration_seconds=1.0,
            extra_metadata={"start_ms": 0, "end_ms": 1000},
        ),
        SceneBeat(
            scene_id=missing_audio_scene.id,
            order_index=1,
            beat_type="dialogue",
            dialogue_excerpt="world",
            duration_seconds=1.0,
            extra_metadata={"start_ms": 0, "end_ms": 1000},
        ),
    ]
    db_session.add_all([ready_scene, *beats])
    db_session.commit()

    generated_scene_ids: list[int] = []

    async def _fake_generate_scene_dialogue_audio(
        db, *, scene: Scene, script: Script, **_: object
    ) -> dict:
        generated_scene_ids.append(int(scene.id))
        meta = dict(scene.extra_metadata or {})
        meta["dialogue_audio"] = {
            "script_id": script.id,
            "oss_url": f"https://cdn.example.com/scene-{scene.id}.mp3",
        }
        scene.extra_metadata = meta
        db.add(scene)
        db.commit()
        return meta["dialogue_audio"]

    async def _fake_generate_episode_audio_timeline(
        db, *, episode: Episode, script: Script, **_: object
    ) -> dict:
        payload = {
            "script_id": script.id,
            "episode_audio": {
                "oss_url": "https://cdn.example.com/episode.mp3",
                "duration_seconds": 2.0,
                "version": 5,
            },
            "beats": [
                {
                    "scene_id": ready_scene.id,
                    "scene_number": 1,
                    "beat_id": beats[0].id,
                    "beat_type": "dialogue",
                    "text": "hello",
                    "start_ms": 0,
                    "end_ms": 1000,
                },
                {
                    "scene_id": missing_audio_scene.id,
                    "scene_number": 2,
                    "beat_id": beats[1].id,
                    "beat_type": "dialogue",
                    "text": "world",
                    "start_ms": 1000,
                    "end_ms": 2000,
                },
            ],
        }
        episode.extra_metadata = {"audio_timeline": payload}
        db.add(episode)
        db.commit()
        return payload

    def _fake_generate_storyboard_support_from_timeline_spec(
        *_: object, **__: object
    ) -> dict:
        return {
            "frames": [
                {
                    "frame_id": "frame-1",
                    "description": "hello",
                    "reference_images": ["https://example.com/ref.png"],
                }
            ],
            "meta": {},
        }

    import app.services.script.production_storyboard as production_storyboard
    import app.services.storyboard.storyboard_image_autogen as storyboard_image_autogen

    monkeypatch.setattr(
        production_storyboard,
        "generate_scene_dialogue_audio",
        _fake_generate_scene_dialogue_audio,
    )
    monkeypatch.setattr(
        production_storyboard,
        "generate_episode_audio_timeline",
        _fake_generate_episode_audio_timeline,
    )
    monkeypatch.setattr(
        production_storyboard,
        "generate_storyboard_support_from_timeline_spec",
        _fake_generate_storyboard_support_from_timeline_spec,
    )
    queued_image_task: dict[str, object] = {}

    def _fake_delay(task_id: int, payload: dict, user_id: int) -> None:
        queued_image_task["task_id"] = task_id
        queued_image_task["payload"] = payload
        queued_image_task["user_id"] = user_id

    monkeypatch.setattr(
        storyboard_image_autogen.storyboard_image_generate_task,
        "delay",
        _fake_delay,
    )

    result = await run_auto_timeline_placeholders(
        db_session,
        story=story,
        episode=episode,
        script=script,
        hook_schedule={},
        scoring=None,
        user_id=user.id,
    )

    assert generated_scene_ids == [missing_audio_scene.id]
    timeline = db_session.query(Timeline).filter(Timeline.script_id == script.id).one()
    assert timeline.source_audio_timeline_version == 5
    assert timeline.created_by == user.id
    assert result["timeline_spec"] == {
        "id": timeline.id,
        "version": 1,
        "source_audio_timeline_version": 5,
        "action": "created",
    }
    image_meta = result["storyboard_image_generation"]
    assert image_meta["status"] == "queued"
    assert image_meta["queued_frame_indexes"] == [0]
    assert image_meta["skipped_frame_indexes"] == []
    assert queued_image_task["user_id"] == user.id
    assert queued_image_task["payload"]["frame_indexes"] == [0]
    child_task = (
        db_session.query(Task).filter(Task.id == image_meta["child_task_id"]).one()
    )
    assert child_task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION
