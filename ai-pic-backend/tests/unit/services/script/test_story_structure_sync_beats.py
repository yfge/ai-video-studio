from types import SimpleNamespace

import pytest
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure,
)


@pytest.mark.unit
def test_sync_script_scenes_creates_scene_beats(monkeypatch):
    created_beat_payloads = []
    created_shots = []
    scene = SimpleNamespace(id=10, scene_number="1")

    def list_scenes_by_script(db, script_id):
        return []

    def create_scene(db, payload):
        return scene

    def create_scene_beat(db, payload):
        created_beat_payloads.append(payload)
        return SimpleNamespace(id=20, order_index=payload.order_index)

    def create_shot(db, payload):
        created_shots.append(payload)
        return SimpleNamespace(id=30)

    from app.services.script import story_structure_sync as module

    monkeypatch.setattr(
        module.story_structure_svc,
        "list_scenes_by_script",
        list_scenes_by_script,
    )
    monkeypatch.setattr(module.story_structure_svc, "create_scene", create_scene)
    monkeypatch.setattr(
        module.story_structure_svc,
        "create_scene_beat",
        create_scene_beat,
    )
    monkeypatch.setattr(module.story_structure_svc, "create_shot", create_shot)

    script = SimpleNamespace(
        id=1,
        scenes=[
            {
                "scene_number": 1,
                "slug_line": "内. 控制室 - 夜",
                "summary": "谁清空了奖金？",
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "抛出损失",
                        "visible_event": "屏幕奖金归零",
                        "dialogue_lines": [
                            {"character": "小机", "content": "奖金清零？"}
                        ],
                        "action_lines": [{"content": "红色警报亮起"}],
                        "duration_seconds": 5,
                        "hook_tag": "loss",
                    }
                ],
            }
        ],
        extra_metadata={},
    )

    result = sync_script_scenes_to_story_structure(object(), script)

    assert result["created"] == 1
    assert result["beats_created"] == 1
    assert created_beat_payloads[0].beat_type == "hook"
    assert created_beat_payloads[0].dialogue_excerpt == "小机: 奖金清零？"
    assert created_beat_payloads[0].metadata["visible_event"] == "屏幕奖金归零"
    assert len(created_shots) == 1
