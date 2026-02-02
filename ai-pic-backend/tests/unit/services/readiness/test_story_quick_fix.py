"""Unit tests for StoryQuickFixService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.script import Story
from app.schemas.readiness import FixApplied, QuickFixResponse
from app.services.readiness.story_quick_fix import (
    AUTO_FIXABLE_CHECKS,
    StoryQuickFixService,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Create a StoryQuickFixService instance."""
    return StoryQuickFixService(mock_db)


@pytest.fixture
def story_with_missing_fields():
    """Create a story with missing fields that can be auto-fixed."""
    story = MagicMock(spec=Story)
    story.id = 1
    story.title = "Test Story"
    story.genre = "Drama"
    story.story_format = "tv_series"
    story.synopsis = None  # Missing
    story.main_conflict = None  # Missing
    story.setting_time = None  # Missing
    story.setting_location = None
    story.world_building = None  # Missing
    story.premise = "A story about a hero"
    story.theme = "Adventure"
    story.character_relationships = None
    story.extra_metadata = {}
    return story


@pytest.fixture
def complete_story():
    """Create a complete story with all fields."""
    story = MagicMock(spec=Story)
    story.id = 2
    story.title = "Complete Story"
    story.genre = "Comedy"
    story.story_format = "tv_series"
    story.synopsis = "A" * 60  # Long enough
    story.main_conflict = "Hero vs villain"
    story.setting_time = "Present day"
    story.setting_location = "New York"
    story.world_building = "Modern urban setting"
    story.premise = None
    story.theme = None
    story.character_relationships = None
    story.extra_metadata = {}
    return story


class TestAutoFixableChecks:
    """Tests for identifying fixable checks."""

    def test_auto_fixable_checks_defined(self):
        """Test that AUTO_FIXABLE_CHECKS contains expected checks."""
        assert "synopsis_present" in AUTO_FIXABLE_CHECKS
        assert "main_conflict_present" in AUTO_FIXABLE_CHECKS
        assert "setting_present" in AUTO_FIXABLE_CHECKS
        assert "world_building_present" in AUTO_FIXABLE_CHECKS

    def test_critical_checks_not_fixable(self):
        """Test that CRITICAL checks are not in AUTO_FIXABLE_CHECKS."""
        assert "title_present" not in AUTO_FIXABLE_CHECKS
        assert "genre_present" not in AUTO_FIXABLE_CHECKS
        assert "has_characters" not in AUTO_FIXABLE_CHECKS


class TestQuickFixService:
    """Tests for StoryQuickFixService."""

    @pytest.mark.asyncio
    async def test_no_fixes_needed(self, service, complete_story, mock_db):
        """Test that complete story needs no fixes."""
        # Mock character query to return a character
        mock_char = MagicMock()
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

        result = await service.fix_story(complete_story)

        assert isinstance(result, QuickFixResponse)
        assert len(result.fixes_applied) == 0
        assert result.improvement.fixed_count == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_apply_fixes(self, service, story_with_missing_fields, mock_db):
        """Test that dry_run=True doesn't apply fixes."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "Generated synopsis that is long enough for validation"

            result = await service.fix_story(story_with_missing_fields, dry_run=True)

            assert result.dry_run is True
            # Fixes should be reported but not applied
            assert len(result.fixes_applied) > 0
            # DB commit should not be called
            mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_applies_fixes_when_not_dry_run(
        self, service, story_with_missing_fields, mock_db
    ):
        """Test that fixes are applied when dry_run=False."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "Generated synopsis that is long enough for validation test"

            result = await service.fix_story(story_with_missing_fields, dry_run=False)

            assert result.dry_run is False
            assert len(result.fixes_applied) > 0
            # DB should be committed
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_fix_synopsis(self, service, story_with_missing_fields, mock_db):
        """Test fixing missing synopsis."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        generated_synopsis = "A" * 60  # Long enough to pass validation

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = generated_synopsis

            fix = await service._fix_synopsis(story_with_missing_fields)

            assert fix is not None
            assert fix.check_name == "synopsis_present"
            assert fix.field == "synopsis"
            assert fix.new_value == generated_synopsis

    @pytest.mark.asyncio
    async def test_fix_synopsis_too_short(self, service, story_with_missing_fields, mock_db):
        """Test that short synopsis is rejected."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "Too short"

            fix = await service._fix_synopsis(story_with_missing_fields)

            assert fix is None

    @pytest.mark.asyncio
    async def test_fix_main_conflict(self, service, story_with_missing_fields, mock_db):
        """Test fixing missing main_conflict."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "Hero must defeat the villain"

            fix = await service._fix_main_conflict(story_with_missing_fields)

            assert fix is not None
            assert fix.check_name == "main_conflict_present"
            assert fix.field == "main_conflict"

    @pytest.mark.asyncio
    async def test_fix_setting_with_context(self, service, story_with_missing_fields, mock_db):
        """Test fixing setting_time with context."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "2024年"

            fix = await service._fix_setting(story_with_missing_fields)

            assert fix is not None
            assert fix.check_name == "setting_present"
            assert fix.field == "setting_time"
            assert fix.new_value == "2024年"

    @pytest.mark.asyncio
    async def test_fix_setting_default_fallback(self, service, mock_db):
        """Test fixing setting with default value when no context."""
        story = MagicMock(spec=Story)
        story.id = 1
        story.genre = None
        story.synopsis = None
        story.premise = None

        mock_db.query.return_value.filter.return_value.all.return_value = []

        fix = await service._fix_setting(story)

        assert fix is not None
        assert fix.new_value == "当代"

    @pytest.mark.asyncio
    async def test_fix_world_building(self, service, story_with_missing_fields, mock_db):
        """Test fixing world_building."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        story_with_missing_fields.setting_time = "Present day"

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "A world where magic exists alongside technology"

            fix = await service._fix_world_building(story_with_missing_fields)

            assert fix is not None
            assert fix.check_name == "world_building_present"
            assert fix.field == "world_building"

    @pytest.mark.asyncio
    async def test_ai_generation_failure_handled(
        self, service, story_with_missing_fields, mock_db
    ):
        """Test that AI generation failures are handled gracefully."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = None  # AI failed

            result = await service.fix_story(story_with_missing_fields)

            # Should have skipped fixes
            assert len(result.fixes_skipped) > 0


class TestQuickFixResponse:
    """Tests for QuickFixResponse structure."""

    @pytest.mark.asyncio
    async def test_response_structure(self, service, story_with_missing_fields, mock_db):
        """Test that response has correct structure."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "Generated content that is long enough to pass validation"

            result = await service.fix_story(story_with_missing_fields)

            assert hasattr(result, "story_id")
            assert hasattr(result, "dry_run")
            assert hasattr(result, "fixes_applied")
            assert hasattr(result, "fixes_skipped")
            assert hasattr(result, "initial_readiness")
            assert hasattr(result, "final_readiness")
            assert hasattr(result, "improvement")

    @pytest.mark.asyncio
    async def test_improvement_stats(self, service, story_with_missing_fields, mock_db):
        """Test improvement stats are calculated correctly."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(
            service, "_generate_text", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = "Generated content that is long enough to pass all checks"

            result = await service.fix_story(story_with_missing_fields, dry_run=True)

            assert result.improvement.fixed_count == len(result.fixes_applied)
            assert result.improvement.initial_failed >= result.improvement.final_failed
