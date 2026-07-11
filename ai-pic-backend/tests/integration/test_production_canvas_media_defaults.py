import json

from app.models.script import Episode, Script, Story
from app.models.task import Task
from app.models.user import User


def test_production_canvas_image_skill_defaults_to_one_frame(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    story = Story(user_id=user.id, title="Canvas media defaults", genre="comedy")
    db_session.add(story)
    db_session.flush()
    episode = Episode(story_id=story.id, episode_number=1, title="Episode 1")
    db_session.add(episode)
    db_session.flush()
    script = Script(
        episode_id=episode.id,
        title="Script 1",
        content="Canvas media defaults",
        extra_metadata={
            "storyboard": {"frames": [{"scene_number": 1, "description": "Frame 1"}]}
        },
    )
    db_session.add(script)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda *_args, **_kwargs: None,
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "生成一个图片候选",
            "skill": "image.candidates",
            "script_id": script.id,
            "require_reference_images": False,
        },
    )

    assert response.status_code == 200
    task = db_session.get(Task, response.json()["data"]["task_id"])
    assert json.loads(task.parameters)["frame_indexes"] == [0]
