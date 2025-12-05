from __future__ import annotations

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db, Base
from app.models.script import Story, Episode, Script
from app.schemas.story_structure import SceneCreate, SceneBeatCreate, ShotCreate
from tests.conftest import override_get_db


def _bootstrap_script(db: Session) -> Script:
    story = Story(title="Story", genre="g", theme="t", target_audience="all")
    episode = Episode(title="Ep1", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(script)
    return script


def test_scene_crud_with_children(db_session: Session):
    # ensure tables exist for this session
    Base.metadata.create_all(bind=db_session.get_bind())

    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    script = _bootstrap_script(db_session)

    # create scene
    scene_payload = {
        "script_id": script.id,
        "scene_number": "1",
        "slug_line": "INT. TEST - DAY",
    }
    res = client.post(f"/api/v1/story-structure/scripts/{script.id}/scenes", json=scene_payload)
    assert res.status_code == 200
    scene_id = res.json()["id"]

    # update scene
    res = client.put(f"/api/v1/story-structure/scenes/{scene_id}", json={"location": "Office"})
    assert res.status_code == 200
    assert res.json()["location"] == "Office"

    # add beat
    beat_payload = {
        "scene_id": scene_id,
        "order_index": 1,
        "beat_summary": "first",
    }
    res = client.post(f"/api/v1/story-structure/scenes/{scene_id}/beats", json=beat_payload)
    assert res.status_code == 200
    beat_id = res.json()["id"]

    # update beat
    res = client.put(f"/api/v1/story-structure/scene-beats/{beat_id}", json={"beat_summary": "updated"})
    assert res.status_code == 200
    assert res.json()["beat_summary"] == "updated"

    # add shots via service helper path
    shot_payload = {
        "scene_id": scene_id,
        "shot_number": "1A",
    }
    res = client.post(f"/api/v1/story-structure/scenes/{scene_id}/shots", json=shot_payload)
    assert res.status_code == 200
    shot_id = res.json()["id"]

    # update shot
    res = client.put(f"/api/v1/story-structure/shots/{shot_id}", json={"shot_type": "WS"})
    assert res.status_code == 200
    assert res.json()["shot_type"] == "WS"

    # delete shot
    res = client.delete(f"/api/v1/story-structure/shots/{shot_id}")
    assert res.status_code == 204

    # delete scene
    res = client.delete(f"/api/v1/story-structure/scenes/{scene_id}")
    assert res.status_code == 204
