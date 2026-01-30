import pytest

from app.services.providers.google_provider.video_helpers import resolve_duration
from app.services.video.video_duration import resolve_duration_ceil
from app.services.video.video_task_utils import coerce_duration


@pytest.mark.unit
def test_resolve_duration_ceil_chooses_next_allowed() -> None:
    resolved = resolve_duration_ceil(target_seconds=5, allowed_durations=[4, 6, 8])
    assert resolved.provider_seconds == 6


@pytest.mark.unit
def test_resolve_duration_ceil_never_shorter_than_target() -> None:
    resolved = resolve_duration_ceil(target_seconds=4.1, allowed_durations=[4, 6, 8])
    assert resolved.provider_seconds == 6


@pytest.mark.unit
def test_resolve_duration_ceil_marks_needs_split_when_exceeds_max() -> None:
    resolved = resolve_duration_ceil(target_seconds=12, allowed_durations=[4, 6, 8])
    assert resolved.provider_seconds == 8
    assert resolved.needs_split is True


@pytest.mark.unit
def test_google_resolve_duration_uses_ceil_strategy() -> None:
    # Previously 5s would resolve to 4s due to nearest-distance tie.
    assert (
        resolve_duration("veo-3.1-generate-preview", 5, resolution="720p") == 6
    ), "should resolve up to avoid under-duration"


@pytest.mark.unit
def test_video_task_utils_coerce_duration_uses_ceil() -> None:
    assert coerce_duration(4.1) == 5

