from pathlib import Path

from app.services.video import video_trim


def test_trim_reencodes_to_last_full_timeline_frame(monkeypatch) -> None:
    captured = {}

    def fake_run_ffmpeg(args: list[str]) -> None:
        captured["args"] = args
        Path(args[-1]).write_bytes(b"frame-aligned-video")

    monkeypatch.setattr(video_trim, "_run_ffmpeg", fake_run_ffmpeg)

    result = video_trim.trim_video_bytes(
        video_bytes=b"provider-video",
        target_seconds=6.26,
        target_fps=24,
    )

    args = captured["args"]
    assert result == b"frame-aligned-video"
    assert args[args.index("-t") + 1] == "6.250000"
    assert args[args.index("-frames:v") + 1] == "150"
    assert args[args.index("-c:v") + 1] == "libx264"
    assert "copy" not in args


def test_extracts_the_final_trimmed_frame_by_index(monkeypatch) -> None:
    captured = {}

    def fake_run_ffmpeg(args: list[str]) -> None:
        captured["args"] = args
        Path(args[-1]).write_bytes(b"last-frame")

    monkeypatch.setattr(video_trim, "_run_ffmpeg", fake_run_ffmpeg)

    result = video_trim.extract_video_frame_bytes(
        video_bytes=b"trimmed-video",
        frame_index=149,
    )

    args = captured["args"]
    assert result == b"last-frame"
    assert args[args.index("-vf") + 1] == "select=eq(n\\,149)"


def test_detects_provider_overshoot_beyond_one_frame() -> None:
    assert video_trim.video_exceeds_target_by_more_than_one_frame(15.093, 15.0, 24)
    assert not video_trim.video_exceeds_target_by_more_than_one_frame(
        15.040,
        15.0,
        24,
    )
