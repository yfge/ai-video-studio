import pytest

from app.models.script import Episode, Script, Story


@pytest.mark.unit
def test_scripts_list_returns_lite_items(client, db_session):
    story = Story(title="Story", genre="drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    episode = Episode(story_id=story.id, episode_number=1, title="Ep1")
    db_session.add(episode)
    db_session.commit()
    db_session.refresh(episode)

    script = Script(
        episode_id=episode.id,
        title="Script 1",
        content="X" * 10000,
        format_type="screenplay",
        language="zh-CN",
        status="draft",
        version="1.0",
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)

    resp = client.get(f"/api/v1/scripts?episode_id={episode.id}&limit=5")
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) == 1

    item = items[0]
    assert item["id"] == script.id
    assert item["title"] == "Script 1"
    assert item["version"] == "1.0"
    assert "created_at" in item
    assert "content" not in item

