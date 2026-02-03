"""Tests for Context Specification System."""

import pytest

from app.services.agent_core.context_spec import (
    ContextSpec,
    FieldPriority,
    FieldSpec,
    TruncationStrategy,
    estimate_tokens,
    is_non_empty_list,
    is_non_empty_string,
    is_positive_int,
    normalize_newlines,
    strip_whitespace,
    truncate_text,
)


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_empty_string(self):
        """Empty string should return 0 tokens."""
        assert estimate_tokens("") == 0

    def test_english_text(self):
        """English text should estimate ~0.25 tokens per char."""
        text = "Hello world this is a test"  # 26 chars
        tokens = estimate_tokens(text)
        # 26 * 0.25 = 6.5 -> 6
        assert 5 <= tokens <= 10

    def test_chinese_text(self):
        """Chinese text should estimate ~0.6 tokens per char."""
        text = "你好世界这是测试"  # 8 Chinese chars
        tokens = estimate_tokens(text)
        # 8 * 0.6 = 4.8 -> 4
        assert 3 <= tokens <= 8

    def test_mixed_text(self):
        """Mixed text should combine estimates."""
        text = "Hello 世界"  # 6 English + 2 Chinese
        tokens = estimate_tokens(text)
        # 6 * 0.25 + 2 * 0.6 = 1.5 + 1.2 = 2.7 -> 2
        assert 1 <= tokens <= 5


class TestTruncateText:
    """Tests for text truncation."""

    def test_no_truncation_needed(self):
        """Short text should not be truncated."""
        text = "Short"
        result = truncate_text(text, max_tokens=100)
        assert result == text

    def test_tail_truncation(self):
        """Tail truncation should keep beginning."""
        text = "First line\nSecond line\nThird line\nFourth line"
        result = truncate_text(text, max_tokens=5, strategy=TruncationStrategy.TAIL)
        assert result.startswith("First")
        assert "..." in result

    def test_head_truncation(self):
        """Head truncation should keep end."""
        text = "First line\nSecond line\nThird line\nFourth line"
        result = truncate_text(text, max_tokens=5, strategy=TruncationStrategy.HEAD)
        assert "..." in result
        assert "line" in result

    def test_middle_truncation(self):
        """Middle truncation should keep beginning and end."""
        text = "Start....." + "middle" * 100 + "......End"
        result = truncate_text(text, max_tokens=10, strategy=TruncationStrategy.MIDDLE)
        assert "Start" in result
        assert "..." in result
        assert "End" in result

    def test_none_strategy(self):
        """None strategy should return original."""
        text = "Long text " * 100
        result = truncate_text(text, max_tokens=5, strategy=TruncationStrategy.NONE)
        assert result == text

    def test_empty_text(self):
        """Empty text should return empty."""
        assert truncate_text("", max_tokens=10) == ""

    def test_zero_max_tokens(self):
        """Zero max_tokens should return empty."""
        assert truncate_text("Some text", max_tokens=0) == ""


class TestFieldSpec:
    """Tests for FieldSpec."""

    def test_create_basic_field(self):
        """Create field with minimal config."""
        field = FieldSpec(name="test", description="Test field")
        assert field.name == "test"
        assert field.priority == FieldPriority.MEDIUM
        assert field.required is False

    def test_validate_required_field(self):
        """Required field should fail with None."""
        field = FieldSpec(name="test", description="Test", required=True)
        assert field.validate(None) is False
        assert field.validate("value") is True

    def test_custom_validator(self):
        """Custom validator should be called."""
        field = FieldSpec(
            name="test",
            description="Test",
            validator=lambda x: x > 0,
        )
        assert field.validate(5) is True
        assert field.validate(-1) is False

    def test_transformer(self):
        """Transformer should modify value."""
        field = FieldSpec(
            name="test",
            description="Test",
            transformer=lambda x: x.upper(),
        )
        assert field.transform("hello") == "HELLO"


class TestContextSpec:
    """Tests for ContextSpec base class."""

    def test_create_with_fields(self):
        """Create context with field definitions."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="title", description="Title", required=True),
                FieldSpec(name="content", description="Content"),
            ]

        ctx = TestContext(title="Test", content="Body")
        assert ctx.get("title") == "Test"
        assert ctx.get("content") == "Body"

    def test_validation_missing_required(self):
        """Validation should catch missing required fields."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="required_field", description="Required", required=True),
            ]

        ctx = TestContext()
        errors = ctx.validate()
        assert len(errors) == 1
        assert "required_field" in errors[0]

    def test_validation_passes(self):
        """Validation should pass for valid context."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="title", description="Title", required=True),
            ]

        ctx = TestContext(title="Valid")
        errors = ctx.validate()
        assert errors == []

    def test_get_with_default(self):
        """Get should return default for missing fields."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="optional", description="Optional", default="default"),
            ]

        ctx = TestContext()
        assert ctx.get("optional") == "default"
        assert ctx.get("unknown", "fallback") == "fallback"

    def test_set_unknown_field(self):
        """Setting unknown field should log warning."""

        class TestContext(ContextSpec):
            FIELDS = []

        ctx = TestContext()
        ctx.set("unknown", "value")  # Should not raise
        assert ctx.get("unknown") is None

    def test_set_invalid_value(self):
        """Setting invalid value should raise."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(
                    name="positive",
                    description="Positive number",
                    validator=lambda x: x > 0,
                ),
            ]

        ctx = TestContext()
        with pytest.raises(ValueError):
            ctx.set("positive", -5)

    def test_estimate_total_tokens(self):
        """Should estimate total tokens across fields."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="text1", description="Text 1"),
                FieldSpec(name="text2", description="Text 2"),
            ]

        ctx = TestContext(text1="Hello", text2="World")
        tokens = ctx.estimate_total_tokens()
        assert tokens > 0

    def test_pack_basic(self):
        """Pack should return dictionary of values."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="title", description="Title"),
                FieldSpec(name="body", description="Body"),
            ]

        ctx = TestContext(title="Test", body="Content")
        packed = ctx.pack()
        assert packed["title"] == "Test"
        assert packed["body"] == "Content"

    def test_pack_with_truncation(self):
        """Pack should truncate fields exceeding max_tokens."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(
                    name="long_text",
                    description="Long text",
                    max_tokens=5,
                    truncation=TruncationStrategy.TAIL,
                ),
            ]

        ctx = TestContext(long_text="This is a very long text " * 50)
        packed = ctx.pack()
        # Should be truncated
        assert len(packed["long_text"]) < len("This is a very long text " * 50)
        assert "..." in packed["long_text"]

    def test_pack_with_global_budget(self):
        """Pack should respect global token budget."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(
                    name="critical",
                    description="Critical",
                    priority=FieldPriority.CRITICAL,
                ),
                FieldSpec(
                    name="low",
                    description="Low priority",
                    priority=FieldPriority.LOW,
                ),
            ]

        ctx = TestContext(critical="Must keep", low="Can drop " * 100)
        packed = ctx.pack(max_tokens=20)
        # Critical should be kept
        assert "critical" in packed
        # Low priority may be truncated or dropped
        if "low" in packed:
            assert len(packed["low"]) < len("Can drop " * 100)

    def test_pack_priority_order(self):
        """Pack should process fields by priority."""

        class TestContext(ContextSpec):
            FIELDS = [
                FieldSpec(name="low", description="Low", priority=FieldPriority.LOW),
                FieldSpec(
                    name="critical",
                    description="Critical",
                    priority=FieldPriority.CRITICAL,
                ),
                FieldSpec(name="medium", description="Medium", priority=FieldPriority.MEDIUM),
            ]

        ctx = TestContext(low="L", critical="C", medium="M")
        packed = ctx.pack(max_tokens=5)
        # Critical should always be included
        assert "critical" in packed


class TestValidators:
    """Tests for common validators."""

    def test_is_non_empty_string(self):
        """Test non-empty string validator."""
        assert is_non_empty_string("hello") is True
        assert is_non_empty_string("") is False
        assert is_non_empty_string("   ") is False
        assert is_non_empty_string(None) is False
        assert is_non_empty_string(123) is False

    def test_is_non_empty_list(self):
        """Test non-empty list validator."""
        assert is_non_empty_list([1, 2, 3]) is True
        assert is_non_empty_list([]) is False
        assert is_non_empty_list(None) is False
        assert is_non_empty_list("string") is False

    def test_is_positive_int(self):
        """Test positive integer validator."""
        assert is_positive_int(5) is True
        assert is_positive_int(0) is False
        assert is_positive_int(-1) is False
        assert is_positive_int(1.5) is False
        assert is_positive_int("5") is False


class TestTransformers:
    """Tests for common transformers."""

    def test_strip_whitespace(self):
        """Test whitespace stripper."""
        assert strip_whitespace("  hello  ") == "hello"
        assert strip_whitespace("no_space") == "no_space"
        assert strip_whitespace(123) == 123  # Non-string passthrough

    def test_normalize_newlines(self):
        """Test newline normalizer."""
        assert normalize_newlines("a\n\n\n\nb") == "a\n\nb"
        assert normalize_newlines("a\nb") == "a\nb"
        assert normalize_newlines(123) == 123  # Non-string passthrough
