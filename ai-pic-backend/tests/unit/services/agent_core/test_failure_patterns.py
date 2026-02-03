"""Tests for Failure Pattern Library."""

import pytest

from app.services.agent_core.failure_patterns import (
    COMMON_PATTERNS,
    FailurePattern,
    FailurePatternMatcher,
    PatternCategory,
)


class TestPatternCategory:
    """Tests for PatternCategory enum."""

    def test_all_categories_defined(self):
        """Verify all expected categories exist."""
        expected = {
            "json_syntax",
            "schema_violation",
            "content_length",
            "missing_field",
            "character_inconsistency",
            "timeline_error",
            "logic_error",
            "format_error",
            "api_error",
        }
        actual = {c.value for c in PatternCategory}
        assert actual == expected


class TestFailurePattern:
    """Tests for FailurePattern dataclass."""

    def test_create_pattern(self):
        """Create a failure pattern."""
        pattern = FailurePattern(
            name="test_pattern",
            category=PatternCategory.JSON_SYNTAX,
            patterns=[r"test.*error"],
            description="A test pattern",
            repair_hints=["Fix the test"],
        )
        assert pattern.name == "test_pattern"
        assert pattern.category == PatternCategory.JSON_SYNTAX
        assert len(pattern.patterns) == 1

    def test_pattern_compiles_regex(self):
        """Patterns should be compiled on init."""
        pattern = FailurePattern(
            name="test",
            category=PatternCategory.JSON_SYNTAX,
            patterns=[r"foo\d+bar"],
            description="Test",
        )
        assert len(pattern._compiled) == 1

    def test_matches_returns_true(self):
        """matches() should return True for matching text."""
        pattern = FailurePattern(
            name="test",
            category=PatternCategory.JSON_SYNTAX,
            patterns=[r"expecting.*\}"],
            description="Test",
        )
        assert pattern.matches("Error: expecting '}'") is True

    def test_matches_returns_false(self):
        """matches() should return False for non-matching text."""
        pattern = FailurePattern(
            name="test",
            category=PatternCategory.JSON_SYNTAX,
            patterns=[r"expecting.*\}"],
            description="Test",
        )
        assert pattern.matches("Everything is fine") is False

    def test_matches_case_insensitive(self):
        """Pattern matching should be case insensitive."""
        pattern = FailurePattern(
            name="test",
            category=PatternCategory.JSON_SYNTAX,
            patterns=[r"error"],
            description="Test",
        )
        assert pattern.matches("ERROR occurred") is True
        assert pattern.matches("Error occurred") is True
        assert pattern.matches("error occurred") is True

    def test_multiple_patterns(self):
        """Should match any of multiple patterns."""
        pattern = FailurePattern(
            name="test",
            category=PatternCategory.JSON_SYNTAX,
            patterns=[r"error", r"failure", r"exception"],
            description="Test",
        )
        assert pattern.matches("An error occurred") is True
        assert pattern.matches("System failure") is True
        assert pattern.matches("Exception thrown") is True
        assert pattern.matches("Success!") is False

    def test_to_dict(self):
        """Pattern should serialize to dictionary."""
        pattern = FailurePattern(
            name="test_pattern",
            category=PatternCategory.API_ERROR,
            patterns=[r"rate.*limit"],
            description="Rate limit hit",
            repair_hints=["Wait and retry"],
            severity="high",
        )
        result = pattern.to_dict()
        assert result["name"] == "test_pattern"
        assert result["category"] == "api_error"
        assert result["severity"] == "high"
        assert "patterns" not in result  # Not included in serialization


class TestCommonPatterns:
    """Tests for the common patterns library."""

    def test_patterns_exist(self):
        """Library should have patterns defined."""
        assert len(COMMON_PATTERNS) > 0

    def test_all_patterns_have_required_fields(self):
        """All patterns should have required fields."""
        for pattern in COMMON_PATTERNS:
            assert pattern.name
            assert pattern.category
            assert len(pattern.patterns) > 0
            assert pattern.description

    def test_json_syntax_patterns_exist(self):
        """JSON syntax patterns should exist."""
        json_patterns = [
            p for p in COMMON_PATTERNS
            if p.category == PatternCategory.JSON_SYNTAX
        ]
        assert len(json_patterns) >= 3  # unclosed brace, array, trailing comma

    def test_api_error_patterns_exist(self):
        """API error patterns should exist."""
        api_patterns = [
            p for p in COMMON_PATTERNS
            if p.category == PatternCategory.API_ERROR
        ]
        assert len(api_patterns) >= 2  # rate limit, context length


class TestFailurePatternMatcher:
    """Tests for FailurePatternMatcher."""

    def test_create_with_default_patterns(self):
        """Matcher should use default patterns."""
        matcher = FailurePatternMatcher()
        assert len(matcher.patterns) == len(COMMON_PATTERNS)

    def test_create_with_custom_patterns(self):
        """Matcher should accept custom patterns."""
        custom = [
            FailurePattern(
                name="custom",
                category=PatternCategory.LOGIC_ERROR,
                patterns=[r"custom error"],
                description="Custom",
            )
        ]
        matcher = FailurePatternMatcher(patterns=custom)
        assert len(matcher.patterns) == 1

    def test_match_returns_all_matching(self):
        """match() should return all matching patterns."""
        matcher = FailurePatternMatcher()
        # This should match rate limit patterns
        matches = matcher.match("rate limit exceeded, too many requests")
        assert len(matches) >= 1
        assert any(p.name == "rate_limit" for p in matches)

    def test_match_returns_empty_for_no_match(self):
        """match() should return empty list for no match."""
        matcher = FailurePatternMatcher()
        matches = matcher.match("Everything is working perfectly")
        assert matches == []

    def test_match_first_returns_first(self):
        """match_first() should return first matching pattern."""
        matcher = FailurePatternMatcher()
        pattern = matcher.match_first("Expecting '}'")
        assert pattern is not None
        assert pattern.category == PatternCategory.JSON_SYNTAX

    def test_match_first_returns_none(self):
        """match_first() should return None for no match."""
        matcher = FailurePatternMatcher()
        pattern = matcher.match_first("All good")
        assert pattern is None

    def test_get_repair_hints(self):
        """get_repair_hints() should return combined hints."""
        matcher = FailurePatternMatcher()
        hints = matcher.get_repair_hints("Expecting '}'")
        assert len(hints) > 0
        # Should have Chinese hints from the pattern
        assert any("}" in h for h in hints)

    def test_get_repair_hints_empty_for_no_match(self):
        """get_repair_hints() should return empty for no match."""
        matcher = FailurePatternMatcher()
        hints = matcher.get_repair_hints("No errors here")
        assert hints == []

    def test_classify_category(self):
        """classify_category() should return correct category."""
        matcher = FailurePatternMatcher()
        category = matcher.classify_category("JSON parse error: expecting '}'")
        assert category == PatternCategory.JSON_SYNTAX

    def test_classify_category_none_for_no_match(self):
        """classify_category() should return None for no match."""
        matcher = FailurePatternMatcher()
        category = matcher.classify_category("Random text")
        assert category is None

    def test_add_pattern(self):
        """add_pattern() should add custom pattern."""
        matcher = FailurePatternMatcher()
        initial_count = len(matcher.patterns)
        matcher.add_pattern(
            FailurePattern(
                name="new_pattern",
                category=PatternCategory.LOGIC_ERROR,
                patterns=[r"new error type"],
                description="New pattern",
            )
        )
        assert len(matcher.patterns) == initial_count + 1
        assert matcher.match_first("new error type") is not None

    def test_get_patterns_by_category(self):
        """get_patterns_by_category() should filter correctly."""
        matcher = FailurePatternMatcher()
        json_patterns = matcher.get_patterns_by_category(PatternCategory.JSON_SYNTAX)
        assert all(p.category == PatternCategory.JSON_SYNTAX for p in json_patterns)
        assert len(json_patterns) >= 1


class TestRealWorldErrors:
    """Tests against real-world error messages."""

    @pytest.fixture
    def matcher(self):
        """Create matcher for tests."""
        return FailurePatternMatcher()

    def test_json_decode_error(self, matcher):
        """Should match JSON decode errors."""
        # Use error message that matches the patterns we defined
        error = "JSONDecodeError: Expecting '}' delimiter: line 5 column 2"
        pattern = matcher.match_first(error)
        assert pattern is not None
        assert pattern.category == PatternCategory.JSON_SYNTAX

    def test_openai_rate_limit(self, matcher):
        """Should match OpenAI rate limit errors."""
        error = "Rate limit exceeded. Please retry after 20 seconds."
        pattern = matcher.match_first(error)
        assert pattern is not None
        assert pattern.name == "rate_limit"

    def test_token_limit(self, matcher):
        """Should match token limit errors."""
        error = "Context length exceeded: input too long for this model"
        pattern = matcher.match_first(error)
        assert pattern is not None
        assert pattern.name == "context_length_exceeded"

    def test_chinese_dialogue_error(self, matcher):
        """Should match Chinese error messages."""
        error = "台词超过15字限制"
        pattern = matcher.match_first(error)
        assert pattern is not None
        assert pattern.name == "dialogue_too_long"

    def test_chinese_character_error(self, matcher):
        """Should match Chinese character errors."""
        error = "未知角色: 张三"
        pattern = matcher.match_first(error)
        assert pattern is not None
        assert pattern.name == "unknown_character"

    def test_trailing_comma_error(self, matcher):
        """Should match trailing comma errors."""
        error = "Invalid JSON: trailing comma detected before }"
        pattern = matcher.match_first(error)
        assert pattern is not None
        assert pattern.name == "trailing_comma"


class TestPatternSeverity:
    """Tests for pattern severity levels."""

    def test_severity_values(self):
        """Patterns should have valid severity values."""
        for pattern in COMMON_PATTERNS:
            assert pattern.severity in {"low", "medium", "high"}

    def test_api_errors_severity(self):
        """API errors should generally be medium or high."""
        api_patterns = [
            p for p in COMMON_PATTERNS
            if p.category == PatternCategory.API_ERROR
        ]
        for pattern in api_patterns:
            assert pattern.severity in {"medium", "high"}
