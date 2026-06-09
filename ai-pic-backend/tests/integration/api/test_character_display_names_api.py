from app.models.episode_character import EpisodeCharacter
from app.models.script import Episode, Story
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.factories import (
    StoryCharacterFactory,
    StoryFactory,
    VirtualIPFactory,
    setup_factories,
)


def test_story_character_response_includes_virtual_ip_display_name(
    client: TestClient, db_session: Session
):
    setup_factories(db_session)

    story = StoryFactory()
    virtual_ip = VirtualIPFactory(name="林晚模板")
    StoryCharacterFactory(
        story=story,
        virtual_ip=virtual_ip,
        character_name=None,
    )

    response = client.get(f"/api/v1/stories/{story.id}")

    assert response.status_code == 200
    character = response.json()["story_characters"][0]
    assert character["virtual_ip_id"] == virtual_ip.id
    assert character["virtual_ip_name"] == "林晚模板"
    assert character["name"] == "林晚模板"
    assert character["display_name"] == "林晚模板"


def test_episode_character_list_includes_virtual_ip_display_name(
    client: TestClient, db: Session, auth_headers: dict
):
    user = User(
        username="display_name_user",
        email="display_name_user@example.com",
        hashed_password="test_hash",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    story = Story(
        user_id=user.id,
        title="Display Name Story",
        genre="drama",
        story_format="short_video",
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    episode = Episode(story_id=story.id, episode_number=1, title="第一集")
    virtual_ip = VirtualIP(user_id=user.id, name="快递员模板")
    db.add_all([episode, virtual_ip])
    db.commit()
    db.refresh(episode)
    db.refresh(virtual_ip)

    db.add(
        EpisodeCharacter(
            episode_id=episode.id,
            virtual_ip_id=virtual_ip.id,
            character_name=None,
            importance=3,
        )
    )
    db.commit()

    response = client.get(
        f"/api/v1/episodes/{episode.id}/characters?page=1&page_size=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["virtual_ip_id"] == virtual_ip.id
    assert item["virtual_ip_name"] == "快递员模板"
    assert item["name"] == "快递员模板"
    assert item["display_name"] == "快递员模板"
