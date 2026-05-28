from app.models.script import Script
from app.models.story_structure import Scene, Shot
from tests.factories import EpisodeFactory, setup_factories


def test_generate_script_syncs_normalized_scenes(
    client, db_session, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    episode = EpisodeFactory(
        scene_count=2,
        extra_metadata={
            "scenes": [
                {
                    "scene_number": 1,
                    "summary": "同步规范化场景测试",
                    "location": "校园",
                    "time_of_day": "白天",
                },
                {"scene_number": 2, "summary": "第二个场景"},
            ]
        },
    )

    # 强制使用本地 mock，避免真实 LLM 调用
    from app.services import ai_service as ai_module

    async def fake_generate_script(**_: object):
        return {
            "content": {
                "content": "mock script",
                "scenes": [],
                "dialogues": [],
                "stage_directions": [],
            },
            "prompt": "mock",
            "generation_method": "mock-provider:structure",
        }

    monkeypatch.setattr(ai_module.ai_service, "generate_script", fake_generate_script)
    import app.services.script.sync_generation as script_sync_generation

    async def fake_quality_gate(**kwargs):
        result = dict(kwargs["result"])
        quality_gate = {"passed": True, "source": "test"}
        result["quality_gate"] = quality_gate
        return result, kwargs["content"], quality_gate

    monkeypatch.setattr(
        script_sync_generation,
        "enforce_script_quality_gate_with_repair",
        fake_quality_gate,
    )

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

    script_obj = db_session.query(Script).filter(Script.id == script_id).first()
    assert script_obj is not None
    assert len(script_obj.scenes or []) == 2
    assert script_obj.scenes[0].get("slug_line")
    assert script_obj.scenes[0].get("summary") == "同步规范化场景测试"

    scenes = (
        db_session.query(Scene)
        .filter(Scene.script_id == script_id)
        .order_by(Scene.scene_number.asc())
        .all()
    )
    assert len(scenes) >= 1
    assert scenes[0].slug_line

    shots = (
        db_session.query(Shot).filter(Shot.scene_id.in_([s.id for s in scenes])).all()
    )
    assert len(shots) == len(scenes)
    assert all(sh.shot_number == "1" for sh in shots)

    import app.api.v1.endpoints.scripts_regeneration as scripts_regeneration

    regeneration_task: dict[str, object] = {}

    def _fake_regenerate_delay(task_id: int, request_dict: dict, user_id: int) -> None:
        regeneration_task["task_id"] = task_id
        regeneration_task["request_dict"] = request_dict
        regeneration_task["user_id"] = user_id

    monkeypatch.setattr(
        scripts_regeneration.script_regenerate_task,
        "delay",
        _fake_regenerate_delay,
    )

    # 再次生成（regenerate）不会重复创建规范化场景
    resp_regen = client.post(f"/api/v1/scripts/{script_id}/regenerate")
    assert resp_regen.status_code == 200
    assert regeneration_task["request_dict"]["script_id"] == script_id
    scenes_after = (
        db_session.query(Scene)
        .filter(Scene.script_id == script_id)
        .order_by(Scene.scene_number.asc())
        .all()
    )
    assert len(scenes_after) == len(scenes)
