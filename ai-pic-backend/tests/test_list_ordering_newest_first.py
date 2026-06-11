"""Story and VirtualIP lists must return newest-first so fresh creations
are visible on the first page instead of being truncated by limit."""

from app.models.script import Story
from app.models.virtual_ip import VirtualIP
from tests.test_timeline_clip_video_grid_rework_api import _bootstrap_episode


def test_story_list_returns_newest_first(client, db_session):
    user, _, _ = _bootstrap_episode(db_session)
    older = Story(title="旧故事", genre="drama", user_id=user.id)
    newer = Story(title="新故事", genre="drama", user_id=user.id)
    db_session.add(older)
    db_session.commit()
    db_session.add(newer)
    db_session.commit()

    response = client.get("/api/v1/stories?limit=2")

    assert response.status_code == 200, response.text
    ids = [story["id"] for story in response.json()]
    assert ids[0] == newer.id
    assert ids.index(newer.id) < ids.index(older.id)


def test_virtual_ip_list_returns_newest_first(client, db_session):
    user, _, _ = _bootstrap_episode(db_session)
    older = VirtualIP(name="旧IP-排序", user_id=user.id)
    newer = VirtualIP(name="新IP-排序", user_id=user.id)
    db_session.add(older)
    db_session.commit()
    db_session.add(newer)
    db_session.commit()

    response = client.get("/api/v1/virtual-ips/?limit=50")

    assert response.status_code == 200, response.text
    ids = [ip["id"] for ip in response.json()["data"]]
    assert ids[0] == newer.id
    assert ids.index(newer.id) < ids.index(older.id)
