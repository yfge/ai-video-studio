import pytest

from app.services.ai_service import _build_storyboard_context


def test_build_storyboard_context_includes_scene_details():
    script_payload = {
        "story": {
            "title": "城市奇遇记",
            "genre": "都市",
            "theme": "人与人的信任",
            "world_building": "现代城市，夜幕霓虹",
        },
        "episode": {
            "episode_number": 1,
            "title": "初遇",
            "summary": "主角在夜市偶遇神秘女子，卷入误会",
            "duration_minutes": 15,
            "scene_count": 3,
        },
        "scenes": [
            {
                "description": "小李在夜市摊位挑选饰品，灯光昏黄，人声鼎沸。",
                "location": "夜市主街",
                "time": "夜",
                "characters": ["小李", "摊主阿姨"],
            },
            {
                "description": "神秘女子在小巷回头，雨后的路面倒映霓虹。",
                "location": "夜市后巷",
                "time": "雨后夜晚",
                "characters": ["神秘女子"],
                "notes": "需要表达紧张氛围",
            },
        ],
        "scene_indices": [1, 2],
        "dialogues": [
            {"scene_number": 1, "content": "小李：这只手链多少钱？"},
            {"scene_number": 2, "content": "神秘女子：别跟着我。"},
        ],
        "stage_directions": [
            {"scene_number": 1, "content": "镜头跟随手部动作，浅景深"},
            {"scene_number": 2, "content": "背光剪影，慢推"},
        ],
        "content": "小李穿梭在夜市的人群中，四处张望……",
    }

    context = _build_storyboard_context(script_payload)

    assert "故事背景" in context
    assert "剧集信息" in context
    assert "场景 1" in context
    assert "地点:夜市主街" in context
    assert "对白:小李：这只手链多少钱？" in context
    assert "舞台:镜头跟随手部动作" in context
    assert "剧本文本片段" in context
    assert "场景 2" in context
    assert "备注:需要表达紧张氛围" in context
    assert "角色:神秘女子" in context

