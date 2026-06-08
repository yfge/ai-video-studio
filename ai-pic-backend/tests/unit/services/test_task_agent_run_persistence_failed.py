import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services.task_agent_run import persist_task_agent_run


def _create_user(db_session) -> User:
    user = User(
        username="tester_failed",
        email="tester_failed@example.com",
        hashed_password="hashed",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_story_script(db_session, user: User) -> Script:
    story = Story(
        user_id=user.id,
        title="Test Story",
        genre="Drama",
        story_format="short_drama",
    )
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    episode = Episode(story_id=story.id, episode_number=1, title="Ep1")
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
        extra_metadata={},
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def test_persist_task_agent_run_failed_minimal_fallback(db_session):
    user = _create_user(db_session)
    task = Task(
        title="生成故事 - fail",
        task_type=TaskType.STORY_GENERATION,
        status=TaskStatus.FAILED,
        prompt="Story outline: fail",
        parameters=None,
        error_message="boom",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(
        task_id=task.id, user_id=user.id, kind="story", db_session=db_session
    )

    db_session.refresh(task)
    params = json.loads(task.parameters)
    run = params["agent_run"]
    assert run["generation_method"] == "story"
    assert run["task_status"] == "failed"
    assert run["error"]["message"] == "boom"
    assert run["prompt"] == "Story outline: fail"


def test_persist_task_agent_run_failed_enriches_builder_run(db_session):
    user = _create_user(db_session)
    script = _create_story_script(db_session, user)

    task = Task(
        title="对白音轨生成 - fail",
        task_type=TaskType.DIALOGUE_AUDIO_GENERATION,
        status=TaskStatus.FAILED,
        prompt=f"Dialogue audio generation for script {script.id}",
        parameters=json.dumps(
            {"script_id": script.id, "tts_model": "speech-2.6-hd"}, ensure_ascii=False
        ),
        error_message="tts failure",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(
        task_id=task.id, user_id=user.id, kind="dialogue_audio", db_session=db_session
    )

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "minimax"
    assert run["model_used"] == "speech-2.6-hd"
    assert run["task_status"] == "failed"
    assert run["error"]["message"] == "tts failure"
