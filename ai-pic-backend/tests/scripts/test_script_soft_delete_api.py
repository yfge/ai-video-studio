import pytest

from app.models.user import User
from tests.factories import EpisodeFactory, ScriptFactory, StoryFactory, setup_factories


@pytest.mark.unit
def test_soft_deleted_script_hidden_from_list_and_detail_via_api(client, db_session):
    setup_factories(db_session)

    admin_user = db_session.query(User).filter_by(username="test_admin").first()
    assert admin_user is not None

    story = StoryFactory(user_id=admin_user.id)
    episode = EpisodeFactory(story=story)
    script = ScriptFactory(episode=episode)
    db_session.commit()

    resp_list = client.get("/api/v1/scripts?limit=100")
    assert resp_list.status_code == 200
    assert any(item["id"] == script.id for item in resp_list.json())

    resp_delete = client.delete(f"/api/v1/scripts/{script.id}")
    assert resp_delete.status_code == 200

    resp_list_after = client.get("/api/v1/scripts?limit=100")
    assert resp_list_after.status_code == 200
    assert all(item["id"] != script.id for item in resp_list_after.json())

    resp_detail = client.get(f"/api/v1/scripts/{script.id}")
    assert resp_detail.status_code == 404
