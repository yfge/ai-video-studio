from app.api.v1.endpoints.episodes import ensure_scenes


def test_ensure_scenes_filters_empty_scene_objects():
    ep_data = {
        "summary": "S",
        "plot_points": [
            {"description": "d1", "timing": "开场"},
            {"description": "d2", "timing": "中段"},
            {"description": "d3", "timing": "结尾"},
        ],
        "scene_count": 6,
        "scenes": [{}, {}, {}, {}, {}, {}],
    }

    scenes, scene_count = ensure_scenes(ep_data)

    assert scene_count == 6
    assert len(scenes) == 6
    assert scenes[0]["slug_line"]
    assert scenes[0]["summary"]
    assert scenes[0]["location"]
    assert scenes[0]["time_of_day"]
