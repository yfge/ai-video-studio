"""Unit tests for StoryReadinessChecker."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.services.readiness.story_readiness import StoryReadinessChecker


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def checker(mock_db):
    """Create a StoryReadinessChecker instance."""
    return StoryReadinessChecker(mock_db)


@pytest.fixture
def valid_story():
    """Create a valid story with all required fields."""
    story = MagicMock(spec=Story)
    story.id = 1
    story.title = "Test Story"
    story.genre = "Drama"
    story.story_format = "short_drama"
    story.synopsis = "A" * 60  # > 50 chars
    story.main_conflict = "Main conflict here"
    story.setting_time = "Present day"
    story.setting_location = "New York"
    story.world_building = "Modern urban setting"
    story.character_relationships = {"protagonist": {"antagonist": "enemy"}}
    story.extra_metadata = {
        "market_region": "US",
        "micro_genre": "romance",
        "hook_plan": "Cliffhanger at episode 3",
    }
    return story


class TestRequiredFieldsChecks:
    """Tests for CRITICAL required field checks."""

    def test_title_present_passes(self, checker, valid_story, mock_db):
        """Test that title check passes when title is set."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        title_check = next(c for c in result.checks if c.name == "title_present")
        assert title_check.passed is True
        assert title_check.severity == "CRITICAL"

    def test_title_missing_fails(self, checker, valid_story, mock_db):
        """Test that title check fails when title is empty."""
        valid_story.title = ""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        title_check = next(c for c in result.checks if c.name == "title_present")
        assert title_check.passed is False
        assert title_check.severity == "CRITICAL"
        assert result.can_proceed is False

    def test_genre_present_passes(self, checker, valid_story, mock_db):
        """Test that genre check passes when genre is set."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        genre_check = next(c for c in result.checks if c.name == "genre_present")
        assert genre_check.passed is True

    def test_genre_missing_fails(self, checker, valid_story, mock_db):
        """Test that genre check fails when genre is empty."""
        valid_story.genre = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        genre_check = next(c for c in result.checks if c.name == "genre_present")
        assert genre_check.passed is False
        assert result.can_proceed is False


class TestCharacterChecks:
    """Tests for character-related checks."""

    def test_has_characters_passes(self, checker, valid_story, mock_db):
        """Test that character check passes when characters exist."""
        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 10

        # Setup query chain for characters
        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        # Setup query chain for valid VIPs
        vip_query = MagicMock()
        vip_result = MagicMock()
        vip_result.id = 10
        vip_query.filter.return_value.all.return_value = [vip_result]

        # Setup query chain for images
        img_query = MagicMock()
        img_result = MagicMock()
        img_result.virtual_ip_id = 10
        img_query.filter.return_value.distinct.return_value.all.return_value = [img_result]

        # Chain all queries
        mock_db.query.side_effect = [char_query, vip_query, img_query]

        result = checker.check(valid_story)
        has_chars = next(c for c in result.checks if c.name == "has_characters")
        assert has_chars.passed is True
        assert "1 character(s)" in has_chars.message

    def test_has_characters_fails_when_empty(self, checker, valid_story, mock_db):
        """Test that character check fails when no characters."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        has_chars = next(c for c in result.checks if c.name == "has_characters")
        assert has_chars.passed is False
        assert has_chars.severity == "CRITICAL"

    def test_virtual_ip_invalid_reference(self, checker, valid_story, mock_db):
        """Test that invalid VirtualIP reference is detected."""
        mock_char = MagicMock(spec=StoryCharacter)
        mock_char.virtual_ip_id = 999  # Non-existent VIP

        char_query = MagicMock()
        char_query.filter.return_value.all.return_value = [mock_char]

        vip_query = MagicMock()
        vip_query.filter.return_value.all.return_value = []  # No valid VIPs

        mock_db.query.side_effect = [char_query, vip_query]

        result = checker.check(valid_story)
        valid_check = next(c for c in result.checks if c.name == "main_characters_valid")
        assert valid_check.passed is False
        assert valid_check.severity == "ERROR"


class TestMarketingMetaChecks:
    """Tests for marketing metadata checks (short_drama only)."""

    def test_marketing_checks_only_for_short_drama(self, checker, valid_story, mock_db):
        """Test that marketing checks are skipped for non-short_drama formats."""
        valid_story.story_format = "tv_series"
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = checker.check(valid_story)
        marketing_checks = [
            c for c in result.checks if c.name in ("market_region_set", "micro_genre_set")
        ]
        assert len(marketing_checks) == 0

    def test_market_region_passes(self, checker, valid_story, mock_db):
        """Test market_region check passes when set."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        region_check = next(c for c in result.checks if c.name == "market_region_set")
        assert region_check.passed is True

    def test_market_region_fails_when_missing(self, checker, valid_story, mock_db):
        """Test market_region check fails when not set."""
        valid_story.extra_metadata = {}
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        region_check = next(c for c in result.checks if c.name == "market_region_set")
        assert region_check.passed is False
        assert region_check.severity == "WARNING"


class TestContentQualityChecks:
    """Tests for content quality checks."""

    def test_synopsis_passes_when_long_enough(self, checker, valid_story, mock_db):
        """Test synopsis check passes when >= 50 chars."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        synopsis_check = next(c for c in result.checks if c.name == "synopsis_present")
        assert synopsis_check.passed is True

    def test_synopsis_fails_when_too_short(self, checker, valid_story, mock_db):
        """Test synopsis check fails when < 50 chars."""
        valid_story.synopsis = "Too short"
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        synopsis_check = next(c for c in result.checks if c.name == "synopsis_present")
        assert synopsis_check.passed is False
        assert synopsis_check.severity == "ERROR"

    def test_setting_passes_with_time_only(self, checker, valid_story, mock_db):
        """Test setting check passes with only time set."""
        valid_story.setting_location = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        setting_check = next(c for c in result.checks if c.name == "setting_present")
        assert setting_check.passed is True

    def test_setting_fails_when_both_missing(self, checker, valid_story, mock_db):
        """Test setting check fails when both time and location are missing."""
        valid_story.setting_time = None
        valid_story.setting_location = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        setting_check = next(c for c in result.checks if c.name == "setting_present")
        assert setting_check.passed is False


class TestReadinessResult:
    """Tests for overall readiness determination."""

    def test_ready_when_all_pass(self, checker, valid_story, mock_db):
        """Test ready=True when all checks pass."""
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

        mock_db.query.side_effect = [char_query, vip_query, img_query]

        result = checker.check(valid_story)
        assert result.ready is True
        assert result.can_proceed is True

    def test_not_ready_with_critical_failure(self, checker, valid_story, mock_db):
        """Test ready=False and can_proceed=False with CRITICAL failure."""
        valid_story.title = ""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = checker.check(valid_story)
        assert result.ready is False
        assert result.can_proceed is False

    def test_can_proceed_with_error_only(self, checker, valid_story, mock_db):
        """Test ready=False but can_proceed=True with only ERROR failures."""
        valid_story.synopsis = ""  # ERROR level

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

        mock_db.query.side_effect = [char_query, vip_query, img_query]

        result = checker.check(valid_story)
        assert result.ready is False
        assert result.can_proceed is True
