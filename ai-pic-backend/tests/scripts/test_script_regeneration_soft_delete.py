import pytest
from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
from tests.factories import (
    EpisodeFactory,
    ScriptFactory,
    StoryFactory,
    UserFactory,
    setup_factories,
)


def _patch_session_local(monkeypatch, session_factory):
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


@pytest.mark.unit
def test_script_regeneration_creates_new_script_and_soft_deletes_old(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)

    user = UserFactory()
    story = StoryFactory(user_id=user.id)
    episode = EpisodeFactory(story=story)
    old_script = ScriptFactory(episode=episode, version="1.0")

    task = Task(
        title="Script regeneration",
        task_type=TaskType.SCRIPT_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    _patch_session_local(monkeypatch, test_db)

    import app.services.script.regeneration_generation as script_regeneration_generation
    from app.services.script.regeneration_task_processor import (
        process_script_regeneration_task,
    )

    async def fake_quality_gate(**kwargs):
        result = dict(kwargs["result"])
        quality_gate = {"passed": True, "source": "test"}
        result["quality_gate"] = quality_gate
        return result, kwargs["content"], quality_gate

    monkeypatch.setattr(
        script_regeneration_generation,
        "enforce_script_quality_gate_with_repair",
        fake_quality_gate,
    )

    process_script_regeneration_task(
        task.id,
        {"script_id": old_script.id},
        user.id,
    )

    session = test_db()
    try:
        old_refreshed = session.query(Script).filter_by(id=old_script.id).first()
        assert old_refreshed is not None
        assert old_refreshed.is_deleted is True

        completed_task = session.query(Task).filter_by(id=task.id).first()
        assert completed_task is not None
        assert completed_task.status == TaskStatus.COMPLETED
        assert isinstance(completed_task.result_file_path, str)
        assert completed_task.result_file_path.startswith("script:")

        new_script_id = int(completed_task.result_file_path.split(":", 1)[1])
        new_script = session.query(Script).filter_by(id=new_script_id).first()
        assert new_script is not None
        assert new_script.is_deleted is False
        assert new_script.version == "1.1"
        assert str(new_script.title).endswith("(v1.1)")

        meta = new_script.extra_metadata or {}
        assert meta.get("parent_script_id") == old_script.id
        assert meta.get("parent_script_business_id") == old_script.business_id
    finally:
        session.close()
