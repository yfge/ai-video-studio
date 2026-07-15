from __future__ import annotations

import json

from app.models.task import Task
from app.services.storyboard.storyboard_image_autogen import (
    queue_storyboard_image_generation,
)
from tests.factories import (
    EpisodeFactory,
    ScriptFactory,
    StoryFactory,
    UserFactory,
    setup_factories,
)


def test_autogen_inherits_story_aspect_ratio_when_request_omits_it(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    story = StoryFactory(default_aspect_ratio="9:16")
    episode = EpisodeFactory(story=story)
    script = ScriptFactory(
        episode=episode,
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "frame_id": "environment-only",
                        "description": "Empty room insert",
                        "characters": [],
                    }
                ]
            }
        },
    )
    db_session.commit()
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda *_args: None,
    )

    result = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        aspect_ratio=None,
    )

    task = db_session.get(Task, result.child_task_id)
    assert json.loads(task.parameters)["aspect_ratio"] == "9:16"


def test_autogen_prefers_episode_aspect_ratio_override(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    story = StoryFactory(default_aspect_ratio="9:16")
    episode = EpisodeFactory(story=story, aspect_ratio="16:9")
    script = ScriptFactory(
        episode=episode,
        extra_metadata={
            "storyboard": {"frames": [{"description": "Skyline", "characters": []}]}
        },
    )
    db_session.commit()
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda *_args: None,
    )

    result = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
    )

    task = db_session.get(Task, result.child_task_id)
    assert json.loads(task.parameters)["aspect_ratio"] == "16:9"
