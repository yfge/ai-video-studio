import json

from app.models.script import Episode, Script, Story
from app.models.story_novel_export import StoryNovelExport
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.video_generation_task import VideoGenerationTask, VideoGenerationTaskStatus
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.models.story_structure import Environment
from app.services.task_agent_run_persistence import persist_task_agent_run


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
        parameters=json.dumps({"script_id": script.id, "tts_model": "speech-2.6-hd"}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(task_id=task.id, user_id=user.id, kind="dialogue_audio", db_session=db_session)

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

    persist_task_agent_run(task_id=task.id, user_id=user.id, kind="storyboard_generation", db_session=db_session)

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "deepseek"
    assert run["model_used"] == "deepseek-chat"


def test_persist_task_agent_run_environment_images(db_session):
    user = _create_user(db_session)
    env = Environment(user_id=user.id, name="Env", category="indoor", tags=[], description="x", reference_images=[])
    db_session.add(env)
    db_session.commit()
    db_session.refresh(env)

    task = Task(
        title="环境文生图",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"environment_images:{env.id}:1",
        parameters=json.dumps({"env_id": env.id, "prompt": "p", "model": "google:imagen-3"}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(task_id=task.id, user_id=user.id, kind="environment_images", db_session=db_session)

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "google"
    assert run["model_used"] == "imagen-3"
    assert run["generation_method"] == "text_to_image"


def test_persist_task_agent_run_virtual_ip_image(db_session):
    user = _create_user(db_session)
    vip = VirtualIP(user_id=user.id, name="VIP", description="d", is_active=True, is_public=False)
    db_session.add(vip)
    db_session.commit()
    db_session.refresh(vip)

    image = VirtualIPImage(
        virtual_ip_id=vip.id,
        virtual_ip_business_id=vip.business_id,
        filename="a.png",
        original_filename="a.png",
        file_path="/uploads/a.png",
        oss_url="http://example.com/a.png",
        file_size=1,
        mime_type="image/png",
        category="portrait",
        tags=["ai_generated"],
        prompt="final prompt",
        ai_model="dall-e-3",
        generation_params={"seed": 1},
        is_default=False,
        is_public=True,
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)

    task = Task(
        title="虚拟IP文生图",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.COMPLETED,
        result_file_path=f"virtual_ip_image:{vip.id}:{image.id}",
        parameters=json.dumps({"virtual_ip_id": vip.id, "model": "openai:dall-e-3"}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    persist_task_agent_run(task_id=task.id, user_id=user.id, kind="virtual_ip_image", db_session=db_session)

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "openai"
    assert run["model_used"] == "dall-e-3"
    assert run["prompt"] == "final prompt"
    assert run["result_ref"]["virtual_ip_image_id"] == image.id


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
        parameters=json.dumps({"model": "deepseek:deepseek-chat", "target_words": 1200}, ensure_ascii=False),
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

    persist_task_agent_run(task_id=task.id, user_id=user.id, kind="text_generation", db_session=db_session)

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "deepseek"
    assert run["model_used"] == "deepseek-chat"
    assert run["result_ref"]["export_id"] == export_row.id


def test_persist_task_agent_run_video_generation(db_session):
    user = _create_user(db_session)
    task = Task(
        title="分镜视频生成",
        task_type=TaskType.VIDEO_GENERATION,
        status=TaskStatus.COMPLETED,
        parameters=json.dumps({"script_id": 123, "model": "google:veo"}, ensure_ascii=False),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    sub = VideoGenerationTask(
        task_id=task.id,
        script_id=123,
        frame_index=0,
        user_id=user.id,
        provider="google",
        provider_task_id="t1",
        model="veo",
        model_type="image_to_video",
        prompt="p",
        parameters=json.dumps({}, ensure_ascii=False),
        status=VideoGenerationTaskStatus.SUCCEEDED,
    )
    db_session.add(sub)
    db_session.commit()

    persist_task_agent_run(task_id=task.id, user_id=user.id, kind="video_generation", db_session=db_session)

    db_session.refresh(task)
    run = json.loads(task.parameters)["agent_run"]
    assert run["provider_used"] == "google"
    assert run["model_used"] == "veo"
    assert run["result_ref"]["video_task_count"] == 1

