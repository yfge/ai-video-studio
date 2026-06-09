from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _patch_session_local(monkeypatch, session_factory):
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _patch_storyboard_generate(monkeypatch, *, image_gen_factory):
    import app.services.storyboard.storyboard_image_generation as sb_gen

    async def _fake_generate_storyboard_image_urls(**kwargs):  # noqa: ANN001
        prompt = kwargs.get("prompt") or ""
        return {
            "urls": ["https://example.com/generated.png"],
            "provider": "mock-provider",
            "model": "mock-model",
            "style_spec": None,
            "style_spec_resolution": None,
            "image_gen": image_gen_factory(prompt),
        }

    monkeypatch.setattr(
        sb_gen, "generate_storyboard_image_urls", _fake_generate_storyboard_image_urls
    )


def test_storyboard_image_task_persists_image_gen_single(
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
                        "description": "Frame 1",
                        "reference_images": ["https://example.com/ref.png"],
                    }
                ]
            }
        }
    )
    task = Task(
        title="Storyboard image generation",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task

    monkeypatch.setattr(
        sb_image_task.prompt_manager,
        "render_prompt",
        lambda *_args, **_kwargs: "test-prompt",
    )

    _patch_storyboard_generate(
        monkeypatch,
        image_gen_factory=lambda _prompt: {
            "generation_profile": "identity",
            "image_fidelity": 0.7,
            "human_fidelity": 0.6,
            "image_reference": "subject",
        },
    )

    sb_image_task._process_storyboard_image_task(
        task.id,
        script.id,
        [0],
        keyframe_mode="single",
    )

    session = test_db()
    try:
        refreshed = session.query(Script).filter_by(id=script.id).first()
        frames = ((refreshed.extra_metadata or {}).get("storyboard") or {}).get(
            "frames"
        ) or []
        assert frames and isinstance(frames[0], dict)
        meta = frames[0].get("image_gen")
        assert isinstance(meta, dict)
        assert meta["generation_profile"] == "identity"
        assert meta["image_fidelity"] == 0.7
        assert meta["human_fidelity"] == 0.6
        assert meta["image_reference"] == "subject"
    finally:
        session.close()


def test_storyboard_image_task_persists_image_gen_start_end(
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
                        "description": "Frame 1",
                        "reference_images": ["https://example.com/ref.png"],
                    }
                ]
            }
        }
    )
    task = Task(
        title="Storyboard image generation",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task

    monkeypatch.setattr(
        sb_image_task.prompt_manager,
        "render_prompt",
        lambda *_args, **_kwargs: "test-prompt",
    )

    def _image_gen_factory(prompt: str) -> dict:
        role = "single"
        if isinstance(prompt, str) and "Opening keyframe" in prompt:
            role = "start"
        elif isinstance(prompt, str) and "Ending keyframe" in prompt:
            role = "end"
        return {
            "keyframe_role": role,
            "generation_profile": "identity",
            "image_fidelity": 0.7,
            "human_fidelity": 0.6,
            "image_reference": "subject",
        }

    _patch_storyboard_generate(monkeypatch, image_gen_factory=_image_gen_factory)

    sb_image_task._process_storyboard_image_task(
        task.id,
        script.id,
        [0],
        keyframe_mode="start_end",
        start_enabled=True,
        end_enabled=True,
    )

    session = test_db()
    try:
        refreshed = session.query(Script).filter_by(id=script.id).first()
        frames = ((refreshed.extra_metadata or {}).get("storyboard") or {}).get(
            "frames"
        ) or []
        assert frames and isinstance(frames[0], dict)
        frame = frames[0]
        start_meta = frame.get("start_image_gen")
        end_meta = frame.get("end_image_gen")
        assert isinstance(start_meta, dict)
        assert isinstance(end_meta, dict)
        assert start_meta["keyframe_role"] == "start"
        assert end_meta["keyframe_role"] == "end"
        assert frame.get("image_gen") == start_meta
    finally:
        session.close()
