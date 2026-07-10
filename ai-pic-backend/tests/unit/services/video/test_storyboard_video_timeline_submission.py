import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskType
from app.models.user import User
from app.models.video_generation_task import VideoGenerationTask
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_task_submission_service import VideoTaskSubmissionService


def test_storyboard_video_submission_preserves_timeline_clip_context(
    db_session, monkeypatch
):
    user = User(
        username="timeline_batch_worker",
        email="timeline_batch_worker@example.com",
        hashed_password="test",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    story = Story(user_id=user.id, title="Timeline batch", genre="short_drama")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=1, title="Pilot")
    db_session.add(episode)
    db_session.commit()
    script = Script(
        episode_id=episode.id,
        title="Pilot script",
        content="A clip",
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "description": "Lead enters the room",
                        "duration_seconds": 4,
                        "start_image_urls": ["https://example.com/start.png"],
                    }
                ]
            }
        },
    )
    task = Task(
        title="Timeline video batch",
        task_type=TaskType.VIDEO_GENERATION,
        prompt="Generate clip video",
        user_id=user.id,
    )
    db_session.add_all([script, task])
    db_session.commit()

    def fake_submit_provider_task(*_args, **kwargs):
        return AIResponse(
            success=True,
            data={"task_id": "provider-video-1", "duration": kwargs["duration"]},
            provider="minimax",
            model="MiniMax-Hailuo-2.3",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    monkeypatch.setattr(
        "app.services.video.video_task_submission_service.submit_provider_task",
        fake_submit_provider_task,
    )
    context = {
        "timeline_id": 71,
        "timeline_version": 6,
        "clip_id": "video_scene_001_beat_001_001",
        "asset_role": "generated_video",
        "auto_render": False,
    }

    VideoTaskSubmissionService(db_session, object()).submit_storyboard_video_tasks(
        task_id=task.id,
        script_id=script.id,
        frame_indexes=[0],
        selections=None,
        options={"timeline_rework_by_frame": {"0": context}},
    )

    video_task = db_session.query(VideoGenerationTask).filter_by(task_id=task.id).one()
    params = json.loads(video_task.parameters)
    assert params["timeline_rework"] == context
    assert params["image_url"] == "https://example.com/start.png"
