from app.models.task import TaskStatus
from app.repositories.story_novel_repository import StoryNovelRepository
from app.services.story import story_novel_task_processor as processor
from sqlalchemy.orm import sessionmaker
from tests.unit.test_story_novel_longform import _setup


def test_pending_task_can_be_claimed_only_once(db_session):
    _user, _story, _service, _revision, task, *_ = _setup(db_session)
    task.status = TaskStatus.PENDING
    db_session.commit()
    repo = StoryNovelRepository(db_session)

    claimed = repo.claim_pending_task(task.id)

    assert claimed is not None
    assert claimed.status == TaskStatus.PROCESSING
    assert repo.claim_pending_task(task.id) is None


def test_duplicate_worker_delivery_executes_operation_once(db_session, monkeypatch):
    user, _story, _service, _revision, task, *_ = _setup(db_session)
    task.status = TaskStatus.PENDING
    db_session.commit()
    factory = sessionmaker(bind=db_session.get_bind())
    calls = []

    monkeypatch.setattr(processor, "SessionLocal", factory)
    monkeypatch.setattr(
        processor,
        "_execute_operation",
        lambda *_args, **_kwargs: calls.append("executed"),
    )

    processor.process_story_novel_task(task.id, {"operation": "ignored"}, user.id)
    processor.process_story_novel_task(task.id, {"operation": "ignored"}, user.id)

    db_session.expire_all()
    assert StoryNovelRepository(db_session).task(task.id).status == TaskStatus.COMPLETED
    assert calls == ["executed"]
