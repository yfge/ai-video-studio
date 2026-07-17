from __future__ import annotations

import pytest
from app.core.exceptions import ValidationError
from app.models.script import Episode, Script, Story, StoryCharacter
from app.models.story_structure import Environment
from app.models.timeline import Timeline
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
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


def _story_episode(
    db,
    user: User,
    virtual_ip: VirtualIP,
    title: str,
    *,
    episode_number: int = 4,
) -> tuple[Story, Episode]:
    story = Story(user_id=user.id, title=title, genre="comedy")
    db.add(story)
    db.commit()
    episode = Episode(
        story_id=story.id,
        episode_number=episode_number,
        title=f"{title}第{episode_number}集",
    )
    db.add_all(
        [
            StoryCharacter(
                story_id=story.id,
                virtual_ip_id=virtual_ip.id,
                character_name=virtual_ip.name,
            ),
            episode,
        ]
    )
    db.commit()
    db.refresh(episode)
    return story, episode


def test_canvas_plan_resolves_unique_story_and_numbered_episode(db_session):
    user = _user(db_session, "canvas_context_unique_owner")
    virtual_ip = VirtualIP(user_id=user.id, name="林妹妹", is_active=True)
    environment = Environment(
        user_id=user.id,
        name="共享办公区",
        category="indoor",
        tags=["办公室"],
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()
    story, episode = _story_episode(db_session, user, virtual_ip, "林妹妹办公室故事")
    db_session.add(
        VirtualIPEnvironment(
            user_id=user.id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            environment_id=environment.id,
            environment_business_id=environment.business_id,
            usage_type="main_scene",
            is_default=True,
        )
    )
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(prompt="基于林妹妹做第 4 集，办公室轻喜剧"),
    )

    assert plan.resolved_context.virtual_ip_id == virtual_ip.id
    assert plan.resolved_context.environment_id == environment.id
    assert plan.resolved_context.story_id == story.id
    assert plan.resolved_context.episode_id == episode.id
    script_result = next(
        item for item in plan.skill_results if item.skill == "script.generate"
    )
    assert script_result.status == "ready"
    assert script_result.outputs["story_id"] == story.id
    assert script_result.outputs["episode_id"] == episode.id


def test_canvas_plan_does_not_guess_between_ambiguous_stories(db_session):
    user = _user(db_session, "canvas_context_ambiguous_owner")
    virtual_ip = VirtualIP(user_id=user.id, name="林妹妹", is_active=True)
    db_session.add(virtual_ip)
    db_session.commit()
    _story_episode(db_session, user, virtual_ip, "甲线")
    _story_episode(db_session, user, virtual_ip, "乙线")

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(prompt="基于林妹妹做第 4 集"),
    )

    assert plan.resolved_context.virtual_ip_id == virtual_ip.id
    assert plan.resolved_context.story_id is None
    assert plan.resolved_context.episode_id is None
    script_result = next(
        item for item in plan.skill_results if item.skill == "script.generate"
    )
    assert script_result.status == "blocked"
    assert script_result.outputs["required_inputs"] == ["production_context"]
    questions = plan.production_context.brief.clarifications
    assert questions[0].id == "context.story_id"
    assert {option.label.split(" ")[0] for option in questions[0].options} == {
        "甲线",
        "乙线",
    }


def test_canvas_plan_resolves_and_validates_timeline_clip_context(db_session):
    user = _user(db_session, "canvas_context_timeline_owner")
    story = Story(user_id=user.id, title="时间线故事", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=4, title="第四集")
    db_session.add(episode)
    db_session.commit()
    script = Script(episode_id=episode.id, title="第四集剧本", content="内容")
    db_session.add(script)
    db_session.commit()
    timeline = Timeline(
        episode_id=episode.id,
        script_id=script.id,
        title="第四集时间线",
        status="draft",
        version=2,
        spec={
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [{"clip_id": "clip-1"}],
                }
            ]
        },
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(timeline)
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="继续第四集当前分镜",
            timeline_id=timeline.id,
            timeline_version=2,
            clip_id="clip-1",
        ),
    )

    assert plan.resolved_context.story_id == story.id
    assert plan.resolved_context.episode_id == episode.id
    assert plan.resolved_context.script_id == script.id
    assert plan.resolved_context.timeline_id == timeline.id
    assert plan.resolved_context.timeline_version == 2
    assert plan.resolved_context.clip_id == "clip-1"

    with pytest.raises(
        ValidationError,
        match="timeline_version 与上游业务上下文不一致",
    ):
        build_canvas_skill_plan(
            db_session,
            user,
            ProductionCanvasPlanRequest(
                prompt="继续旧版分镜",
                timeline_id=timeline.id,
                timeline_version=1,
            ),
        )


def test_canvas_plan_rejects_mismatched_story_lineage(db_session):
    user = _user(db_session, "canvas_context_lineage_owner")
    stories = [
        Story(user_id=user.id, title="故事一", genre="comedy"),
        Story(user_id=user.id, title="故事二", genre="comedy"),
    ]
    db_session.add_all(stories)
    db_session.commit()
    episode = Episode(story_id=stories[1].id, episode_number=1, title="第一集")
    db_session.add(episode)
    db_session.commit()

    with pytest.raises(ValidationError, match="story_id 与上游业务上下文不一致"):
        build_canvas_skill_plan(
            db_session,
            user,
            ProductionCanvasPlanRequest(
                prompt="继续第一集",
                story_id=stories[0].id,
                episode_id=episode.id,
            ),
        )


def test_canvas_plan_rejects_environment_outside_ip_pool(db_session):
    user = _user(db_session, "canvas_context_unlinked_environment_owner")
    virtual_ip = VirtualIP(user_id=user.id, name="林妹妹", is_active=True)
    environment = Environment(
        user_id=user.id,
        name="未关联办公室",
        category="indoor",
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()

    with pytest.raises(
        ValidationError,
        match="environment_id 不属于指定 virtual_ip_id 的环境资源池",
    ):
        build_canvas_skill_plan(
            db_session,
            user,
            ProductionCanvasPlanRequest(
                prompt="继续林妹妹的办公室短剧",
                virtual_ip_id=virtual_ip.id,
                environment_id=environment.id,
            ),
        )


def test_canvas_plan_rejects_explicit_environment_with_implicit_unlinked_ip(
    db_session,
):
    user = _user(db_session, "canvas_context_implicit_ip_owner")
    virtual_ip = VirtualIP(user_id=user.id, name="林妹妹", is_active=True)
    environment = Environment(
        user_id=user.id,
        name="未关联办公室",
        category="indoor",
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()

    with pytest.raises(
        ValidationError,
        match="environment_id 不属于指定 virtual_ip_id 的环境资源池",
    ):
        build_canvas_skill_plan(
            db_session,
            user,
            ProductionCanvasPlanRequest(
                prompt="基于林妹妹制作第1集",
                environment_id=environment.id,
            ),
        )
