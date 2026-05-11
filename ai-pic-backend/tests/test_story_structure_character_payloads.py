from __future__ import annotations

from app.core.database import Base, get_db
from app.main import app
from app.models.script import Episode, Script, Story
from app.schemas.story_structure import SceneBeatCreate, SceneCreate
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _bootstrap_script(db: Session) -> Script:
    story = Story(title="Story", genre="g", theme="t", target_audience="all")
    episode = Episode(title="Ep1", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(script)
    return script


def test_script_structure_accepts_list_characters_involved(db_session: Session):
    Base.metadata.create_all(bind=db_session.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    script = _bootstrap_script(db_session)

    scene = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(
            script_id=script.id,
            scene_number="1",
            slug_line="INT. TEST - DAY",
        ).model_dump(),
    ).json()
    beat_payload = SceneBeatCreate(
        scene_id=scene["id"],
        order_index=1,
        beat_type="dialogue",
        beat_summary="line",
        characters_involved=["林"],
    ).model_dump()

    res = client.post(
        f"/api/v1/story-structure/scenes/{scene['id']}/beats",
        json=beat_payload,
    )
    assert res.status_code == 200
    assert res.json()["characters_involved"] == ["林"]

    structure = client.get(f"/api/v1/story-structure/scripts/{script.id}/structure")
    assert structure.status_code == 200
    assert structure.json()["scenes"][0]["beats"][0]["characters_involved"] == ["林"]
