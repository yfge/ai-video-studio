"""Tests for EpisodeRenderService."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.render.episode_render_service import EpisodeRenderService
from app.services.render.video_concat import VideoClip


class TestGetStoryboardClips:
    """Test storyboard clip extraction."""

    def test_extract_clips(self):
        """Test extracting video clips from storyboard."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_script = MagicMock()
        mock_script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {
                        "video_url": "https://example.com/v1.mp4",
                        "duration_seconds": 3.0,
                        "frame_number": 1,
                        "description": "Frame 1",
                    },
                    {
                        "video_url": "https://example.com/v2.mp4",
                        "duration_seconds": 5.0,
                        "frame_number": 2,
                        "description": "Frame 2",
                    },
                ]
            }
        }

        clips = service.get_storyboard_clips(mock_script)

        assert len(clips) == 2
        assert clips[0].url == "https://example.com/v1.mp4"
        assert clips[0].target_duration_seconds == 3.0
        assert clips[1].target_duration_seconds == 5.0

    def test_skip_frames_without_video(self):
        """Test that frames without video_url are skipped."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_script = MagicMock()
        mock_script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {"video_url": "https://example.com/v1.mp4", "duration_seconds": 3.0},
                    {"duration_seconds": 5.0},  # No video_url
                    {"video_url": "https://example.com/v3.mp4", "duration_seconds": 4.0},
                ]
            }
        }

        clips = service.get_storyboard_clips(mock_script)

        assert len(clips) == 2
        assert clips[0].url == "https://example.com/v1.mp4"
        assert clips[1].url == "https://example.com/v3.mp4"

    def test_handle_string_duration(self):
        """Test handling duration as string."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_script = MagicMock()
        mock_script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {
                        "video_url": "https://example.com/v1.mp4",
                        "duration_seconds": "4.5",  # String instead of float
                    }
                ]
            }
        }

        clips = service.get_storyboard_clips(mock_script)

        assert len(clips) == 1
        assert clips[0].target_duration_seconds == 4.5

    def test_default_duration(self):
        """Test default duration when not specified."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_script = MagicMock()
        mock_script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {"video_url": "https://example.com/v1.mp4"}  # No duration
                ]
            }
        }

        clips = service.get_storyboard_clips(mock_script)

        assert len(clips) == 1
        assert clips[0].target_duration_seconds == 3.0  # Default

    def test_empty_storyboard(self):
        """Test handling empty storyboard."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_script = MagicMock()
        mock_script.extra_metadata = {}

        clips = service.get_storyboard_clips(mock_script)

        assert len(clips) == 0


class TestGetEpisodeAudioUrl:
    """Test episode audio URL extraction."""

    def test_get_audio_url(self):
        """Test getting dialogue audio URL."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_episode = MagicMock()
        mock_episode.extra_metadata = {
            "dialogue_audio": {
                "oss_url": "https://example.com/audio.mp3"
            }
        }

        url = service.get_episode_audio_url(mock_episode)

        assert url == "https://example.com/audio.mp3"

    def test_no_audio_metadata(self):
        """Test when no audio metadata exists."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_episode = MagicMock()
        mock_episode.extra_metadata = {}

        url = service.get_episode_audio_url(mock_episode)

        assert url is None

    def test_none_episode(self):
        """Test when episode is None."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        url = service.get_episode_audio_url(None)

        assert url is None


class TestRenderEpisode:
    """Test episode rendering."""

    @pytest.mark.asyncio
    async def test_script_not_found(self):
        """Test error when script not found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = EpisodeRenderService(mock_db)
        result = await service.render_episode(999)

        assert result["success"] is False
        assert "Script not found" in result["error"]

    @pytest.mark.asyncio
    async def test_no_episode(self):
        """Test error when script has no episode."""
        mock_db = MagicMock()
        mock_script = MagicMock()
        mock_script.episode = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_script

        service = EpisodeRenderService(mock_db)
        result = await service.render_episode(1)

        assert result["success"] is False
        assert "no episode" in result["error"]

    @pytest.mark.asyncio
    async def test_no_clips(self):
        """Test error when no video clips."""
        mock_db = MagicMock()
        mock_script = MagicMock()
        mock_script.episode = MagicMock()
        mock_script.extra_metadata = {"storyboard": {"frames": []}}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_script

        service = EpisodeRenderService(mock_db)
        result = await service.render_episode(1)

        assert result["success"] is False
        assert "No video clips" in result["error"]

    @pytest.mark.asyncio
    @patch("app.services.render.episode_render_service.concat_video_clips")
    async def test_render_success(self, mock_concat):
        """Test successful render."""
        mock_concat.return_value = {
            "success": True,
            "duration_seconds": 10.0,
            "frame_count": 2,
            "has_replaced_audio": False,
        }

        mock_db = MagicMock()
        mock_episode = MagicMock()
        mock_episode.id = 1
        mock_episode.extra_metadata = {}

        mock_script = MagicMock()
        mock_script.episode = mock_episode
        mock_script.extra_metadata = {
            "storyboard": {
                "frames": [
                    {"video_url": "https://example.com/v1.mp4", "duration_seconds": 5.0},
                    {"video_url": "https://example.com/v2.mp4", "duration_seconds": 5.0},
                ]
            }
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_script

        service = EpisodeRenderService(mock_db)

        with patch.object(service, "_render_version") as mock_render:
            mock_render.return_value = {
                "success": True,
                "url": "https://example.com/render.mp4",
                "duration_seconds": 10.0,
            }

            result = await service.render_episode(
                1, render_with_tts_audio=False, render_with_video_audio=True
            )

        assert result["success"] is True
        assert result["frame_count"] == 2


class TestSaveRenderResults:
    """Test saving render results."""

    def test_save_results(self):
        """Test saving render results to episode metadata."""
        mock_db = MagicMock()
        service = EpisodeRenderService(mock_db)

        mock_episode = MagicMock()
        mock_episode.extra_metadata = {}

        results = {
            "frame_count": 3,
            "total_duration": 15.0,
            "renders": {
                "video_audio": {
                    "success": True,
                    "url": "https://example.com/v1.mp4",
                    "duration_seconds": 15.0,
                },
                "tts_audio": {
                    "success": True,
                    "url": "https://example.com/v2.mp4",
                    "duration_seconds": 15.0,
                },
            },
        }

        service._save_render_results(mock_episode, results)

        assert "episode_renders" in mock_episode.extra_metadata
        assert "latest" in mock_episode.extra_metadata["episode_renders"]
        assert mock_episode.extra_metadata["episode_renders"]["latest"]["frame_count"] == 3
        mock_db.commit.assert_called_once()
