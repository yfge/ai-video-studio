"""Unit tests for EpisodeReadinessChecker."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.script import Episode, Script, Story, StoryCharacter
from app.services.readiness.episode_readiness import EpisodeReadinessChecker


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def checker(mock_db):
    """Create an EpisodeReadinessChecker instance."""
    return EpisodeReadinessChecker(mock_db)


@pytest.fixture
def valid_story():
    """Create a valid story with all required fields."""
    story = MagicMock(spec=Story)
    story.id = 1
    story.title = "Test Story"
    story.genre = "Drama"
    story.story_format = "tv_series"  # Not short_drama to skip marketing checks
    story.synopsis = "A" * 60
    story.main_conflict = "Main conflict"
    story.setting_time = "Present"
    story.setting_location = None
    story.world_building = None
    story.character_relationships = None
    story.extra_metadata = {}
    return story


@pytest.fixture
def valid_episode():
    """Create a valid episode."""
    episode = MagicMock(spec=Episode)
    episode.id = 10
    episode.story_id = 1
    episode.episode_number = 1
    episode.title = "Pilot"
    episode.is_deleted = False
    return episode


class TestEpisodeExistsCheck:
    """Tests for episode_exists check."""

    def test_episode_exists_passes(self, checker, valid_story, valid_episode, mock_db):
        """Test episode_exists passes for valid episode."""
        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        # For previous episodes check (none for first episode)
        prev_ep_query = MagicMock()
        prev_ep_query.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [char_query, vip_query, img_query, prev_ep_query]

        result = checker.check(valid_story, valid_episode)
        exists_check = next(c for c in result.checks if c.name == "episode_exists")
        assert exists_check.passed is True
        assert "Episode #1" in exists_check.message

    def test_episode_deleted_fails(self, checker, valid_story, valid_episode, mock_db):
        """Test episode_exists fails for deleted episode."""
        valid_episode.is_deleted = True

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = checker.check(valid_story, valid_episode)
        exists_check = next(c for c in result.checks if c.name == "episode_exists")
        assert exists_check.passed is False
        assert exists_check.severity == "CRITICAL"


class TestStoryMatchesCheck:
    """Tests for story_matches check."""

    def test_story_matches_passes(self, checker, valid_story, valid_episode, mock_db):
        """Test story_matches passes when IDs match."""
        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        prev_ep_query = MagicMock()
        prev_ep_query.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [char_query, vip_query, img_query, prev_ep_query]

        result = checker.check(valid_story, valid_episode)
        match_check = next(c for c in result.checks if c.name == "story_matches")
        assert match_check.passed is True

    def test_story_matches_fails_when_mismatch(
        self, checker, valid_story, valid_episode, mock_db
    ):
        """Test story_matches fails when IDs don't match."""
        valid_episode.story_id = 999  # Different story

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = checker.check(valid_story, valid_episode)
        match_check = next(c for c in result.checks if c.name == "story_matches")
        assert match_check.passed is False
        assert match_check.severity == "CRITICAL"


class TestPreviousEpisodesCheck:
    """Tests for previous_episodes_complete check."""

    def test_first_episode_no_check(self, checker, valid_story, valid_episode, mock_db):
        """Test no continuity check for first episode."""
        valid_episode.episode_number = 1

        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        prev_ep_query = MagicMock()
        prev_ep_query.filter.return_value.all.return_value = []  # No earlier episodes

        mock_db.query.side_effect = [char_query, vip_query, img_query, prev_ep_query]

        result = checker.check(valid_story, valid_episode)
        prev_checks = [c for c in result.checks if c.name == "previous_episodes_complete"]
        assert len(prev_checks) == 0  # Should not have this check

    def test_previous_episodes_complete_passes(
        self, checker, valid_story, valid_episode, mock_db
    ):
        """Test continuity check passes when all previous episodes have scripts."""
        valid_episode.episode_number = 3

        # Setup story checks
        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        # Previous episodes (ep 1 and 2)
        prev_ep1 = MagicMock(spec=Episode)
        prev_ep1.id = 8
        prev_ep1.episode_number = 1

        prev_ep2 = MagicMock(spec=Episode)
        prev_ep2.id = 9
        prev_ep2.episode_number = 2

        prev_ep_query = MagicMock()
        prev_ep_query.filter.return_value.all.return_value = [prev_ep1, prev_ep2]

        # Scripts for previous episodes
        script1 = MagicMock()
        script1.episode_id = 8
        script2 = MagicMock()
        script2.episode_id = 9

        script_query = MagicMock()
        script_query.filter.return_value.distinct.return_value.all.return_value = [
            script1,
            script2,
        ]

        mock_db.query.side_effect = [
            char_query,
            vip_query,
            img_query,
            prev_ep_query,
            script_query,
        ]

        result = checker.check(valid_story, valid_episode)
        prev_check = next(c for c in result.checks if c.name == "previous_episodes_complete")
        assert prev_check.passed is True
        assert "2 previous episode(s)" in prev_check.message

    def test_previous_episodes_incomplete_warns(
        self, checker, valid_story, valid_episode, mock_db
    ):
        """Test continuity check warns when previous episodes lack scripts."""
        valid_episode.episode_number = 3

        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        # Previous episodes
        prev_ep1 = MagicMock(spec=Episode)
        prev_ep1.id = 8
        prev_ep1.episode_number = 1

        prev_ep2 = MagicMock(spec=Episode)
        prev_ep2.id = 9
        prev_ep2.episode_number = 2

        prev_ep_query = MagicMock()
        prev_ep_query.filter.return_value.all.return_value = [prev_ep1, prev_ep2]

        # Only episode 1 has a script
        script1 = MagicMock()
        script1.episode_id = 8

        script_query = MagicMock()
        script_query.filter.return_value.distinct.return_value.all.return_value = [script1]

        mock_db.query.side_effect = [
            char_query,
            vip_query,
            img_query,
            prev_ep_query,
            script_query,
        ]

        result = checker.check(valid_story, valid_episode)
        prev_check = next(c for c in result.checks if c.name == "previous_episodes_complete")
        assert prev_check.passed is False
        assert prev_check.severity == "WARNING"
        assert "2" in prev_check.message  # Episode 2 missing


class TestEpisodeReadinessResult:
    """Tests for overall episode readiness determination."""

    def test_inherits_story_checks(self, checker, valid_story, valid_episode, mock_db):
        """Test that episode result includes story checks."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = checker.check(valid_story, valid_episode)

        # Should have story checks like title_present
        check_names = [c.name for c in result.checks]
        assert "title_present" in check_names
        assert "genre_present" in check_names

    def test_summary_includes_episode_number(
        self, checker, valid_story, valid_episode, mock_db
    ):
        """Test that summary mentions episode number."""
        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        prev_ep_query = MagicMock()
        prev_ep_query.filter.return_value.all.return_value = []

        mock_db.query.side_effect = [char_query, vip_query, img_query, prev_ep_query]

        result = checker.check(valid_story, valid_episode)
        assert "Episode #1" in result.summary

    def test_episode_id_in_result(self, checker, valid_story, valid_episode, mock_db):
        """Test that episode_id is set in result."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story, valid_episode)
        assert result.episode_id == valid_episode.id
        assert result.story_id == valid_story.id
