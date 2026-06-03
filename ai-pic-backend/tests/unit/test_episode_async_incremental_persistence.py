import json

import pytest
from app.models.script import Episode, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services.episode import async_generation_task as episode_task_processor
from app.services.task_worker import episode_generate_task
from billiard.exceptions import SoftTimeLimitExceeded


@pytest.mark.unit
def test_episode_generate_task_has_episode_specific_time_limit():
    assert episode_generate_task.soft_time_limit >= 3600
    assert episode_generate_task.time_limit > episode_generate_task.soft_time_limit


@pytest.mark.unit
def test_episode_async_keeps_streamed_episode_on_soft_timeout(db_session, monkeypatch):
    user = User(
        username="episode-timeout-user",
        email="episode-timeout@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    story = Story(title="Timeout Story", genre="drama", user_id=user.id)
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    task = Task(
        title=f"生成剧集 - 故事{story.id}",
        description="异步剧集生成",
        task_type=TaskType.EPISODE_GENERATION,
        prompt=f"Episode plan for story {story.id}",
        parameters=json.dumps({"story_id": story.id, "episode_count": 2}),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    streamed_episode = {
        "episode_number": 1,
        "title": "第一集",
        "summary": "主角发现关键危机。",
        "plot_points": [{"description": "发现危机", "timing": "开场"}],
        "character_arcs": None,
        "conflicts": [{"description": "危机逼近", "intensity": "high"}],
        "scene_count": 2,
        "scenes": [
            {"scene_number": 1, "summary": "危机浮现"},
            {"scene_number": 2, "summary": "主角决定行动"},
        ],
    }

    class _StubAIService:
        logger = episode_task_processor.ai_service.logger

        async def generate_episodes(self, **kwargs):
            callbacks = kwargs.get("callbacks")
            if callbacks and callbacks.on_episode:
                callbacks.on_episode(
                    streamed_episode,
                    {
                        "prompt": "episode prompt",
                        "provider": "stub-provider",
                        "model": "stub-model",
                        "usage": {"total_tokens": 12},
                        "outline": {"episode_number": 1},
                        "fallback_from_outline": False,
                        "react_attempts": 1,
                        "duration_accepted": True,
                    },
                )
            raise SoftTimeLimitExceeded()

    stub_service = _StubAIService()
    monkeypatch.setattr(episode_task_processor, "ai_service", stub_service)

    episode_task_processor.run_episode_generation_task(
        db_session,
        task.id,
        {"story_id": story.id, "episode_count": 2, "episode_duration": 10},
        user.id,
    )

    persisted = (
        db_session.query(Episode)
        .filter(Episode.story_id == story.id, Episode.episode_number == 1)
        .one_or_none()
    )
    assert persisted is not None
    assert persisted.is_deleted is False
    assert persisted.title == "第一集"

    db_session.refresh(task)
    assert task.status == TaskStatus.FAILED
    assert "SoftTimeLimitExceeded" in (task.error_message or "")
