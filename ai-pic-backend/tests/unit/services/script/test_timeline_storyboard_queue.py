import json
from uuid import uuid4

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskType
from app.models.timeline import Timeline
from app.models.user import User
from app.services.script.timeline_storyboard_queue import (
    generate_storyboard_placeholders_and_queue_images,
)
from app.services.storyboard.storyboard_image_autogen import (
    STORYBOARD_IMAGE_METADATA_KEY,
)


def test_storyboard_queue_reuses_existing_assets_without_overwrite(
    db_session,
    monkeypatch,
):
    def fail_generate_storyboard(*_args, **_kwargs):
        raise AssertionError("existing storyboard assets should be reused")

    monkeypatch.setattr(
        "app.services.script.timeline_storyboard_queue."
        "generate_storyboard_support_from_timeline_spec",
        fail_generate_storyboard,
    )
    user = User(
        username=f"storyboard_reuse_{uuid4().hex[:8]}",
        email=f"storyboard-reuse-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    story = Story(title="Story", genre="short_drama", user_id=user.id)
    episode = Episode(
        story=story,
        episode_number=1,
        title="Episode",
        duration_minutes=1,
    )
    script = Script(
        episode=episode,
        title="Script",
        content="A: hello",
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "frame_id": "legacy-frame",
                        "video_url": "https://example.com/legacy.mp4",
                    }
                ]
            }
        },
    )
    timeline = Timeline(
        episode=episode,
        script=script,
        title="Timeline",
        status="draft",
        spec={"spec_version": "timeline.v1", "tracks": []},
        version=1,
        created_by=user.id,
        updated_by=user.id,
    )
    task = Task(
        title="Timeline pipeline",
        task_type=TaskType.TIMELINE_PIPELINE,
        parameters=json.dumps({"script_id": 1}),
        user_id=user.id,
    )
    db_session.add_all([story, episode, script, timeline, task])
    db_session.commit()

    result = generate_storyboard_placeholders_and_queue_images(
        db_session,
        parent_task=task,
        script=script,
        episode=episode,
        timeline=timeline,
        user_id=user.id,
        overwrite_storyboard=False,
        min_pause_ms=1500,
    )

    assert result.status == "skipped"
    assert result.reason == "existing_storyboard_assets"
    assert result.skipped_frame_indexes == [0]
    db_session.refresh(task)
    metadata = json.loads(task.parameters)[STORYBOARD_IMAGE_METADATA_KEY]
    assert metadata["status"] == "skipped"
    assert metadata["reason"] == "existing_storyboard_assets"
