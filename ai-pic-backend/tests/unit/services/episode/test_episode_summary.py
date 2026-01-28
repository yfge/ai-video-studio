import pytest
from app.services.episode.episode_summary import build_episode_summary


@pytest.mark.unit
def test_build_episode_summary_prefers_summary_and_compacts_whitespace():
    payload = {"summary": "  Line1\n\nLine2\tLine3  "}
    assert build_episode_summary(payload, max_chars=200) == "Line1 Line2 Line3"


@pytest.mark.unit
def test_build_episode_summary_falls_back_to_plot_points():
    payload = {"plot_points": [{"description": "A"}, {"description": "B"}]}
    assert build_episode_summary(payload, max_chars=200) == "A; B"
