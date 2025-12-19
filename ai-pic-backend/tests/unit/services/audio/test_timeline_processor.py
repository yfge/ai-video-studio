"""Unit tests for timeline processing utilities."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.audio.timeline_processor import (
    utc_now_iso,
    build_episode_timeline_beats,
    build_storyboard_frames_from_audio_timeline,
    _create_frame,
    generate_storyboard_from_episode_audio_timeline,
)


class TestUtcNowIso:
    """Tests for utc_now_iso function."""

    def test_returns_iso_format(self):
        """Test that function returns ISO formatted string."""
        result = utc_now_iso()
        assert isinstance(result, str)
        assert result.endswith("Z")
        # Should be parseable as datetime
        datetime.fromisoformat(result.rstrip("Z"))

    def test_is_utc(self):
        """Test that the timestamp is in UTC."""
        result = utc_now_iso()
        # ISO format should be like 2025-01-01T12:00:00.123456Z
        assert "T" in result


class TestBuildEpisodeTimelineBeats:
    """Tests for build_episode_timeline_beats function."""

    def test_basic_timeline(self):
        """Test building timeline from scenes and beats."""
        scene1 = MagicMock()
        scene1.id = 1
        scene1.scene_number = "1"

        beat1 = MagicMock()
        beat1.id = 10
        beat1.beat_type = "dialogue"
        beat1.dialogue_excerpt = "Hello"
        beat1.beat_summary = "Summary"
        beat1.duration_seconds = 2.0
        beat1.extra_metadata = {"speaker_name": "John"}

        beats_by_scene = {1: [beat1]}

        merged, total_ms = build_episode_timeline_beats(
            scenes=[scene1],
            beats_by_scene_id=beats_by_scene,
        )

        assert len(merged) == 1
        assert merged[0]["scene_id"] == 1
        assert merged[0]["beat_id"] == 10
        assert merged[0]["text"] == "Hello"  # dialogue uses dialogue_excerpt
        assert merged[0]["speaker_name"] == "John"
        assert total_ms == 2000

    def test_action_beat_uses_summary(self):
        """Test that action beats use beat_summary."""
        scene = MagicMock()
        scene.id = 1
        scene.scene_number = 1

        beat = MagicMock()
        beat.id = 10
        beat.beat_type = "action"
        beat.dialogue_excerpt = "Dialogue"
        beat.beat_summary = "Action summary"
        beat.duration_seconds = 1.0
        beat.extra_metadata = {}

        merged, _ = build_episode_timeline_beats(
            scenes=[scene],
            beats_by_scene_id={1: [beat]},
        )

        assert merged[0]["text"] == "Action summary"

    def test_timing_from_metadata(self):
        """Test using start_ms and end_ms from metadata."""
        scene = MagicMock()
        scene.id = 1
        scene.scene_number = 1

        beat = MagicMock()
        beat.id = 10
        beat.beat_type = "dialogue"
        beat.dialogue_excerpt = "Hello"
        beat.beat_summary = ""
        beat.duration_seconds = 0
        beat.extra_metadata = {
            "start_ms": 500,
            "end_ms": 1500,
        }

        merged, total_ms = build_episode_timeline_beats(
            scenes=[scene],
            beats_by_scene_id={1: [beat]},
        )

        assert merged[0]["start_ms"] == 500
        assert merged[0]["end_ms"] == 1500
        assert total_ms == 1500

    def test_multiple_scenes_offset(self):
        """Test that multiple scenes have proper time offset."""
        scene1 = MagicMock()
        scene1.id = 1
        scene1.scene_number = 1

        scene2 = MagicMock()
        scene2.id = 2
        scene2.scene_number = 2

        beat1 = MagicMock()
        beat1.id = 10
        beat1.beat_type = "dialogue"
        beat1.dialogue_excerpt = "Hello"
        beat1.beat_summary = ""
        beat1.duration_seconds = 2.0
        beat1.extra_metadata = {}

        beat2 = MagicMock()
        beat2.id = 20
        beat2.beat_type = "dialogue"
        beat2.dialogue_excerpt = "World"
        beat2.beat_summary = ""
        beat2.duration_seconds = 1.0
        beat2.extra_metadata = {}

        merged, total_ms = build_episode_timeline_beats(
            scenes=[scene1, scene2],
            beats_by_scene_id={1: [beat1], 2: [beat2]},
        )

        assert len(merged) == 2
        # Scene 2 beat should be offset by scene 1 duration
        assert merged[1]["start_ms"] == 2000
        assert merged[1]["end_ms"] == 3000
        assert total_ms == 3000

    def test_empty_scenes(self):
        """Test with empty scenes list."""
        merged, total_ms = build_episode_timeline_beats(
            scenes=[],
            beats_by_scene_id={},
        )
        assert merged == []
        assert total_ms == 0

    def test_invalid_scene_number(self):
        """Test handling invalid scene number."""
        scene = MagicMock()
        scene.id = 1
        scene.scene_number = "invalid"

        merged, _ = build_episode_timeline_beats(
            scenes=[scene],
            beats_by_scene_id={1: []},
        )

        # Should handle gracefully


class TestBuildStoryboardFramesFromAudioTimeline:
    """Tests for build_storyboard_frames_from_audio_timeline function."""

    def test_basic_storyboard(self):
        """Test basic storyboard frame generation."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 2000,
                    "scene_id": 1,
                    "scene_number": 1,
                    "speaker_name": "John",
                    "text": "Hello world",
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        assert len(frames) == 1
        assert frames[0]["frame_number"] == 1
        assert frames[0]["scene_number"] == 1
        assert frames[0]["start_ms"] == 0
        assert frames[0]["end_ms"] == 2000
        assert frames[0]["duration_seconds"] == 2.0
        assert "John" in frames[0]["description"]

    def test_action_beat_frame(self):
        """Test action beat creates frame."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "action",
                    "start_ms": 0,
                    "end_ms": 1000,
                    "scene_id": 1,
                    "text": "Walking away",
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        assert len(frames) == 1
        assert frames[0]["description"] == "Walking away"

    def test_short_pause_merged(self):
        """Test short pauses are merged into previous frame."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 2000,
                    "scene_id": 1,
                    "scene_number": 1,
                    "text": "Hello",
                },
                {
                    "beat_type": "pause",
                    "start_ms": 2000,
                    "end_ms": 2500,  # 500ms pause - less than 1500ms threshold
                    "scene_id": 1,
                    "scene_number": 1,
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        # Short pause should be merged into dialogue frame
        assert len(frames) == 1
        assert frames[0]["end_ms"] == 2500
        assert frames[0]["duration_seconds"] == 2.5

    def test_long_pause_creates_frame(self):
        """Test long pauses create separate frame."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 2000,
                    "scene_id": 1,
                    "text": "Hello",
                },
                {
                    "beat_type": "pause",
                    "start_ms": 2000,
                    "end_ms": 4000,  # 2000ms pause - more than 1500ms threshold
                    "scene_id": 1,
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        # Long pause should create separate frame
        assert len(frames) == 2
        assert frames[1]["description"] == "（停顿）"

    def test_custom_min_pause_duration(self):
        """Test custom minimum pause duration threshold."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 2000,
                    "scene_id": 1,
                    "text": "Hello",
                },
                {
                    "beat_type": "pause",
                    "start_ms": 2000,
                    "end_ms": 3000,  # 1000ms pause
                    "scene_id": 1,
                },
            ]
        }

        # With low threshold, pause becomes separate frame
        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline,
            min_pause_duration_ms=500,
        )

        assert len(frames) == 2

    def test_missing_beats_key(self):
        """Test missing beats key raises error."""
        with pytest.raises(RuntimeError, match="audio_timeline_missing_beats"):
            build_storyboard_frames_from_audio_timeline(audio_timeline={})

    def test_invalid_beat_type_skipped(self):
        """Test invalid beat types are skipped."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "unknown",
                    "start_ms": 0,
                    "end_ms": 1000,
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        assert len(frames) == 0

    def test_scene_index_mapping(self):
        """Test scene index is assigned correctly."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 1000,
                    "scene_id": 5,
                    "text": "First",
                },
                {
                    "beat_type": "dialogue",
                    "start_ms": 1000,
                    "end_ms": 2000,
                    "scene_id": 10,
                    "text": "Second",
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        # Scene indices should be assigned in order of appearance
        assert frames[0]["scene_index"] == 1
        assert frames[1]["scene_index"] == 2

    def test_default_speaker_name(self):
        """Test default speaker name for dialogue without speaker."""
        audio_timeline = {
            "beats": [
                {
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 1000,
                    "scene_id": 1,
                    "text": "Hello",
                    # No speaker_name
                },
            ]
        }

        frames = build_storyboard_frames_from_audio_timeline(
            audio_timeline=audio_timeline
        )

        assert "旁白" in frames[0]["description"]


class TestCreateFrame:
    """Tests for _create_frame helper function."""

    def test_basic_frame(self):
        """Test creating basic frame."""
        frame = _create_frame(
            scene_number_int=1,
            scene_id_int=100,
            scene_index_map={100: 1},
            description="Test frame",
            duration_ms=2000,
            start_ms_int=0,
            end_ms_int=2000,
            frame_number=1,
        )

        assert frame["frame_number"] == 1
        assert frame["scene_number"] == 1
        assert frame["scene_index"] == 1
        assert frame["description"] == "Test frame"
        assert frame["duration_seconds"] == 2.0
        assert frame["start_ms"] == 0
        assert frame["end_ms"] == 2000
        assert frame["status"] == "draft"
        assert frame["generation_source"] == "audio_timeline"
        assert "frame_id" in frame

    def test_frame_with_none_scene(self):
        """Test creating frame with None scene values."""
        frame = _create_frame(
            scene_number_int=None,
            scene_id_int=None,
            scene_index_map={},
            description="Test",
            duration_ms=1000,
            start_ms_int=0,
            end_ms_int=1000,
            frame_number=1,
        )

        assert frame["scene_number"] is None
        assert frame["scene_index"] is None


class TestGenerateStoryboardFromEpisodeAudioTimeline:
    """Tests for generate_storyboard_from_episode_audio_timeline function."""

    def test_basic_generation(self):
        """Test basic storyboard generation."""
        db = MagicMock()
        script = MagicMock()
        script.id = 1
        script.extra_metadata = {}
        script.storyboard_version = 0

        episode = MagicMock()
        episode.id = 10
        episode.extra_metadata = {
            "audio_timeline": {
                "script_id": 1,
                "beats": [
                    {
                        "beat_type": "dialogue",
                        "start_ms": 0,
                        "end_ms": 1000,
                        "scene_id": 1,
                        "text": "Hello",
                    }
                ],
            }
        }

        result = generate_storyboard_from_episode_audio_timeline(
            db, script=script, episode=episode
        )

        assert "frames" in result
        assert "meta" in result
        assert len(result["frames"]) == 1
        db.commit.assert_called_once()

    def test_missing_audio_timeline(self):
        """Test error when audio timeline is missing."""
        db = MagicMock()
        script = MagicMock()
        script.id = 1

        episode = MagicMock()
        episode.extra_metadata = {}

        with pytest.raises(RuntimeError, match="episode_audio_timeline_not_found"):
            generate_storyboard_from_episode_audio_timeline(
                db, script=script, episode=episode
            )

    def test_script_mismatch(self):
        """Test error when script ID doesn't match."""
        db = MagicMock()
        script = MagicMock()
        script.id = 1

        episode = MagicMock()
        episode.extra_metadata = {
            "audio_timeline": {
                "script_id": 999,  # Different script ID
                "beats": [],
            }
        }

        with pytest.raises(RuntimeError, match="audio_timeline_script_mismatch"):
            generate_storyboard_from_episode_audio_timeline(
                db, script=script, episode=episode
            )

    def test_no_frames_generated(self):
        """Test error when no frames are generated."""
        db = MagicMock()
        script = MagicMock()
        script.id = 1

        episode = MagicMock()
        episode.extra_metadata = {
            "audio_timeline": {
                "script_id": 1,
                "beats": [],  # Empty beats
            }
        }

        with pytest.raises(RuntimeError, match="no_frames_generated"):
            generate_storyboard_from_episode_audio_timeline(
                db, script=script, episode=episode
            )

    def test_refuse_overwrite_with_assets(self):
        """Test refusing to overwrite storyboard with existing assets."""
        db = MagicMock()
        script = MagicMock()
        script.id = 1
        script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {"image_url": "http://example.com/image.jpg"}
                ]
            }
        }

        episode = MagicMock()
        episode.extra_metadata = {
            "audio_timeline": {
                "script_id": 1,
                "beats": [
                    {
                        "beat_type": "dialogue",
                        "start_ms": 0,
                        "end_ms": 1000,
                        "text": "Hello",
                    }
                ],
            }
        }

        with pytest.raises(RuntimeError, match="storyboard_has_assets"):
            generate_storyboard_from_episode_audio_timeline(
                db, script=script, episode=episode, overwrite_existing=False
            )

    def test_overwrite_with_flag(self):
        """Test overwriting storyboard when flag is set."""
        db = MagicMock()
        script = MagicMock()
        script.id = 1
        script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {"image_url": "http://example.com/image.jpg"}
                ]
            }
        }
        script.storyboard_version = 1

        episode = MagicMock()
        episode.id = 10
        episode.extra_metadata = {
            "audio_timeline": {
                "script_id": 1,
                "beats": [
                    {
                        "beat_type": "dialogue",
                        "start_ms": 0,
                        "end_ms": 1000,
                        "scene_id": 1,
                        "text": "Hello",
                    }
                ],
            }
        }

        # Should not raise
        result = generate_storyboard_from_episode_audio_timeline(
            db, script=script, episode=episode, overwrite_existing=True
        )

        assert len(result["frames"]) == 1
