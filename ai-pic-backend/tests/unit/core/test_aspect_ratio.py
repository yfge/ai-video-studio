import pytest

from app.core.aspect_ratio import DEFAULT_ASPECT_RATIO, resolve_aspect_ratio


@pytest.mark.unit
@pytest.mark.parametrize(
    ("request_value", "episode_value", "story_value", "expected"),
    [
        (None, None, None, DEFAULT_ASPECT_RATIO),
        ("16:9", None, None, "16:9"),
        (None, "16:9", None, "16:9"),
        (None, None, "16:9", "16:9"),
        # priority: request > episode > story
        ("9:16", "16:9", "16:9", "9:16"),
        (None, "9:16", "16:9", "9:16"),
        # strip + invalid values fallback
        (" 16:9 ", None, None, "16:9"),
        ("1:1", "4:3", "3:4", DEFAULT_ASPECT_RATIO),
    ],
)
def test_resolve_aspect_ratio_priority_and_fallback(
    request_value, episode_value, story_value, expected
):
    assert (
        resolve_aspect_ratio(
            request_value=request_value,
            episode_value=episode_value,
            story_value=story_value,
        )
        == expected
    )

