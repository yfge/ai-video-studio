from app.models.episode_character import EpisodeCharacter
from app.models.script import Episode, Story
from app.models.user import User
from app.models.virtual_ip import VirtualIP


def test_episode_characters_normalize_legacy_scene_appearances(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    story = Story(title="Episode Character Story", genre="short_drama", user_id=user.id)
    episode = Episode(story=story, episode_number=1, title="Pilot")
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="角色模板",
        description="Character reference",
    )
    db_session.add_all([story, episode, virtual_ip])
    db_session.commit()
    db_session.refresh(episode)
    db_session.refresh(virtual_ip)

    character = EpisodeCharacter(
        episode_id=episode.id,
        episode_business_id=episode.business_id,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        character_name="老拐",
        scene_appearances=[4],
    )
    db_session.add(character)
    db_session.commit()

    numeric_response = client.get(
        f"/api/v1/episodes/{episode.id}/characters?page_size=50",
    )
    business_response = client.get(
        f"/api/v1/episodes/{episode.business_id}/characters?page_size=50",
    )

    assert numeric_response.status_code == 200, numeric_response.text
    assert business_response.status_code == 200, business_response.text
    for response in (numeric_response, business_response):
        payload = response.json()
        assert payload["total"] == 1
        assert payload["items"][0]["scene_appearances"] == [{"scene_number": 4}]
