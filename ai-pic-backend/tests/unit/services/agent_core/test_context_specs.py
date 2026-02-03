"""Tests for Concrete Context Specifications."""

import pytest

from app.services.agent_core.context_spec import FieldPriority
from app.services.agent_core.context_specs import (
    EpisodeContext,
    ScriptContext,
    StoryboardContext,
    StoryContext,
    TimelineContext,
)


class TestStoryContext:
    """Tests for StoryContext."""

    def test_required_fields(self):
        """Should require title and genre."""
        ctx = StoryContext()
        errors = ctx.validate()
        assert any("title" in e for e in errors)
        assert any("genre" in e for e in errors)

    def test_valid_context(self):
        """Should pass with all required fields."""
        ctx = StoryContext(
            title="测试故事",
            genre="悬疑",
            characters=[{"name": "主角"}],
        )
        errors = ctx.validate()
        assert errors == []

    def test_character_field_critical(self):
        """Characters field should be critical priority."""
        char_field = next(f for f in StoryContext.FIELDS if f.name == "characters")
        assert char_field.priority == FieldPriority.CRITICAL

    def test_pack_with_budget(self):
        """Should pack within token budget."""
        ctx = StoryContext(
            title="测试",
            genre="悬疑",
            characters=[{"name": "角色1"}],
            setting="这是一个非常详细的背景设定" * 100,
        )
        packed = ctx.pack(max_tokens=500)
        # Title and characters (critical) should be present
        assert "title" in packed
        assert "characters" in packed


class TestEpisodeContext:
    """Tests for EpisodeContext."""

    def test_required_fields(self):
        """Should require story_outline and episode_number."""
        ctx = EpisodeContext()
        errors = ctx.validate()
        assert any("story_outline" in e for e in errors)
        assert any("episode_number" in e for e in errors)

    def test_valid_context(self):
        """Should pass with all required fields."""
        ctx = EpisodeContext(
            story_outline="故事大纲内容",
            episode_number=1,
        )
        errors = ctx.validate()
        assert errors == []

    def test_continuity_ledger_truncation(self):
        """Continuity ledger should be truncatable."""
        ledger_field = next(f for f in EpisodeContext.FIELDS if f.name == "continuity_ledger")
        assert ledger_field.max_tokens == 1000

    def test_pack_preserves_critical_fields(self):
        """Pack should preserve critical fields."""
        ctx = EpisodeContext(
            story_outline="大纲",
            episode_number=1,
            continuity_ledger="连续性" * 500,  # Long
        )
        packed = ctx.pack(max_tokens=100)
        assert "story_outline" in packed
        assert "episode_number" in packed


class TestScriptContext:
    """Tests for ScriptContext."""

    def test_required_fields(self):
        """Should require episode_outline and scene_index."""
        ctx = ScriptContext()
        errors = ctx.validate()
        assert any("episode_outline" in e for e in errors)
        assert any("scene_index" in e for e in errors)

    def test_valid_context(self):
        """Should pass with all required fields."""
        ctx = ScriptContext(
            episode_outline="剧集大纲",
            scene_index=0,
        )
        errors = ctx.validate()
        assert errors == []

    def test_characters_in_scene_no_truncation(self):
        """Characters in scene should not be truncated."""
        from app.services.agent_core.context_spec import TruncationStrategy

        char_field = next(f for f in ScriptContext.FIELDS if f.name == "characters_in_scene")
        assert char_field.truncation == TruncationStrategy.NONE


class TestTimelineContext:
    """Tests for TimelineContext."""

    def test_required_fields(self):
        """Should require script and target_duration."""
        ctx = TimelineContext()
        errors = ctx.validate()
        assert any("script" in e for e in errors)
        assert any("target_duration" in e for e in errors)

    def test_valid_context(self):
        """Should pass with all required fields."""
        ctx = TimelineContext(
            script="场景一：\n角色A：你好",
            target_duration=60,
        )
        errors = ctx.validate()
        assert errors == []

    def test_script_critical_no_truncation(self):
        """Script should be critical and not truncatable."""
        from app.services.agent_core.context_spec import TruncationStrategy

        script_field = next(f for f in TimelineContext.FIELDS if f.name == "script")
        assert script_field.priority == FieldPriority.CRITICAL
        assert script_field.truncation == TruncationStrategy.NONE


class TestStoryboardContext:
    """Tests for StoryboardContext."""

    def test_required_fields(self):
        """Should require script_beat."""
        ctx = StoryboardContext()
        errors = ctx.validate()
        assert any("script_beat" in e for e in errors)

    def test_valid_context(self):
        """Should pass with required fields."""
        ctx = StoryboardContext(
            script_beat="角色A走进房间，看向窗外",
        )
        errors = ctx.validate()
        assert errors == []

    def test_characters_critical(self):
        """Characters should be critical priority."""
        char_field = next(f for f in StoryboardContext.FIELDS if f.name == "characters")
        assert char_field.priority == FieldPriority.CRITICAL


class TestFieldCoverage:
    """Tests to ensure all context specs have proper field coverage."""

    @pytest.mark.parametrize(
        "context_class",
        [StoryContext, EpisodeContext, ScriptContext, TimelineContext, StoryboardContext],
    )
    def test_all_fields_have_descriptions(self, context_class):
        """All fields should have descriptions."""
        for field in context_class.FIELDS:
            assert field.description, f"{context_class.__name__}.{field.name} missing description"

    @pytest.mark.parametrize(
        "context_class",
        [StoryContext, EpisodeContext, ScriptContext, TimelineContext, StoryboardContext],
    )
    def test_has_at_least_one_required_field(self, context_class):
        """Each context should have at least one required field."""
        required_fields = [f for f in context_class.FIELDS if f.required]
        assert len(required_fields) > 0, f"{context_class.__name__} has no required fields"

    @pytest.mark.parametrize(
        "context_class",
        [StoryContext, EpisodeContext, ScriptContext, TimelineContext, StoryboardContext],
    )
    def test_has_critical_fields(self, context_class):
        """Each context should have at least one critical field."""
        critical_fields = [f for f in context_class.FIELDS if f.priority == FieldPriority.CRITICAL]
        assert len(critical_fields) > 0, f"{context_class.__name__} has no critical fields"


class TestTokenBudgetScenarios:
    """Tests for realistic token budget scenarios."""

    def test_story_context_full_pack(self):
        """Story context should pack all fields when budget allows."""
        ctx = StoryContext(
            title="测试故事",
            genre="悬疑",
            characters=[{"name": "主角", "desc": "30岁男性"}],
            setting="现代都市",
            theme="成长",
            tone="紧张",
            constraints="无血腥暴力",
            hook_requirements="每集结尾留悬念",
            target_duration=300,
            episode_count=10,
        )
        packed = ctx.pack(max_tokens=5000)
        # All fields should be present with large budget
        assert "title" in packed
        assert "genre" in packed
        assert "characters" in packed

    def test_episode_context_tight_budget(self):
        """Episode context should prioritize under tight budget."""
        ctx = EpisodeContext(
            story_outline="这是故事大纲",  # Short critical field
            episode_number=5,
            total_episodes=10,
            target_duration=60,
            characters=[{"name": "A"}, {"name": "B"}],
            continuity_ledger={"facts": ["fact1"] * 100},  # Long non-critical
            previous_summary="上集回顾" * 50,  # Long low-priority
            arc_requirements="角色A需要成长",
            hook_plan="本集悬念",
        )
        packed = ctx.pack(max_tokens=100)
        # Critical fields should be present
        assert "story_outline" in packed
        assert "episode_number" in packed
        # With tight budget, lower priority fields may be truncated
