"""
Unit tests for Script Repository.

Tests the ScriptRepository, EpisodeRepository, and StoryRepository classes.
"""

from unittest.mock import MagicMock

from app.repositories.script_repository import (
    EpisodeRepository,
    ScriptRepository,
    StoryRepository,
)


class TestScriptRepository:
    """Tests for ScriptRepository."""

    def test_init(self):
        """Test repository initialization."""
        mock_session = MagicMock()
        repo = ScriptRepository(mock_session)
        assert repo.session == mock_session

    def test_get_with_relations_by_id(self):
        """Test getting script with relations by ID."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(id=1)

        repo = ScriptRepository(mock_session)
        result = repo.get_with_relations(script_id=1)

        assert result is not None
        mock_query.first.assert_called_once()

    def test_get_with_relations_no_params(self):
        """Test getting script with no params returns None."""
        mock_session = MagicMock()
        repo = ScriptRepository(mock_session)
        result = repo.get_with_relations()
        assert result is None

    def test_list_by_episode(self):
        """Test listing scripts by episode."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [MagicMock(id=1), MagicMock(id=2)]

        repo = ScriptRepository(mock_session)
        results = repo.list_by_episode(episode_id=1)

        assert len(results) == 2
        mock_query.all.assert_called_once()

    def test_update_storyboard(self):
        """Test updating script storyboard."""
        mock_script = MagicMock()
        mock_script.extra_metadata = {}
        mock_script.storyboard_version = 1

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_script
        )

        repo = ScriptRepository(mock_session)
        result = repo.update_storyboard(1, {"frames": []})

        assert result is not None
        assert mock_script.extra_metadata["storyboard"] == {"frames": []}
        assert mock_script.storyboard_version == 2

    def test_update_storyboard_not_found(self):
        """Test updating storyboard for non-existent script."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        repo = ScriptRepository(mock_session)
        result = repo.update_storyboard(999, {"frames": []})

        assert result is None

    def test_update_storyboard_plan(self):
        """Test updating script storyboard plan."""
        mock_script = MagicMock()
        mock_script.storyboard_plan = None

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_script
        )

        repo = ScriptRepository(mock_session)
        result = repo.update_storyboard_plan(1, {"scenes": []})

        assert result is not None
        assert mock_script.storyboard_plan == {"scenes": []}


class TestEpisodeRepository:
    """Tests for EpisodeRepository."""

    def test_init(self):
        """Test repository initialization."""
        mock_session = MagicMock()
        repo = EpisodeRepository(mock_session)
        assert repo.session == mock_session

    def test_get_with_story_by_id(self):
        """Test getting episode with story by ID."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(id=1)

        repo = EpisodeRepository(mock_session)
        result = repo.get_with_story(episode_id=1)

        assert result is not None

    def test_get_with_story_no_params(self):
        """Test getting episode with no params returns None."""
        mock_session = MagicMock()
        repo = EpisodeRepository(mock_session)
        result = repo.get_with_story()
        assert result is None

    def test_list_by_story(self):
        """Test listing episodes by story."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [MagicMock(id=1)]

        repo = EpisodeRepository(mock_session)
        results = repo.list_by_story(story_id=1)

        assert len(results) == 1


class TestStoryRepository:
    """Tests for StoryRepository."""

    def test_init(self):
        """Test repository initialization."""
        mock_session = MagicMock()
        repo = StoryRepository(mock_session)
        assert repo.session == mock_session

    def test_list_by_user(self):
        """Test listing stories by user."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [MagicMock(id=1)]

        repo = StoryRepository(mock_session)
        results = repo.list_by_user(user_id=1)

        assert len(results) == 1

    def test_get_by_user(self):
        """Test getting story by user."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock(id=1)

        repo = StoryRepository(mock_session)
        result = repo.get_by_user(story_id=1, user_id=1)

        assert result is not None

    def test_get_by_user_not_found(self):
        """Test getting story by user when not found."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repo = StoryRepository(mock_session)
        result = repo.get_by_user(story_id=999, user_id=1)

        assert result is None
