"""Tests for the deterministic Timeline render video contract."""

from app.services.render.video_render_spec import (
    RenderVideoSpec,
    allocate_frame_counts,
    resolve_render_video_spec,
)


def test_resolve_explicit_vertical_render_contract_and_timeline_duration():
    spec = resolve_render_video_spec(
        {"resolution": "1080x1920", "fps": 24},
        {"resolution": "1080x1920", "duration_ms": 180_000},
        [60.0, 120.0],
    )

    assert spec == RenderVideoSpec(
        width=1080,
        height=1920,
        fps=24,
        total_duration_seconds=180.0,
    )
    assert spec.total_frames == 4320


def test_frame_allocation_removes_per_clip_rounding_drift():
    durations = [5.064, 12.833, 1.62, 160.483]
    spec = RenderVideoSpec(1080, 1920, 24, 180.0)

    counts = allocate_frame_counts(durations, spec)

    assert sum(counts) == 4320
    assert all(count > 0 for count in counts)


def test_p_resolution_preserves_timeline_orientation():
    portrait = resolve_render_video_spec(
        {"resolution": "720p"},
        {"resolution": "1080x1920", "duration_ms": 1000},
        [1.0],
    )
    landscape = resolve_render_video_spec(
        {"resolution": "720p"},
        {"resolution": "1920x1080", "duration_ms": 1000},
        [1.0],
    )

    assert (portrait.width, portrait.height) == (720, 1280)
    assert (landscape.width, landscape.height) == (1280, 720)
