from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import Timeline, TimelineClipAsset
from tests.factories import ScriptFactory, UserFactory, setup_factories


def test_storyboard_image_task_checkpoints_before_later_frame_failure(
    db_session,
    test_db,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory()
    timeline = Timeline(
        episode_id=script.episode_id,
        script_id=script.id,
        title="Timeline checkpoint",
        status="draft",
        spec={
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        {"clip_id": "clip-1"},
                        {"clip_id": "clip-2"},
                    ],
                }
            ]
        },
        version=3,
        created_by=user.id,
    )
    db_session.add(timeline)
    db_session.commit()
    script.extra_metadata = {
        "storyboard": {
            "frames": [
                {
                    "frame_id": "frame-1",
                    "description": "First frame",
                    "timeline_id": timeline.id,
                    "timeline_version": timeline.version,
                    "timeline_clip_id": "clip-1",
                },
                {
                    "frame_id": "frame-2",
                    "description": "Second frame",
                    "timeline_id": timeline.id,
                    "timeline_version": timeline.version,
                    "timeline_clip_id": "clip-2",
                },
            ]
        }
    }
    task = Task(
        title="Storyboard image checkpoint",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user.id,
    )
    db_session.add_all([script, task])
    db_session.commit()

    import app.core.database as database_module
    import app.services.storyboard.dynamic_prompt as dynamic_prompt
    from app.api.v1.endpoints.storyboard import image_task_processor

    monkeypatch.setattr(database_module, "SessionLocal", test_db)
    monkeypatch.setattr(
        dynamic_prompt,
        "build_dynamic_prompt_bundles",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        image_task_processor,
        "load_image_ref_context",
        lambda *_args, **_kwargs: None,
    )

    generated_indexes: list[int] = []

    def generate_frame(frames, frame_index, *_args, **_kwargs):
        generated_indexes.append(frame_index)
        if frame_index == 1:
            raise RuntimeError("second frame provider failure")
        image_url = "https://example.com/generated-frame-1.png"
        frames[frame_index]["start_image_url"] = image_url
        frames[frame_index]["image_url"] = image_url
        return {"generated_urls": [image_url]}

    monkeypatch.setattr(
        image_task_processor,
        "generate_frame_image",
        generate_frame,
    )

    image_task_processor._process_storyboard_image_task(
        task.id,
        script.id,
        [0, 1],
    )
    assert generated_indexes == [0, 1]

    image_task_processor._process_storyboard_image_task(
        task.id,
        script.id,
        [0, 1],
    )
    assert generated_indexes == [0, 1, 1]

    session = test_db()
    try:
        persisted = session.get(Script, script.id)
        frames = persisted.extra_metadata["storyboard"]["frames"]
        assert frames[0]["start_image_url"].endswith("generated-frame-1.png")
        assert not frames[1].get("start_image_url")
        assert session.get(Task, task.id).status == TaskStatus.FAILED
        link = session.query(TimelineClipAsset).filter_by(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id="clip-1",
            asset_role="storyboard_image",
        )
        assert link.one().source == "storyboard_image_generation"
    finally:
        session.close()
