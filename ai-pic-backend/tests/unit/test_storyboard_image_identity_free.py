from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
from app.services.storyboard.storyboard_image_queue_inputs import (
    frame_requires_reference_images,
)
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _patch_session_local(monkeypatch, session_factory):
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _create_storyboard_task(db_session, user_id: int) -> Task:
    task = Task(
        title="Storyboard image generation",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user_id,
    )
    db_session.add(task)
    db_session.commit()
    return task


def _storyboard_frames(session, script_id: int):
    script = session.query(Script).filter_by(id=script_id).first()
    storyboard = (script.extra_metadata or {}).get("storyboard") or {}
    return storyboard.get("frames") or []


def test_nonempty_character_objects_remain_reference_bound():
    assert frame_requires_reference_images({"characters": [{"name": "Lin Xia"}]})
    assert not frame_requires_reference_images({"characters": []})


def test_storyboard_image_task_allows_explicit_identity_free_frame_without_reference(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "scene_number": 1,
                        "description": "Empty hallway insert",
                        "characters": [],
                    }
                ]
            }
        }
    )
    task = _create_storyboard_task(db_session, user.id)
    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task
    import app.services.storyboard.storyboard_image_generation as sb_gen

    captured = {}
    monkeypatch.setattr(sb_image_task, "ai_service", mock_ai_service)
    monkeypatch.setattr(
        sb_image_task.prompt_manager,
        "render_prompt",
        lambda *_args, **_kwargs: "test-prompt",
    )

    async def _fake_generate_storyboard_image_urls(**kwargs):  # noqa: ANN001
        captured["refs"] = kwargs.get("refs")
        return {
            "urls": ["https://example.com/generated.png"],
            "provider": "mock-provider",
            "model": "mock-model",
            "style_spec": None,
            "style_spec_resolution": None,
            "image_gen": {"reference_images_count": len(kwargs.get("refs") or [])},
        }

    monkeypatch.setattr(
        sb_gen, "generate_storyboard_image_urls", _fake_generate_storyboard_image_urls
    )
    sb_image_task._process_storyboard_image_task(
        task.id,
        script.id,
        [0],
        keyframe_mode="single",
        require_reference_images=True,
    )

    session = test_db()
    try:
        refreshed_task = session.query(Task).filter_by(id=task.id).first()
        frames = _storyboard_frames(session, script.id)
        assert refreshed_task.status == TaskStatus.COMPLETED
        assert captured["refs"] == []
        assert frames[0]["image_url"]
    finally:
        session.close()


def test_queue_storyboard_image_generation_includes_identity_free_frames(
    db_session, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "description": "Character shot",
                        "characters": ["Lin Xia"],
                        "reference_images": ["https://example.com/ref.png"],
                    },
                    {"description": "Environment insert", "characters": []},
                    {"description": "Legacy unclassified frame"},
                ]
            }
        }
    )

    import app.services.storyboard.storyboard_image_autogen as autogen

    captured: dict = {}
    monkeypatch.setattr(
        autogen.storyboard_image_generate_task,
        "delay",
        lambda _task_id, payload, _user_id: captured.update(payload=payload),
    )
    result = autogen.queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        require_reference_images=True,
    )

    assert result.queued_frame_indexes == [0, 1]
    assert result.skipped_frame_indexes == [2]
    assert captured["payload"]["frame_indexes"] == [0, 1]
    assert captured["payload"]["require_reference_images"] is True
