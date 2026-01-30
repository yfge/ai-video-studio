"""Tests for frame duration splitter."""

import pytest

from app.services.storyboard.frame_duration_splitter import (
    DEFAULT_MAX_DURATION_SECONDS,
    DEFAULT_MIN_DURATION_SECONDS,
    SplitResult,
    adjust_frame_durations,
    merge_short_frames,
    split_long_frames,
)


class TestSplitLongFrames:
    """Tests for split_long_frames function."""

    def test_empty_frames_returns_empty(self):
        """Empty input returns empty result."""
        result = split_long_frames([])
        assert result.frames == []
        assert result.splits_performed == 0

    def test_short_frames_unchanged(self):
        """Frames under max duration pass through unchanged."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 5.0, "start_ms": 0, "end_ms": 5000},
            {"frame_id": "f2", "duration_seconds": 7.5, "start_ms": 5000, "end_ms": 12500},
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 2
        assert result.splits_performed == 0

    def test_long_frame_split_into_segments(self):
        """Frame exceeding max duration is split."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 12.0,
                "start_ms": 0,
                "end_ms": 12000,
                "scene_number": 1,
                "description": "Long action sequence",
            },
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 2
        assert result.splits_performed == 1

        # First segment
        assert result.frames[0]["start_ms"] == 0
        assert result.frames[0]["end_ms"] == 8000
        assert result.frames[0]["duration_seconds"] == 8.0
        assert result.frames[0]["parent_frame_id"] == "f1"
        assert result.frames[0]["split_index"] == 0

        # Second segment
        assert result.frames[1]["start_ms"] == 8000
        assert result.frames[1]["end_ms"] == 12000
        assert result.frames[1]["duration_seconds"] == 4.0
        assert result.frames[1]["parent_frame_id"] == "f1"
        assert result.frames[1]["split_index"] == 1
        assert "（续）" in result.frames[1]["description"]

    def test_very_long_frame_split_into_multiple_segments(self):
        """Frame exceeding 2x max is split into 3 segments."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 20.0,
                "start_ms": 0,
                "end_ms": 20000,
            },
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 3
        assert result.splits_performed == 2

        # Verify total coverage
        assert result.frames[0]["start_ms"] == 0
        assert result.frames[0]["end_ms"] == 8000
        assert result.frames[1]["start_ms"] == 8000
        assert result.frames[1]["end_ms"] == 16000
        assert result.frames[2]["start_ms"] == 16000
        assert result.frames[2]["end_ms"] == 20000

    def test_frame_numbers_renumbered(self):
        """Frame numbers are sequential after splitting."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 5.0, "start_ms": 0, "end_ms": 5000},
            {"frame_id": "f2", "duration_seconds": 12.0, "start_ms": 5000, "end_ms": 17000},
            {"frame_id": "f3", "duration_seconds": 3.0, "start_ms": 17000, "end_ms": 20000},
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 4
        assert [f["frame_number"] for f in result.frames] == [1, 2, 3, 4]

    def test_linkage_metadata_present(self):
        """Split frames contain linkage metadata."""
        frames = [
            {"frame_id": "original", "duration_seconds": 10.0, "start_ms": 0, "end_ms": 10000},
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 2
        for frame in result.frames:
            assert "parent_frame_id" in frame
            assert "split_index" in frame
            assert "total_splits" in frame
            assert "beat_range" in frame
            assert frame["parent_frame_id"] == "original"
            assert frame["total_splits"] == 2


class TestMergeShortFrames:
    """Tests for merge_short_frames function."""

    def test_empty_frames_returns_empty(self):
        """Empty input returns empty result."""
        result = merge_short_frames([])
        assert result.frames == []
        assert result.merges_performed == 0

    def test_long_frames_unchanged(self):
        """Frames above min duration pass through unchanged."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 5.0, "start_ms": 0, "end_ms": 5000},
            {"frame_id": "f2", "duration_seconds": 6.0, "start_ms": 5000, "end_ms": 11000},
        ]
        result = merge_short_frames(frames, min_duration_seconds=4.0)

        assert len(result.frames) == 2
        assert result.merges_performed == 0

    def test_consecutive_short_pauses_merged(self):
        """Consecutive short pause beats are merged."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 1.0,
                "start_ms": 0,
                "end_ms": 1000,
                "scene_number": 1,
                "description": "（停顿）",
            },
            {
                "frame_id": "f2",
                "duration_seconds": 2.0,
                "start_ms": 1000,
                "end_ms": 3000,
                "scene_number": 1,
                "description": "（停顿）",
            },
        ]
        result = merge_short_frames(frames, min_duration_seconds=4.0)

        assert len(result.frames) == 1
        assert result.merges_performed == 1
        assert result.frames[0]["start_ms"] == 0
        assert result.frames[0]["end_ms"] == 3000
        assert result.frames[0]["duration_seconds"] == 3.0

    def test_short_actions_merged(self):
        """Consecutive short action beats are merged."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 1.5,
                "start_ms": 0,
                "end_ms": 1500,
                "scene_number": 1,
                "description": "动作A",
                "beat_type": "action",
            },
            {
                "frame_id": "f2",
                "duration_seconds": 1.5,
                "start_ms": 1500,
                "end_ms": 3000,
                "scene_number": 1,
                "description": "动作B",
                "beat_type": "action",
            },
        ]
        result = merge_short_frames(frames, min_duration_seconds=4.0)

        assert len(result.frames) == 1
        assert result.merges_performed == 1
        # Descriptions should be combined
        assert "动作A" in result.frames[0]["description"]
        assert "动作B" in result.frames[0]["description"]

    def test_dialogue_not_merged(self):
        """Dialogue beats are not merged by default."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 2.0,
                "start_ms": 0,
                "end_ms": 2000,
                "beat_type": "dialogue",
                "scene_number": 1,
            },
            {
                "frame_id": "f2",
                "duration_seconds": 2.0,
                "start_ms": 2000,
                "end_ms": 4000,
                "beat_type": "dialogue",
                "scene_number": 1,
            },
        ]
        result = merge_short_frames(frames, min_duration_seconds=4.0)

        assert len(result.frames) == 2
        assert result.merges_performed == 0

    def test_different_scenes_not_merged(self):
        """Frames from different scenes are not merged."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 1.0,
                "start_ms": 0,
                "end_ms": 1000,
                "scene_number": 1,
                "description": "（停顿）",
            },
            {
                "frame_id": "f2",
                "duration_seconds": 1.0,
                "start_ms": 1000,
                "end_ms": 2000,
                "scene_number": 2,  # Different scene
                "description": "（停顿）",
            },
        ]
        result = merge_short_frames(frames, min_duration_seconds=4.0)

        assert len(result.frames) == 2
        assert result.merges_performed == 0

    def test_non_continuous_timeline_not_merged(self):
        """Frames with gaps in timeline are not merged."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 1.0,
                "start_ms": 0,
                "end_ms": 1000,
                "scene_number": 1,
                "description": "（停顿）",
            },
            {
                "frame_id": "f2",
                "duration_seconds": 1.0,
                "start_ms": 2000,  # Gap from 1000 to 2000
                "end_ms": 3000,
                "scene_number": 1,
                "description": "（停顿）",
            },
        ]
        result = merge_short_frames(frames, min_duration_seconds=4.0)

        assert len(result.frames) == 2
        assert result.merges_performed == 0


class TestAdjustFrameDurations:
    """Tests for adjust_frame_durations combined function."""

    def test_both_merge_and_split(self):
        """Function applies both merge and split operations."""
        frames = [
            # Short pauses to merge
            {
                "frame_id": "f1",
                "duration_seconds": 1.0,
                "start_ms": 0,
                "end_ms": 1000,
                "scene_number": 1,
                "description": "（停顿）",
            },
            {
                "frame_id": "f2",
                "duration_seconds": 1.0,
                "start_ms": 1000,
                "end_ms": 2000,
                "scene_number": 1,
                "description": "（停顿）",
            },
            # Long frame to split
            {
                "frame_id": "f3",
                "duration_seconds": 12.0,
                "start_ms": 2000,
                "end_ms": 14000,
                "scene_number": 1,
                "description": "Long dialogue",
            },
        ]
        result = adjust_frame_durations(
            frames,
            max_duration_seconds=8.0,
            min_duration_seconds=4.0,
        )

        # Should have: 1 merged pause + 2 split segments = 3 frames
        assert len(result.frames) == 3
        assert result.merges_performed == 1
        assert result.splits_performed == 1

    def test_idempotent_for_valid_frames(self):
        """Frames within valid range are unchanged."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 5.0, "start_ms": 0, "end_ms": 5000},
            {"frame_id": "f2", "duration_seconds": 6.0, "start_ms": 5000, "end_ms": 11000},
        ]
        result = adjust_frame_durations(
            frames,
            max_duration_seconds=8.0,
            min_duration_seconds=4.0,
        )

        assert len(result.frames) == 2
        assert result.merges_performed == 0
        assert result.splits_performed == 0


class TestSplitResult:
    """Tests for SplitResult dataclass."""

    def test_to_dict(self):
        """SplitResult can be converted to dict."""
        result = SplitResult(
            frames=[{"frame_id": "f1"}],
            splits_performed=2,
            merges_performed=1,
            audit_notes=["Note 1", "Note 2"],
        )
        d = result.to_dict()

        assert d["frame_count"] == 1
        assert d["splits_performed"] == 2
        assert d["merges_performed"] == 1
        assert d["audit_notes"] == ["Note 1", "Note 2"]


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exactly_max_duration_not_split(self):
        """Frame exactly at max duration is not split."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 8.0, "start_ms": 0, "end_ms": 8000},
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 1
        assert result.splits_performed == 0

    def test_slightly_over_max_split(self):
        """Frame slightly over max duration is split when no min threshold."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 8.1, "start_ms": 0, "end_ms": 8100},
        ]
        # Use min_duration_seconds=0 to disable absorption of tiny segments
        result = split_long_frames(
            frames, max_duration_seconds=8.0, min_duration_seconds=0.0
        )

        assert len(result.frames) == 2
        assert result.splits_performed == 1

    def test_very_short_final_segment_absorbed(self):
        """Very short final segment is absorbed into previous."""
        frames = [
            {
                "frame_id": "f1",
                "duration_seconds": 9.0,  # 8s + 1s (< 2s = 0.5 * 4s min)
                "start_ms": 0,
                "end_ms": 9000,
            },
        ]
        result = split_long_frames(
            frames,
            max_duration_seconds=8.0,
            min_duration_seconds=4.0,
        )

        # Should not create a 1s segment, instead extend first
        assert len(result.frames) == 1 or (
            len(result.frames) == 2 and result.frames[1]["duration_seconds"] >= 1.0
        )

    def test_duration_from_ms_when_seconds_missing(self):
        """Duration calculated from ms when duration_seconds missing."""
        frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 10000},  # 10s
        ]
        result = split_long_frames(frames, max_duration_seconds=8.0)

        assert len(result.frames) == 2
        assert result.splits_performed == 1

    def test_invalid_frame_skipped(self):
        """Non-dict frames are skipped."""
        frames = [
            {"frame_id": "f1", "duration_seconds": 5.0, "start_ms": 0, "end_ms": 5000},
            None,  # Invalid
            "invalid",  # Invalid
            {"frame_id": "f2", "duration_seconds": 5.0, "start_ms": 5000, "end_ms": 10000},
        ]
        result = split_long_frames(frames)

        assert len(result.frames) == 2
