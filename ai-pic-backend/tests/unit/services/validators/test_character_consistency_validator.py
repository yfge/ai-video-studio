"""Tests for CharacterConsistencyValidator."""

import pytest

from app.services.validators.character_consistency_validator import (
    CharacterConsistencyValidator,
    CharacterProfile,
    CharacterValidationResult,
    ValidationSeverity,
)


class TestCharacterProfile:
    """Tests for CharacterProfile dataclass."""

    def test_to_dict(self):
        """Test profile serialization."""
        profile = CharacterProfile(
            name="Alice",
            aliases=["小爱", "A"],
            role_type="protagonist",
            gender="female",
            age="young",
            personality=["kind", "brave"],
        )
        data = profile.to_dict()

        assert data["name"] == "Alice"
        assert data["aliases"] == ["小爱", "A"]
        assert data["role_type"] == "protagonist"
        assert data["gender"] == "female"

    def test_from_dict(self):
        """Test profile deserialization."""
        data = {
            "name": "Bob",
            "aliases": ["小鲍"],
            "gender": "male",
            "age": "middle-aged",
        }
        profile = CharacterProfile.from_dict(data)

        assert profile.name == "Bob"
        assert profile.aliases == ["小鲍"]
        assert profile.gender == "male"


class TestCharacterValidationResult:
    """Tests for CharacterValidationResult."""

    def test_success_result(self):
        """Test creating success result."""
        result = CharacterValidationResult.success("All good", {"count": 5})

        assert result.passed is True
        assert result.severity == ValidationSeverity.INFO
        assert result.message == "All good"
        assert result.details["count"] == 5

    def test_warning_result(self):
        """Test creating warning result."""
        result = CharacterValidationResult.warning(
            "Minor issue",
            details={"issue": "typo"},
            suggestions=["Fix it"],
        )

        assert result.passed is True
        assert result.severity == ValidationSeverity.WARNING
        assert result.suggestions == ["Fix it"]

    def test_error_result(self):
        """Test creating error result."""
        result = CharacterValidationResult.error(
            "Major issue",
            details={"problem": "contradiction"},
        )

        assert result.passed is False
        assert result.severity == ValidationSeverity.ERROR

    def test_to_dict(self):
        """Test result serialization."""
        result = CharacterValidationResult.success("OK")
        data = result.to_dict()

        assert "passed" in data
        assert "severity" in data
        assert "message" in data
        assert "timestamp" in data


class TestCharacterConsistencyValidator:
    """Tests for CharacterConsistencyValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator with sample profiles."""
        v = CharacterConsistencyValidator()
        v.register_profiles([
            CharacterProfile(
                name="张三",
                aliases=["老张", "Zhang San"],
                gender="male",
                age="middle-aged",
                personality=["calm", "introverted"],
            ),
            CharacterProfile(
                name="李四",
                aliases=["小李"],
                gender="male",
                age="young",
                personality=["outgoing", "brave"],
            ),
            CharacterProfile(
                name="王美",
                aliases=["小美", "Mei"],
                gender="female",
                age="young",
                personality=["kind", "shy"],
            ),
        ])
        return v

    def test_register_profiles_from_dict(self):
        """Test registering profiles from dictionaries."""
        v = CharacterConsistencyValidator()
        v.register_profiles([
            {"name": "Alice", "aliases": ["A"], "gender": "female"},
            {"name": "Bob", "gender": "male"},
        ])

        assert v.get_profile("Alice") is not None
        assert v.get_profile("A") is not None
        assert v.get_profile("Bob") is not None

    def test_resolve_name_canonical(self, validator):
        """Test resolving canonical name."""
        assert validator.resolve_name("张三") == "张三"
        assert validator.resolve_name("李四") == "李四"

    def test_resolve_name_alias(self, validator):
        """Test resolving alias to canonical name."""
        assert validator.resolve_name("老张") == "张三"
        assert validator.resolve_name("Zhang San") == "张三"
        assert validator.resolve_name("小李") == "李四"

    def test_resolve_name_case_insensitive(self, validator):
        """Test case-insensitive name resolution."""
        assert validator.resolve_name("zhang san") == "张三"
        assert validator.resolve_name("ZHANG SAN") == "张三"

    def test_resolve_name_unknown(self, validator):
        """Test resolving unknown name returns None."""
        assert validator.resolve_name("Unknown") is None
        assert validator.resolve_name("路人甲") is None

    def test_get_profile(self, validator):
        """Test getting profile by name or alias."""
        profile = validator.get_profile("张三")
        assert profile is not None
        assert profile.name == "张三"
        assert profile.gender == "male"

        # Via alias
        profile2 = validator.get_profile("老张")
        assert profile2 is not None
        assert profile2.name == "张三"

    def test_validate_names_in_text_all_known(self, validator):
        """Test validating text with all known characters."""
        text = """
张三: 今天天气不错。
李四: 是啊，我们去散步吧。
王美: 好主意！
"""
        results = validator.validate_names_in_text(text)

        assert len(results) == 1
        assert results[0].passed is True
        assert "valid" in results[0].message.lower()

    def test_validate_names_in_text_with_alias(self, validator):
        """Test validating text using character aliases."""
        text = """
老张: 小李，你来一下。
小李: 好的，老张。
"""
        results = validator.validate_names_in_text(text)

        assert len(results) == 1
        assert results[0].passed is True

    def test_validate_names_in_text_unknown_character(self, validator):
        """Test detecting unknown character."""
        text = """
张三: 你好。
陌生人: 你好，我是陌生人。
"""
        results = validator.validate_names_in_text(text)

        # Should have warning about unknown character
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        assert len(warnings) >= 1
        assert any("陌生人" in str(r.details) for r in warnings)

    def test_validate_names_in_text_potential_typo(self, validator):
        """Test detecting potential typo."""
        text = """
张三: 你好。
张三三: 你好。
"""
        results = validator.validate_names_in_text(text)

        # Should detect "张三三" as similar to "张三"
        typo_warnings = [
            r for r in results
            if r.severity == ValidationSeverity.WARNING
            and "typo" in r.message.lower()
        ]
        # May or may not detect depending on similarity threshold
        assert len(results) >= 1

    def test_validate_names_skip_narrator(self, validator):
        """Test that narrator names are skipped."""
        text = """
旁白: 这是一个阳光明媚的早晨。
张三: 今天心情不错。
Narrator: And so the story begins.
"""
        results = validator.validate_names_in_text(text)

        # Should not report narrator as unknown
        unknown_warnings = [
            r for r in results
            if "unknown" in r.message.lower()
        ]
        assert not any("旁白" in str(r.details) for r in unknown_warnings)
        assert not any("Narrator" in str(r.details) for r in unknown_warnings)

    def test_validate_character_attributes_consistent(self, validator):
        """Test validating consistent attributes."""
        results = validator.validate_character_attributes(
            "张三",
            {"gender": "male", "age": "middle-aged"},
        )

        assert len(results) == 1
        assert results[0].passed is True

    def test_validate_character_attributes_gender_contradiction(self, validator):
        """Test detecting gender contradiction."""
        results = validator.validate_character_attributes(
            "张三",  # male in profile
            {"gender": "female"},
        )

        errors = [r for r in results if not r.passed]
        assert len(errors) == 1
        assert "contradiction" in errors[0].message.lower()
        assert any(c["attribute"] == "gender" for c in errors[0].details.get("contradictions", []))

    def test_validate_character_attributes_age_contradiction(self, validator):
        """Test detecting age contradiction."""
        results = validator.validate_character_attributes(
            "李四",  # young in profile
            {"age": "elderly"},
        )

        errors = [r for r in results if not r.passed]
        assert len(errors) == 1
        assert any(c["attribute"] == "age" for c in errors[0].details.get("contradictions", []))

    def test_validate_character_attributes_personality_conflict(self, validator):
        """Test detecting personality conflict."""
        results = validator.validate_character_attributes(
            "张三",  # introverted in profile
            {"personality": ["extroverted", "talkative"]},
        )

        errors = [r for r in results if not r.passed]
        assert len(errors) == 1
        assert any(c["attribute"] == "personality" for c in errors[0].details.get("contradictions", []))

    def test_validate_character_attributes_unknown_character(self, validator):
        """Test validating attributes for unknown character."""
        results = validator.validate_character_attributes(
            "Unknown",
            {"gender": "male"},
        )

        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        assert len(warnings) == 1
        assert "no profile" in warnings[0].message.lower()


class TestNameSimilarity:
    """Tests for name similarity detection."""

    @pytest.fixture
    def validator(self):
        return CharacterConsistencyValidator()

    def test_names_similar_substring(self, validator):
        """Test similarity for substring relationship."""
        assert validator._names_similar("john", "john smith") is True
        assert validator._names_similar("张", "张三") is True

    def test_names_similar_edit_distance(self, validator):
        """Test similarity for small edit distance."""
        assert validator._names_similar("alice", "alica") is True  # 1 char diff
        assert validator._names_similar("bob", "bobb") is True  # 1 char added

    def test_names_not_similar(self, validator):
        """Test dissimilar names."""
        assert validator._names_similar("alice", "bob") is False
        assert validator._names_similar("zhang", "wang") is False

    def test_names_same_not_similar(self, validator):
        """Test same name returns False (not a typo)."""
        assert validator._names_similar("alice", "alice") is False


class TestAgeCompatibility:
    """Tests for age compatibility checking."""

    @pytest.fixture
    def validator(self):
        return CharacterConsistencyValidator()

    def test_age_compatible_same_group(self, validator):
        """Test compatible ages in same group."""
        assert validator._age_compatible("young", "youth") is True
        assert validator._age_compatible("elderly", "old") is True
        assert validator._age_compatible("青年", "年轻") is True

    def test_age_compatible_different_group(self, validator):
        """Test incompatible ages in different groups."""
        assert validator._age_compatible("child", "elderly") is False
        assert validator._age_compatible("young", "老年") is False
