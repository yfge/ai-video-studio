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


def test_ensure_scenes_expands_underreported_scene_count_from_plot_points():
    ep_data = {
        "summary": "S",
        "plot_points": [
            {"description": "hook", "timing": "开场"},
            {"description": "escalate", "timing": "中段"},
            {"description": "payoff", "timing": "后段"},
            {"description": "cliffhanger", "timing": "结尾"},
        ],
        "scene_count": 1,
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "INT. room - day",
                "summary": "hook",
            }
        ],
    }

    scenes, scene_count = ensure_scenes(ep_data)

    assert scene_count == 4
    assert len(scenes) == 4
    assert [scene["scene_number"] for scene in scenes] == [1, 2, 3, 4]
    assert scenes[-1]["summary"] == "cliffhanger"


def test_ensure_scenes_renumbers_duplicate_scene_numbers():
    ep_data = {
        "summary": "S",
        "scene_count": 3,
        "scenes": [
            {"scene_number": 1, "summary": "a"},
            {"scene_number": 1, "summary": "b"},
            {"scene_number": 1, "summary": "c"},
        ],
    }

    scenes, scene_count = ensure_scenes(ep_data)

    assert scene_count == 3
    assert [scene["scene_number"] for scene in scenes] == [1, 2, 3]
