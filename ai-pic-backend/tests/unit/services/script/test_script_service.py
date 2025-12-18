"""
Unit tests for Script Service.

Tests the ScriptService class business logic.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from app.services.script.script_service import ScriptService, get_script_service
from app.core.exceptions import NotFoundError


class TestScriptService:
    """Tests for ScriptService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.service = ScriptService(self.mock_session)

    def test_init(self):
        """Test service initialization."""
        assert self.service.session == self.mock_session
        assert self.service.script_repo is not None
        assert self.service.episode_repo is not None
        assert self.service.story_repo is not None

    def test_get_user_id_filter_admin(self):
        """Test admin user returns None for filter."""
        mock_user = MagicMock()
        mock_user.is_admin = True
        mock_user.is_superuser = False

        result = self.service._get_user_id_filter(mock_user)
        assert result is None

    def test_get_user_id_filter_superuser(self):
        """Test superuser returns None for filter."""
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.is_superuser = True

        result = self.service._get_user_id_filter(mock_user)
        assert result is None

    def test_get_user_id_filter_regular_user(self):
        """Test regular user returns their ID for filter."""
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.is_superuser = False
        mock_user.id = 123

        result = self.service._get_user_id_filter(mock_user)
        assert result == 123

    def test_check_user_access_admin(self):
        """Test admin has access."""
        mock_user = MagicMock()
        mock_user.is_admin = True
        mock_user.is_superuser = False

        result = self.service._check_user_access(mock_user)
        assert result is True

    def test_check_user_access_story_owner(self):
        """Test story owner has access."""
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.is_superuser = False
        mock_user.id = 123

        mock_story = MagicMock()
        mock_story.user_id = 123

        result = self.service._check_user_access(mock_user, story=mock_story)
        assert result is True

    def test_check_user_access_denied(self):
        """Test access denied for non-owner."""
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.is_superuser = False
        mock_user.id = 123

        mock_story = MagicMock()
        mock_story.user_id = 456

        result = self.service._check_user_access(mock_user, story=mock_story)
        assert result is False

    @patch.object(ScriptService, '_get_user_id_filter')
    def test_get_script_found(self, mock_filter):
        """Test getting script that exists."""
        mock_filter.return_value = None
        mock_script = MagicMock()
        self.service.script_repo.get_with_relations = MagicMock(return_value=mock_script)

        result = self.service.get_script(script_id=1)

        assert result == mock_script
        self.service.script_repo.get_with_relations.assert_called_once()

    @patch.object(ScriptService, '_get_user_id_filter')
    def test_get_script_not_found(self, mock_filter):
        """Test getting script that doesn't exist."""
        mock_filter.return_value = None
        self.service.script_repo.get_with_relations = MagicMock(return_value=None)

        with pytest.raises(NotFoundError):
            self.service.get_script(script_id=999)

    @patch.object(ScriptService, '_get_user_id_filter')
    def test_list_scripts(self, mock_filter):
        """Test listing scripts."""
        mock_filter.return_value = 123
        mock_user = MagicMock()
        mock_scripts = [MagicMock(), MagicMock()]
        self.service.script_repo.list_by_episode = MagicMock(return_value=mock_scripts)

        result = self.service.list_scripts(user=mock_user, episode_id=1)

        assert len(result) == 2
        self.service.script_repo.list_by_episode.assert_called_once()

    @patch.object(ScriptService, '_get_user_id_filter')
    @patch.object(ScriptService, '_sync_scenes_safe')
    def test_create_script(self, mock_sync, mock_filter):
        """Test creating a script."""
        mock_filter.return_value = None
        mock_user = MagicMock()
        mock_episode = MagicMock()
        mock_script = MagicMock()

        self.service.episode_repo.get_with_story = MagicMock(return_value=mock_episode)
        self.service.script_repo.create = MagicMock(return_value=mock_script)

        mock_data = MagicMock()
        mock_data.episode_id = 1
        mock_data.content = "Test content here"
        mock_data.dict.return_value = {"episode_id": 1, "content": "Test content here"}

        result = self.service.create_script(script_data=mock_data, user=mock_user)

        assert result == mock_script
        self.service.script_repo.create.assert_called_once()
        self.mock_session.commit.assert_called_once()

    @patch.object(ScriptService, '_get_user_id_filter')
    def test_create_script_episode_not_found(self, mock_filter):
        """Test creating script with non-existent episode."""
        mock_filter.return_value = None
        mock_user = MagicMock()

        self.service.episode_repo.get_with_story = MagicMock(return_value=None)

        mock_data = MagicMock()
        mock_data.episode_id = 999

        with pytest.raises(NotFoundError):
            self.service.create_script(script_data=mock_data, user=mock_user)

    @patch.object(ScriptService, 'get_script')
    @patch.object(ScriptService, '_sync_scenes_safe')
    def test_update_script(self, mock_sync, mock_get):
        """Test updating a script."""
        mock_script = MagicMock()
        mock_get.return_value = mock_script
        mock_user = MagicMock()

        mock_update = MagicMock()
        mock_update.content = "Updated content"
        mock_update.dict.return_value = {"content": "Updated content"}

        result = self.service.update_script(
            script_id=1,
            update_data=mock_update,
            user=mock_user
        )

        assert result == mock_script
        self.mock_session.commit.assert_called_once()

    @patch.object(ScriptService, 'get_script')
    def test_delete_script(self, mock_get):
        """Test deleting a script."""
        mock_script = MagicMock()
        mock_get.return_value = mock_script
        mock_user = MagicMock()
        mock_user.id = 123

        self.service.delete_script(script_id=1, user=mock_user)

        mock_script.soft_delete.assert_called_once_with(user_id=123, reason="user delete")
        self.mock_session.commit.assert_called_once()


class TestGetScriptService:
    """Tests for get_script_service factory function."""

    def test_creates_service(self):
        """Test factory creates service instance."""
        mock_session = MagicMock()
        service = get_script_service(mock_session)
        assert isinstance(service, ScriptService)
        assert service.session == mock_session
