import json

from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
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
    refreshed_script = session.query(Script).filter_by(id=script_id).first()
    storyboard = (refreshed_script.extra_metadata or {}).get("storyboard") or {}
    return storyboard.get("frames") or []


def test_storyboard_image_task_requires_reference_images(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [{"scene_number": 1, "description": "Frame without refs"}]
            }
        }
    )
    task = _create_storyboard_task(db_session, user.id)
    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task

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
        assert refreshed_task.status == TaskStatus.FAILED
        assert "缺少参考图" in refreshed_task.error_message
        assert frames and "image_url" not in frames[0]
    finally:
        session.close()


def test_storyboard_image_task_forwards_required_frame_references(
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
                        "description": "Frame with refs",
                        "reference_images": ["https://example.com/ref.png"],
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
        assert captured["refs"] == ["https://example.com/ref.png"]
        assert frames[0]["image_url"]
        assert frames[0]["image_gen"]["reference_images_count"] == 1
    finally:
        session.close()


def test_storyboard_image_payload_preserves_generation_options(monkeypatch):
    from app.api.v1.endpoints.storyboard import media

    monkeypatch.setattr(
        media,
        "resolve_storyboard_aspect_ratio",
        lambda db, *, script, requested: requested or "16:9",
    )
    request = media.StoryboardImageRequest(
        frames=[0],
        model="openai:gpt-image-2",
        generation_profile="high-fidelity",
        size="1536x1024",
        strength=0.35,
        count=3,
        require_reference_images=True,
    )

    payload = media._build_storyboard_image_payload(
        db=object(),
        script=object(),
        script_id=129,
        request=request,
    )

    assert payload["model"] == "openai:gpt-image-2"
    assert payload["generation_profile"] == "high-fidelity"
    assert payload["size"] == "1536x1024"
    assert payload["strength"] == 0.35
    assert payload["count"] == 3
    assert payload["require_reference_images"] is True


def test_queue_storyboard_image_generation_filters_frames_without_references(
    db_session, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "scene_number": 1,
                        "description": "Frame with refs",
                        "reference_images": ["https://example.com/ref.png"],
                    },
                    {"scene_number": 2, "description": "Frame without refs"},
                ]
            }
        }
    )

    import app.services.storyboard.storyboard_image_autogen as autogen

    captured: dict = {}

    def _fake_delay(task_id: int, payload: dict, user_id: int) -> None:
        captured["task_id"] = task_id
        captured["payload"] = payload
        captured["user_id"] = user_id

    monkeypatch.setattr(autogen.storyboard_image_generate_task, "delay", _fake_delay)

    result = autogen.queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        require_reference_images=True,
    )

    assert result.status == "queued"
    assert result.child_task_id is not None
    assert result.queued_frame_indexes == [0]
    assert result.skipped_frame_indexes == [1]
    assert captured["payload"]["frame_indexes"] == [0]
    assert captured["payload"]["model"] == "gpt-image-2"
    assert captured["payload"]["keyframe_mode"] == "single"
    assert captured["payload"]["count"] == 1
    assert captured["payload"]["require_reference_images"] is True
    assert captured["user_id"] == user.id

    task = db_session.query(Task).filter_by(id=result.child_task_id).first()
    assert task is not None
    payload = json.loads(task.parameters)
    assert payload["frame_indexes"] == [0]
    assert payload["frames"] == [0]


def test_queue_storyboard_image_generation_skips_when_no_reference_frames(
    db_session, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {"scene_number": 1, "description": "Frame without refs"},
                    {"scene_number": 2, "reference_images": []},
                ]
            }
        }
    )

    import app.services.storyboard.storyboard_image_autogen as autogen

    def _unexpected_delay(*_args, **_kwargs) -> None:
        raise AssertionError("no child task should be queued")

    monkeypatch.setattr(
        autogen.storyboard_image_generate_task,
        "delay",
        _unexpected_delay,
    )

    result = autogen.queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        require_reference_images=True,
    )

    assert result.status == "skipped"
    assert result.child_task_id is None
    assert result.reason == "no_reference_images"
    assert result.queued_frame_indexes == []
    assert result.skipped_frame_indexes == [0, 1]
