from importlib import import_module
from types import SimpleNamespace

import pytest
from app.api.v1.endpoints.stories import novel_task_queue
from app.core.database import Base, get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story
from app.models.user import User
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def outline(status="confirmed", version=1):
    return {
        "status": status,
        "version": version,
        "thread_schedule_version": 1,
        "thread_payoffs": [],
        "chapters": [
            {
                "position": 1,
                "title": "第一章",
                "goal": "发现异常",
                "key_events": ["主角收到异常信号"],
                "character_focus": ["主角"],
                "open_threads": [],
                "end_state": "主角决定追查",
            },
            {
                "position": 2,
                "title": "第二章",
                "goal": "主角公开真相",
                "key_events": ["主角公开真相"],
                "character_focus": ["主角"],
                "open_threads": [],
                "end_state": "主角公开真相",
            },
        ],
    }


def seed_v1():
    return {
        "schema": "story_seed_v1",
        "title": "流程验收故事",
        "premise": "主角发现异常",
        "outline": "第1章至第2章",
        "protagonists": [
            {
                "virtual_ip_business_id": "vip-main",
                "initial_state": "尚未知情",
            }
        ],
        "world_constraints": [],
        "central_conflict": "真相与秩序冲突",
        "ending_direction": "主角公开真相",
        "content_constraints": [],
    }


def seed_v2():
    return {
        **seed_v1(),
        "schema": "story_seed_v2",
        "outline_text": "第1章至第2章",
        "structured_outline": outline(),
    }


@pytest.fixture
def process_api(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    import_module("app.models")
    engine = create_engine(
        f"sqlite:///{tmp_path / 'story-novel-process.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with sessions() as db:
        user = User(
            username="process_owner",
            email="process-owner@example.com",
            hashed_password="not-used",
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=True,
            is_superuser=True,
        )
        db.add(user)
        db.flush()
        story = Story(
            user_id=user.id,
            title="流程验收故事",
            genre="mystery",
            premise="主角发现异常",
            synopsis="第1章至第2章",
            main_conflict="真相与秩序冲突",
            resolution="主角公开真相",
            workflow_mode="novel_adaptation_v1",
            story_seed=seed_v1(),
            story_seed_schema="story_seed_v1",
            story_seed_status="draft",
            story_seed_version=1,
        )
        db.add(story)
        db.commit()
        user_id, story_id, story_business_id = user.id, story.id, story.business_id

    def override_db():
        with sessions() as db:
            yield db

    current_user = SimpleNamespace(id=user_id, is_admin=True, is_superuser=True)
    queued = []

    def capture_task(name, args=None, **_kwargs):
        queued.append({"name": name, "args": args or []})

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = lambda: current_user
    monkeypatch.setattr(novel_task_queue.celery_app, "send_task", capture_task)
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(
                client=client,
                sessions=sessions,
                user_id=user_id,
                story_id=story_id,
                story_business_id=story_business_id,
                current_user=current_user,
                queued=queued,
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_active_user, None)
        engine.dispose()


def persist_confirmed_seed(context):
    with context.sessions() as db:
        story = db.get(Story, context.story_id)
        story.story_seed = seed_v2()
        story.story_seed_schema = "story_seed_v2"
        story.story_seed_status = "confirmed"
        story.story_seed_version = 3
        db.commit()
