"""Integration tests for IP environment readiness warnings."""

from app.models.script import Script
from app.models.story_structure import Environment, Scene
from app.models.user import User
from app.models.virtual_ip import VirtualIPEnvironment
from tests.integration.test_readiness_api import (
    _create_episode,
    _create_story,
    _create_story_character,
    _create_virtual_ip,
)


def test_story_readiness_warns_for_missing_ip_environment_pool(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    vip = _create_virtual_ip(db_session, user, has_image=True)
    story = _create_story(db_session, user)
    _create_story_character(db_session, story, vip)

    response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

    assert response.status_code == 200
    data = response.json()
    assert data["can_proceed"] is True
    env_check = next(
        item for item in data["checks"] if item["name"] == "ip_environment_pool_linked"
    )
    assert env_check["passed"] is False
    assert env_check["severity"] == "WARNING"


def test_story_readiness_warns_for_scene_environment_coverage(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    vip = _create_virtual_ip(db_session, user, has_image=True)
    story = _create_story(db_session, user)
    episode = _create_episode(db_session, story)
    _create_story_character(db_session, story, vip)

    env = Environment(user_id=user.id, name="公寓", category="indoor")
    db_session.add(env)
    db_session.commit()
    db_session.refresh(env)

    script = Script(episode_id=episode.id, title="Script")
    link = VirtualIPEnvironment(
        user_id=user.id,
        virtual_ip_id=vip.id,
        virtual_ip_business_id=vip.business_id,
        environment_id=env.id,
        environment_business_id=env.business_id,
    )
    db_session.add_all([link, script])
    db_session.commit()
    db_session.refresh(script)

    db_session.add_all(
        [
            Scene(script_id=script.id, scene_number="1", slug_line="INT."),
            Scene(
                script_id=script.id,
                scene_number="2",
                slug_line="EXT.",
                environment_id=env.id,
                environment_business_id=env.business_id,
            ),
        ]
    )
    db_session.commit()

    response = client.post(f"/api/v1/stories/{story.id}/readiness-check")

    assert response.status_code == 200
    data = response.json()
    coverage = next(
        item for item in data["checks"] if item["name"] == "scene_environment_coverage"
    )
    assert coverage["passed"] is False
    assert coverage["severity"] == "WARNING"
    assert coverage["message"] == "Scene environment coverage: 1/2"
