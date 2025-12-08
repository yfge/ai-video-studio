from app.models.story_structure import Scene
from tests.factories import EpisodeFactory, setup_factories


def test_generate_script_dialogue_fallback(client, db_session, monkeypatch):
    setup_factories(db_session)
    episode = EpisodeFactory()

    # 让 generate_script 仅返回场景，触发对白/舞台指示占位生成
    from app.services import ai_service as ai_module

    async def fake_generate_script(**_: object):
        return {
            "content": {
                "scenes": [{"scene_number": 1, "summary": "测试场景对白缺失"}],
                "dialogues": [],
                "stage_directions": [],
            },
            "prompt": "mock",
            "generation_method": "mock-provider:fallback",
        }

    monkeypatch.setattr(ai_module.ai_service, "generate_script", fake_generate_script)

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
    data = resp.json()

    assert data["dialogues"], "对白应自动补齐"
    assert data["dialogues"][0]["scene_number"] == 1
    assert data["stage_directions"], "舞台指示应自动补齐"

    # 确保规范化场景仍同步
    scenes = (
        db_session.query(Scene)
        .filter(Scene.script_id == data["id"])
        .order_by(Scene.scene_number.asc())
        .all()
    )
    assert len(scenes) == 1
