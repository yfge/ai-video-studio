from app.models.story_structure import Scene, Shot
from tests.factories import EpisodeFactory, setup_factories


def test_generate_script_syncs_normalized_scenes(client, db_session, mock_ai_service):
    setup_factories(db_session)
    episode = EpisodeFactory()

    payload = {
        "episode_id": episode.id,
        "format_type": "screenplay",
        "language": "zh-CN",
        "dialogue_style": "natural",
        "scene_detail_level": "medium",
        "temperature": 0.7,
    }

    resp = client.post("/api/v1/scripts/generate", json=payload)
    assert resp.status_code == 200
    script_id = resp.json()["id"]

    scenes = (
        db_session.query(Scene)
        .filter(Scene.script_id == script_id)
        .order_by(Scene.scene_number.asc())
        .all()
    )
    assert len(scenes) == 1
    assert scenes[0].slug_line

    shots = db_session.query(Shot).filter(Shot.scene_id == scenes[0].id).all()
    assert len(shots) == 1
    assert shots[0].shot_number == "1"

    # 再次生成（regenerate）不会重复创建规范化场景
    resp_regen = client.post(f"/api/v1/scripts/{script_id}/regenerate")
    assert resp_regen.status_code == 200
    scenes_after = (
        db_session.query(Scene)
        .filter(Scene.script_id == script_id)
        .order_by(Scene.scene_number.asc())
        .all()
    )
    assert len(scenes_after) == 1
