from app.models.task import Task, TaskStatus, TaskType
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _patch_session_local(monkeypatch, session_factory):
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _storyboard_script(frame_count: int):
    return ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {"scene_number": 1, "description": f"Frame {index + 1}"}
                    for index in range(frame_count)
                ]
            }
        }
    )


def _image_task(db_session, user_id: int, status: TaskStatus):
    task = Task(
        title="Storyboard image generation",
        task_type=TaskType.IMAGE_GENERATION,
        status=status,
        user_id=user_id,
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_storyboard_image_task_does_not_restart_cancelled_task(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = _storyboard_script(1)
    task = _image_task(db_session, user.id, TaskStatus.CANCELLED)
    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task

    monkeypatch.setattr(
        sb_image_task,
        "generate_frame_image",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("cancelled task generated an image")
        ),
    )

    sb_image_task._process_storyboard_image_task(task.id, script.id, [0])

    session = test_db()
    try:
        assert session.get(Task, task.id).status == TaskStatus.CANCELLED
    finally:
        session.close()


def test_storyboard_image_task_stops_before_next_frame_after_cancel(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = _storyboard_script(2)
    task = _image_task(db_session, user.id, TaskStatus.PENDING)
    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task
    import app.services.storyboard.dynamic_prompt as dynamic_prompt_pkg

    monkeypatch.setattr(
        dynamic_prompt_pkg,
        "build_dynamic_prompt_bundles",
        lambda *_args, **_kwargs: {},
    )
    generated: list[int] = []

    def cancel_after_first_frame(_frames, index, *_args, **_kwargs):
        generated.append(index)
        session = test_db()
        try:
            session.get(Task, task.id).status = TaskStatus.CANCELLED
            session.commit()
        finally:
            session.close()
        return {"generated_urls": []}

    monkeypatch.setattr(sb_image_task, "generate_frame_image", cancel_after_first_frame)

    sb_image_task._process_storyboard_image_task(task.id, script.id, [0, 1])

    session = test_db()
    try:
        assert generated == [0]
        assert session.get(Task, task.id).status == TaskStatus.CANCELLED
    finally:
        session.close()


def test_storyboard_image_task_fails_without_persisted_images(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = _storyboard_script(1)
    task = _image_task(db_session, user.id, TaskStatus.PENDING)
    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task
    import app.services.storyboard.dynamic_prompt as dynamic_prompt_pkg

    monkeypatch.setattr(
        dynamic_prompt_pkg,
        "build_dynamic_prompt_bundles",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        sb_image_task,
        "generate_frame_image",
        lambda *_args, **_kwargs: {"generated_urls": []},
    )

    sb_image_task._process_storyboard_image_task(task.id, script.id, [0])

    session = test_db()
    try:
        refreshed = session.get(Task, task.id)
        assert refreshed.status == TaskStatus.FAILED
        assert "no persisted images" in refreshed.error_message
    finally:
        session.close()
