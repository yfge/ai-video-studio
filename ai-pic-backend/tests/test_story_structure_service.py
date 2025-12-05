from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.script import Story, Episode, Script
from app.schemas.story_structure import SceneCreate, SceneBeatCreate, ShotCreate
from app.services import story_structure_service as svc


def _create_script(db: Session) -> Script:
    story = Story(title="Story", genre="test", theme="t", target_audience="all")
    episode = Episode(title="Ep1", story=story, episode_number=1)
    script = Script(title="Script1", episode=episode, content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(script)
    return script


def test_create_scene_with_children_and_fetch(db_session: Session):
    script = _create_script(db_session)

    scene_data = SceneCreate(
        script_id=script.id,
        scene_number="1",
        slug_line="EXT. TEST - DAY",
        status="draft",
    )
    beats = [
        SceneBeatCreate(scene_id=script.id, order_index=1, beat_type="action", beat_summary="do stuff"),
        SceneBeatCreate(scene_id=script.id, order_index=2, beat_type="dialogue", beat_summary="talk stuff"),
    ]
    shots = [
        {"shot_number": "1A", "scene_beat_order_index": 1, "shot_type": "WS"},
        {"shot_number": "1B", "scene_beat_order_index": 2, "shot_type": "CU"},
    ]

    created = svc.create_scene_with_children(db_session, scene_data, beats, shots)

    assert created["scene"].id
    assert len(created["beats"]) == 2
    assert len(created["shots"]) == 2
    assert created["shots"][0].scene_beat_id == created["beats"][0].id
    assert created["shots"][1].scene_beat_id == created["beats"][1].id

    aggregated = svc.get_script_structure(db_session, script.id)
    assert aggregated is not None
    assert len(aggregated) == 1
    assert len(aggregated[0]["beats"]) == 2
    assert len(aggregated[0]["shots"]) == 2
