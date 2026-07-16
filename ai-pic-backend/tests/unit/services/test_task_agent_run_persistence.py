import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.services.task_agent_run import persist_task_agent_run


def _create_user(db_session) -> User:
    user = User(
        username="tester",
        email="tester@example.com",
        hashed_password="hashed",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_persist_task_agent_run_story(db_session):
    user = _create_user(db_session)

    story = Story(
        user_id=user.id,
        title="Test Story",
        genre="Drama",
        story_format="short_drama",
        extra_metadata={
            "agent_run": {"provider_used": "openai", "model_used": "gpt-4"}
        },
        generation_prompt="story prompt",
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    task = Task(
        title="生成故事",
        task_type=TaskType.STORY_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"story:{story.id}",
        parameters=json.dumps({"title": "x"}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    persist_task_agent_run(
        task_id=task.id,
        user_id=user.id,
        kind="story",
        db_session=db_session,
    )

    db_session.refresh(task)
    params = json.loads(task.parameters)
    assert params["title"] == "x"
    assert params["agent_run"]["provider_used"] == "openai"
    assert params["agent_run"]["model_used"] == "gpt-4"
    assert params["agent_run"]["prompt"] == "story prompt"
    assert params["agent_run"]["result_ref"]["story_id"] == story.id


def test_persist_task_agent_run_episode(db_session):
    user = _create_user(db_session)

    story = Story(
        user_id=user.id,
        title="Test Story",
        genre="Drama",
        story_format="short_drama",
        extra_metadata={
            "episode_step_outlines": {
                "prompt": "outline prompt",
                "agent_run": {
                    "provider_used": "deepseek",
                    "model_used": "deepseek-chat",
                    "raw_content": "outline raw",
                    "normalized": {"episodes": [{"episode_number": 1}]},
                },
            }
        },
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    ep1 = Episode(
        story_id=story.id,
        episode_number=1,
        title="Ep1",
        extra_metadata={
            "agent_run": {
                "provider_used": "deepseek",
                "model_used": "m1",
                "raw_content": "ep1 raw",
                "normalized": {"episode_number": 1},
            }
        },
        generation_prompt="ep1 prompt",
    )
    ep2 = Episode(
        story_id=story.id,
        episode_number=2,
        title="Ep2",
        extra_metadata={
            "agent_run": {
                "provider_used": "deepseek",
                "model_used": "m2",
                "raw_content": "ep2 raw",
                "normalized": {"episode_number": 2},
            }
        },
        generation_prompt="ep2 prompt",
    )
    db_session.add_all([ep1, ep2])
    db_session.commit()
    db_session.refresh(ep1)
    db_session.refresh(ep2)

    task = Task(
        title="生成剧集",
        task_type=TaskType.EPISODE_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"episodes:{ep1.id},{ep2.id}",
        parameters=json.dumps({"story_id": story.id}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    persist_task_agent_run(
        task_id=task.id,
        user_id=user.id,
        kind="episode",
        request_dict={"story_id": story.id},
        db_session=db_session,
    )

    db_session.refresh(task)
    params = json.loads(task.parameters)
    agent_run = params["agent_run"]
    assert agent_run["outline"]["prompt"] == "outline prompt"
    assert agent_run["outline"]["provider_used"] == "deepseek"
    assert agent_run["outline"]["raw_content"] == "outline raw"
    assert agent_run["outline"]["normalized"]

    episodes = agent_run["episodes"]
    assert len(episodes) == 2
    assert {ep["episode_number"] for ep in episodes} == {1, 2}
    assert episodes[0]["prompt"]
    assert episodes[0]["raw_content"] == "ep1 raw"
    assert episodes[0]["normalized"]["episode_number"] == 1


def test_persist_task_agent_run_script(db_session):
    user = _create_user(db_session)

    story = Story(
        user_id=user.id,
        title="Test Story",
        genre="Drama",
        story_format="short_drama",
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    episode = Episode(
        story_id=story.id,
        episode_number=1,
        title="Ep1",
    )
    db_session.add(episode)
    db_session.commit()
    db_session.refresh(episode)

    script = Script(
        episode_id=episode.id,
        title="Script1",
        content="content",
        scenes=[],
        dialogues=[],
        stage_directions=[],
        extra_metadata={
            "agent_run": {"provider_used": "minimax", "model_used": "abab"}
        },
        generation_prompt="script prompt",
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)

    timeline = Timeline(
        episode_id=episode.id,
        script_id=script.id,
        title="Timeline 1",
        status="ready",
        spec={"tracks": []},
        version=3,
        created_by=user.id,
    )
    db_session.add(timeline)
    db_session.commit()
    db_session.refresh(timeline)

    task = Task(
        title="生成剧本",
        task_type=TaskType.SCRIPT_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"script:{script.id}",
        parameters=json.dumps({"episode_id": episode.id}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    persist_task_agent_run(
        task_id=task.id,
        user_id=user.id,
        kind="script",
        db_session=db_session,
    )

    db_session.refresh(task)
    params = json.loads(task.parameters)
    assert params["agent_run"]["provider_used"] == "minimax"
    assert params["agent_run"]["prompt"] == "script prompt"
    assert params["agent_run"]["result_ref"]["script_id"] == script.id
    assert params["agent_run"]["result_ref"]["story_id"] == story.id
    assert params["agent_run"]["result_ref"]["timeline_id"] == timeline.id
    assert params["agent_run"]["result_ref"]["timeline_version"] == 3
