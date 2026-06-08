import json

from app.models.script import Episode, Script, Story
from app.models.story_novel_export import StoryNovelExport
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services.task_agent_run import persist_task_agent_run


def _create_user(db_session) -> User:
    user = User(
        username="tester2",
        email="tester2@example.com",
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


def test_persist_task_agent_run_dialogue_audio(db_session):
    user = _create_user(db_session)
    script = _create_story_script(db_session, user)

    task = Task(
        title="对白音轨生成",
        task_type=TaskType.DIALOGUE_AUDIO_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"script:{script.id}:dialogue_audio",
        parameters=json.dumps(
            {"script_id": script.id, "tts_model": "speech-2.6-hd"}, ensure_ascii=False
        ),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(
        task_id=task.id, user_id=user.id, kind="dialogue_audio", db_session=db_session
    )

    db_session.refresh(task)
    params = json.loads(task.parameters)
    run = params["agent_run"]
    assert run["provider_used"] == "minimax"
    assert run["model_used"] == "speech-2.6-hd"
    assert run["result_ref"]["script_id"] == script.id


def test_persist_task_agent_run_storyboard_generation(db_session):
    user = _create_user(db_session)
    script = _create_story_script(db_session, user)
    script.extra_metadata = {
        "storyboard": {
            "frames": [],
            "meta": {
                "generation_method": "direct",
                "generation_model": "deepseek-chat",
                "provider": "deepseek",
            },
        }
    }
    db_session.commit()

    task = Task(
        title="分镜生成",
        task_type=TaskType.STORYBOARD_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"script:{script.id}:storyboard",
        parameters=json.dumps({"script_id": script.id}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(
        task_id=task.id,
        user_id=user.id,
        kind="storyboard_generation",
        db_session=db_session,
    )

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "deepseek"
    assert run["model_used"] == "deepseek-chat"


def test_persist_task_agent_run_story_novel_export(db_session):
    user = _create_user(db_session)
    story = Story(user_id=user.id, title="S", genre="Drama", story_format="short_drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    task = Task(
        title="导出知乎体小说",
        task_type=TaskType.TEXT_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path="exports:novels/x.txt",
        parameters=json.dumps(
            {"model": "deepseek:deepseek-chat", "target_words": 1200},
            ensure_ascii=False,
        ),
        user_id=user.id,
        target_business_id=story.business_id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    export_row = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=task.id,
        user_id=user.id,
        target_words=1200,
        content_text="hello",
        model="deepseek:deepseek-chat",
        temperature=0.7,
        file_relative_path="exports/novels/x.txt",
    )
    db_session.add(export_row)
    db_session.commit()

    persist_task_agent_run(
        task_id=task.id, user_id=user.id, kind="text_generation", db_session=db_session
    )

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "deepseek"
    assert run["model_used"] == "deepseek-chat"
    assert run["result_ref"]["export_id"] == export_row.id
