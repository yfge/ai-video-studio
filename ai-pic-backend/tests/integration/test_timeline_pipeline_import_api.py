import json

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.services.storyboard.storyboard_image_autogen import (
    STORYBOARD_IMAGE_METADATA_KEY,
)


def _patch_session_local(monkeypatch, session_factory) -> None:
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _create_user(db_session, *, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_script_with_scenes(db_session, *, user: User) -> tuple[Script, list[int]]:
    story = Story(
        title="Timeline Pipeline Story",
        genre="drama",
        user_id=user.id,
    )
    episode = Episode(
        title="Episode 1",
        episode_number=1,
        duration_minutes=6,
        story=story,
    )
    script = Script(title="Script 1", content="", episode=episode)
    scenes = [
        Scene(script=script, scene_number="1", slug_line="INT. ROOM - DAY"),
        Scene(script=script, scene_number="2", slug_line="EXT. STREET - NIGHT"),
    ]
    db_session.add_all([story, episode, script, *scenes])
    db_session.commit()
    return script, [scene.id for scene in scenes]


def _create_task(db_session, *, user_id: int) -> Task:
    task = Task(
        title="Timeline pipeline",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user_id,
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_process_timeline_pipeline_imports_audio_timeline_to_timeline_spec(
    db_session, test_db, monkeypatch
):
    import app.api.v1.endpoints.scripts.timeline_pipeline as timeline_pipeline_endpoint
    import app.services.timeline_pipeline_runner as timeline_pipeline_runner

    user = _create_user(db_session, username="pipeline_import_admin")
    script, scene_ids = _create_script_with_scenes(db_session, user=user)
    task = _create_task(db_session, user_id=user.id)
    called: dict[str, object] = {
        "timeline": False,
        "storyboard": False,
        "shot_plan": False,
    }

    async def _fake_generate_dialogue_with_duration_control(
        db_session,  # noqa: ANN001
        *,
        scenes: list[Scene],
        overwrite_beats: bool,
        **_: object,
    ) -> dict:
        called["scene_ids"] = [scene.id for scene in scenes]
        called["overwrite_beats"] = overwrite_beats
        return {"success": True, "statistics": {"duration_ratio": 1.0}}

    async def _fake_generate_episode_audio_timeline(
        db_session,  # noqa: ANN001
        **kwargs: object,
    ) -> dict:
        script_arg = kwargs["script"]
        called["timeline"] = True
        return {
            "script_id": script_arg.id,
            "episode_audio": {
                "oss_url": "https://cdn.example.com/pipeline.mp3",
                "duration_seconds": 2.4,
                "version": 7,
            },
            "beats": [
                {
                    "scene_id": scene_ids[0],
                    "scene_number": 1,
                    "beat_id": 501,
                    "beat_type": "dialogue",
                    "text": "hello",
                    "start_ms": 0,
                    "end_ms": 1200,
                },
                {
                    "scene_id": scene_ids[1],
                    "scene_number": 2,
                    "beat_id": 502,
                    "beat_type": "pause",
                    "text": "",
                    "start_ms": 1200,
                    "end_ms": 1700,
                },
                {
                    "scene_id": scene_ids[1],
                    "scene_number": 2,
                    "beat_id": 503,
                    "beat_type": "dialogue",
                    "text": "world",
                    "start_ms": 1700,
                    "end_ms": 2400,
                },
            ],
        }

    def _fake_generate_storyboard_support_from_timeline_spec(
        *_: object, **__: object
    ) -> dict:
        called["storyboard"] = True
        return {
            "frames": [
                {
                    "frame_id": "frame-1",
                    "description": "has refs",
                    "reference_images": ["https://example.com/ref.png"],
                },
                {"frame_id": "frame-2", "description": "missing refs"},
            ],
            "meta": {},
        }

    monkeypatch.setattr(
        timeline_pipeline_runner,
        "generate_dialogue_with_duration_control",
        _fake_generate_dialogue_with_duration_control,
    )
    monkeypatch.setattr(
        timeline_pipeline_runner,
        "generate_episode_audio_timeline",
        _fake_generate_episode_audio_timeline,
    )

    async def _fake_generate_timeline_shot_plan_from_current_version(
        db_session,  # noqa: ANN001
        timeline,
        *,
        user_id: int,
    ):
        called["shot_plan"] = True
        called["shot_plan_expected_version"] = timeline.version
        timeline.version += 1
        spec = {**timeline.spec, "version": timeline.version}
        for track in spec["tracks"]:
            if track["track_type"] != "video":
                continue
            for clip in track["clips"]:
                refs = clip.setdefault("source_refs", {})
                refs["timeline_shot_plan"] = {
                    "clip_id": clip["clip_id"],
                    "duration_ms": clip["duration_ms"],
                    "plot": clip.get("text") or "plot",
                    "dialogue_source": clip.get("text") or "dialogue",
                    "visual_prompt": "timeline shot plan visual prompt",
                    "video_prompt": "timeline shot plan video prompt",
                    "character_anchor": "cartoon robot",
                    "camera": "push in",
                    "action": "points at timeline",
                    "provider": "deepseek",
                    "model": "deepseek-v4-flash",
                }
        timeline.spec = spec
        db_session.add(timeline)
        db_session.commit()
        db_session.refresh(timeline)
        return timeline

    monkeypatch.setattr(
        timeline_pipeline_runner,
        "generate_timeline_shot_plan_from_current_version",
        _fake_generate_timeline_shot_plan_from_current_version,
    )
    import app.services.script.timeline_storyboard_queue as timeline_storyboard_queue

    monkeypatch.setattr(
        timeline_storyboard_queue,
        "generate_storyboard_support_from_timeline_spec",
        _fake_generate_storyboard_support_from_timeline_spec,
    )
    import app.services.storyboard.storyboard_image_autogen as storyboard_image_autogen

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
    _patch_session_local(monkeypatch, test_db)

    timeline_pipeline_endpoint._process_timeline_pipeline_task(
        task.id,
        {
            "script_id": script.id,
            "use_duration_control": True,
            "min_pause_seconds": 2.25,
        },
        user.id,
    )

    session = test_db()
    try:
        refreshed = session.query(Task).filter(Task.id == task.id).first()
        assert refreshed is not None
        assert refreshed.status == TaskStatus.COMPLETED
        assert refreshed.result_file_path == f"script:{script.id}:timeline_pipeline"
        params = json.loads(refreshed.parameters)
        image_meta = params[STORYBOARD_IMAGE_METADATA_KEY]
        assert image_meta["status"] == "queued"
        assert image_meta["child_task_id"] == queued_image_task["task_id"]
        assert image_meta["queued_frame_indexes"] == [0]
        assert image_meta["skipped_frame_indexes"] == [1]
        assert queued_image_task["payload"]["script_id"] == script.id
        assert queued_image_task["payload"]["frame_indexes"] == [0]
        assert queued_image_task["payload"]["require_reference_images"] is True
        assert queued_image_task["user_id"] == user.id
        timeline = (
            session.query(Timeline)
            .filter(Timeline.episode_id == script.episode_id)
            .filter(Timeline.script_id == script.id)
            .one()
        )
        assert timeline.source_audio_timeline_version == 7
        tracks = {track["track_type"]: track for track in timeline.spec["tracks"]}
        assert set(tracks) == {"dialogue", "video", "subtitle"}
        assert tracks["dialogue"]["clips"][0]["clip_id"].startswith(
            f"dialogue_scene_{scene_ids[0]}_beat_501_"
        )
        assert [clip["beat_id"] for clip in tracks["video"]["clips"]] == [501, 503]
        assert tracks["video"]["clips"][0]["absorbed_pause_beat_ids"] == [502]
        assert tracks["video"]["clips"][0]["end_ms"] == 1700
        assert (
            tracks["video"]["clips"][0]["source_refs"]["timeline_shot_plan"]["provider"]
            == "deepseek"
        )
    finally:
        session.close()

    assert called["scene_ids"] == scene_ids
    assert called["overwrite_beats"] is True
    assert called["timeline"] is True
    assert called["shot_plan"] is True
    assert called["shot_plan_expected_version"] == 1
    assert called["storyboard"] is True
