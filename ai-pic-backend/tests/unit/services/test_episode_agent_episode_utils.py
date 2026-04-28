import pytest
from app.services.episode_agent_episode_utils import (
    MAX_FALLBACK_SCENES,
    stub_episode_from_outline,
    validate_episode_payload,
)


@pytest.mark.unit
def test_stub_episode_from_outline_builds_scenes_and_plot_points_from_beats():
    outline = {
        "episode_number": 2,
        "title": "Test Ep",
        "logline": "A logline.",
        "beats": [
            {
                "act_label": "ACT1",
                "beat_title": "开场",
                "beat_summary": "主角出场",
                "location_hint": "cafe",
            },
            {
                "act_label": "ACT2",
                "beat_title": "冲突",
                "description": "发生冲突",
            },
        ],
    }

    result = stub_episode_from_outline(outline)

    assert result["fallback_from_outline"] is True
    assert result["scene_count"] == 2
    assert isinstance(result.get("scenes"), list)
    assert len(result["scenes"]) == 2
    assert result["scenes"][0]["location"] == "cafe"
    assert result["scenes"][1]["location"] == "unspecified"

    assert isinstance(result.get("plot_points"), list)
    assert len(result["plot_points"]) == 2
    assert result["plot_points"][0]["description"] == "主角出场"
    assert result["plot_points"][0]["timing"] == "ACT1 - 开场"


@pytest.mark.unit
def test_stub_episode_from_outline_caps_fallback_scenes():
    outline = {
        "beats": [
            {"beat_summary": f"beat-{idx}"} for idx in range(MAX_FALLBACK_SCENES + 3)
        ]
    }

    result = stub_episode_from_outline(outline)

    assert isinstance(result.get("scenes"), list)
    assert len(result["scenes"]) == MAX_FALLBACK_SCENES
    assert result["scene_count"] == MAX_FALLBACK_SCENES
    assert len(result["plot_points"]) == MAX_FALLBACK_SCENES
    assert result["scenes"][0]["scene_number"] == 1
    assert result["scenes"][-1]["scene_number"] == MAX_FALLBACK_SCENES


@pytest.mark.unit
def test_stub_episode_from_outline_without_beats_builds_multi_scene_fallback():
    result = stub_episode_from_outline(
        {"episode_number": 1, "title": "Test", "logline": "主角发现关键证据。"}
    )

    assert result["scene_count"] == 4
    assert len(result["scenes"]) == 4
    assert len(result["plot_points"]) == 4
    assert [scene["scene_number"] for scene in result["scenes"]] == [1, 2, 3, 4]


@pytest.mark.unit
def test_validate_episode_payload_rejects_single_scene_payload():
    valid, reason = validate_episode_payload(
        {
            "summary": "S",
            "conflicts": [{"description": "C"}],
            "scene_count": 1,
            "scenes": [{"scene_number": 1, "summary": "only"}],
        }
    )

    assert valid is False
    assert reason == "too_few_scenes"
