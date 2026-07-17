from app.models.script import Episode, Story, StoryCharacter
from app.models.story_structure import Environment
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


def test_canvas_plan_links_answered_environment_when_story_resolves_ip(db_session):
    user = User(
        username="canvas_context_auto_environment_owner",
        email="canvas_context_auto_environment_owner@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    virtual_ip = VirtualIP(user_id=user.id, name="女主角", is_active=True)
    environment = Environment(
        user_id=user.id,
        name="办公室",
        category="indoor",
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()
    story = Story(user_id=user.id, title="办公室逆袭", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(
        story_id=story.id,
        episode_number=1,
        title="办公室逆袭第1集",
    )
    db_session.add_all(
        [
            StoryCharacter(
                story_id=story.id,
                virtual_ip_id=virtual_ip.id,
                character_name=virtual_ip.name,
            ),
            episode,
        ]
    )
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="制作办公室逆袭第1集",
            clarification_answers={"assets.environment_names": "办公室"},
        ),
    )

    assert plan.resolved_context.virtual_ip_id == virtual_ip.id
    assert plan.resolved_context.environment_id == environment.id
    assert plan.resolved_context.story_id == story.id
    assert plan.resolved_context.episode_id == episode.id
