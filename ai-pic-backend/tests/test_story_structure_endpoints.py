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


def test_scene_beat_order_conflict_returns_400(db_session: Session):
    Base.metadata.create_all(bind=db_session.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    script = _bootstrap_script(db_session)

    scene = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(script_id=script.id, scene_number="1", slug_line="INT").model_dump(),
    ).json()

    first = SceneBeatCreate(scene_id=scene["id"], order_index=1, beat_summary="first").model_dump()
    assert client.post(f"/api/v1/story-structure/scenes/{scene['id']}/beats", json=first).status_code == 200

    conflict = SceneBeatCreate(scene_id=scene["id"], order_index=1, beat_summary="duplicate").model_dump()
    res = client.post(f"/api/v1/story-structure/scenes/{scene['id']}/beats", json=conflict)

    assert res.status_code == 400
    assert res.json()["detail"] == "order_index already exists for scene"


def test_shot_duplicate_number_and_beat_mismatch(db_session: Session):
    Base.metadata.create_all(bind=db_session.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    script = _bootstrap_script(db_session)

    # scene A with beat
    scene_a = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(script_id=script.id, scene_number="1", slug_line="INT").model_dump(),
    ).json()
    beat = client.post(
        f"/api/v1/story-structure/scenes/{scene_a['id']}/beats",
        json=SceneBeatCreate(scene_id=scene_a["id"], order_index=1, beat_summary="first").model_dump(),
    ).json()

    # duplicate shot number in same scene
    first_shot = ShotCreate(scene_id=scene_a["id"], shot_number="1A").model_dump()
    assert client.post(f"/api/v1/story-structure/scenes/{scene_a['id']}/shots", json=first_shot).status_code == 200
    res_dup = client.post(f"/api/v1/story-structure/scenes/{scene_a['id']}/shots", json=first_shot)
    assert res_dup.status_code == 400
    assert res_dup.json()["detail"] == "shot_number already exists for scene"

    # beat/scene mismatch
    scene_b = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(script_id=script.id, scene_number="2", slug_line="EXT").model_dump(),
    ).json()
    bad_shot = ShotCreate(scene_id=scene_b["id"], shot_number="2A", scene_beat_id=beat["id"]).model_dump()
    res_mismatch = client.post(f"/api/v1/story-structure/scenes/{scene_b['id']}/shots", json=bad_shot)
    assert res_mismatch.status_code == 400
    assert res_mismatch.json()["detail"] == "beat does not belong to scene"
