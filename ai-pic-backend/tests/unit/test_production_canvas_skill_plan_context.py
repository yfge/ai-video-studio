from __future__ import annotations

from app.models.script import Episode, Script, Story, StoryCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


def _user(db, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_canvas_skill_plan_marks_downstream_ready_with_episode_context(db_session):
    user = _user(db_session, "canvas_skill_episode_owner")
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        tags=["轻喜剧"],
        is_active=True,
    )
    story = Story(user_id=user.id, title="林妹妹故事", genre="comedy")
    db_session.add_all([virtual_ip, story])
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=4, title="办公室轻喜剧")
    db_session.add_all(
        [
            StoryCharacter(
                story_id=story.id,
                virtual_ip_id=virtual_ip.id,
                character_name="林妹妹",
            ),
            episode,
        ]
    )
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于林妹妹做第 4 集，办公室轻喜剧",
            episode_id=episode.id,
        ),
    )
    script_result = next(
        result for result in plan.skill_results if result.skill == "script.generate"
    )

    assert script_result.status == "ready"
    assert script_result.outputs["episode_id"] == episode.id
    assert "required_inputs" not in script_result.outputs


def test_canvas_skill_plan_carries_script_context_for_downstream_execution(
    db_session,
):
    user = _user(db_session, "canvas_skill_script_owner")
    story = Story(user_id=user.id, title="程序员轻喜剧", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(
        story_id=story.id,
        episode_number=4,
        title="智能生活入门",
    )
    db_session.add(episode)
    db_session.commit()
    script = Script(
        episode_id=episode.id,
        title="第 4 集剧本",
        content="办公室轻喜剧",
    )
    db_session.add(script)
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于现有剧本继续生成分镜和时间线",
            episode_id=episode.id,
            script_id=script.id,
        ),
    )
    results = {result.skill: result for result in plan.skill_results}

    assert results["storyboard.plan"].status == "ready"
    assert results["storyboard.plan"].outputs["script_id"] == script.id
    assert results["storyboard.plan"].outputs["episode_id"] == episode.id
    assert results["script.generate"].status == "review"
    assert results["timeline.assemble"].status == "review"
    assert results["timeline.assemble"].outputs["script_id"] == script.id
    assert results["image.candidates"].status == "review"
    assert results["video.candidates"].status == "blocked"
