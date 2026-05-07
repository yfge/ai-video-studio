import json

import pytest

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User


def _admin_user(db_session) -> User:
    return db_session.query(User).filter(User.username == "test_admin").one()


def _create_user(db_session, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_story_episode_script(db_session, user: User, *, with_timeline: bool):
    story = Story(
        title="逆光之下",
        genre="urban",
        synopsis="摄影师卷入商业阴谋。",
        user_id=user.id,
    )
    episode = Episode(
        story=story,
        episode_number=6,
        title="真相逼近",
        summary="关键证据浮出水面。",
    )
    script = Script(
        episode=episode,
        title="第6集剧本",
        content="林深：不是你想的那样。",
        format_type="screenplay",
        language="zh-CN",
        version="v3",
        extra_metadata={
            "storyboard": {
                "frames": [{"frame_id": "04-3-02", "start_ms": 78800, "end_ms": 80780}]
            }
        },
    )
    db_session.add_all([story, episode, script])
    db_session.commit()
    db_session.refresh(story)
    db_session.refresh(episode)
    db_session.refresh(script)

    if with_timeline:
        episode.extra_metadata = {
            "audio_timeline": {
                "script_id": script.id,
                "beats": [
                    {
                        "start_ms": 78800,
                        "end_ms": 80780,
                        "dialogue_excerpt": "不是你想的那样。",
                    }
                ],
            }
        }
        db_session.commit()
        db_session.refresh(episode)

    return story, episode, script


def _create_task(
    db_session,
    user: User,
    *,
    title: str,
    task_type: TaskType,
    status: TaskStatus,
    target_business_id: str | None = None,
    parameters: dict | None = None,
):
    task = Task(
        title=title,
        description=f"{title} detail",
        task_type=task_type,
        status=status,
        prompt="prompt",
        parameters=json.dumps(parameters or {}),
        target_business_id=target_business_id,
        error_message="failed reason" if status == TaskStatus.FAILED else None,
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.mark.integration
def test_workbench_summary_aggregates_user_state(client, db_session):
    user = _admin_user(db_session)
    _, episode, script = _create_story_episode_script(
        db_session, user, with_timeline=True
    )

    _create_task(
        db_session,
        user,
        title="时间轴生成",
        task_type=TaskType.TIMELINE_PIPELINE,
        status=TaskStatus.PROCESSING,
        target_business_id=script.business_id,
        parameters={"progress": 62},
    )
    _create_task(
        db_session,
        user,
        title="图像生成",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        status=TaskStatus.FAILED,
        target_business_id=episode.business_id,
    )
    _create_task(
        db_session,
        user,
        title="剧集生成",
        task_type=TaskType.EPISODE_GENERATION,
        status=TaskStatus.PENDING,
    )

    response = client.get("/api/v1/workbench/summary")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["metrics"] == {
        "pending_tasks": 1,
        "running_tasks": 1,
        "failed_tasks": 1,
        "continuable_episodes": 1,
    }
    assert data["recent_episodes"][0]["current_stage"] == "storyboard_ready"
    assert data["recent_episodes"][0]["script_ready"] is True
    assert data["recent_episodes"][0]["timeline_ready"] is True
    assert data["recent_episodes"][0]["storyboard_ready"] is True
    assert data["recent_episodes"][0]["latest_script_id"] == script.id
    assert {task["status"] for task in data["task_queue"]} >= {
        "pending",
        "processing",
        "failed",
    }
    processing = next(task for task in data["task_queue"] if task["status"] == "processing")
    assert processing["progress"] == 62


@pytest.mark.integration
def test_workbench_summary_is_user_scoped(client, db_session):
    current_user = _admin_user(db_session)
    other_user = _create_user(db_session, "other_operator")
    _create_story_episode_script(db_session, current_user, with_timeline=False)
    other_story, other_episode, _ = _create_story_episode_script(
        db_session, other_user, with_timeline=True
    )
    _create_task(
        db_session,
        other_user,
        title="Other Task",
        task_type=TaskType.TIMELINE_PIPELINE,
        status=TaskStatus.FAILED,
        target_business_id=other_episode.business_id,
    )

    response = client.get("/api/v1/workbench/summary")

    assert response.status_code == 200, response.text
    data = response.json()
    story_ids = {episode["story_id"] for episode in data["recent_episodes"]}
    task_titles = {task["title"] for task in data["task_queue"]}
    assert other_story.id not in story_ids
    assert "Other Task" not in task_titles
