"""Unit tests for InfoGateValidator."""

from __future__ import annotations

import pytest

from app.schemas.continuity import RevealedInfoItem
from app.services.validators.info_gate_validator import (
    InfoGateContext,
    InfoGateSeverity,
    InfoGateValidator,
    InfoGateViolation,
    InfoGateViolationType,
)


class TestInfoGateViolation:
    """Tests for InfoGateViolation dataclass."""

    def test_to_dict_basic(self) -> None:
        """Test basic serialization."""
        violation = InfoGateViolation(
            violation_type=InfoGateViolationType.CHARACTER_KNOWS_TOO_MUCH,
            severity=InfoGateSeverity.ERROR,
            message="Test message",
        )
        result = violation.to_dict()
        assert result["violation_type"] == "character_knows_too_much"
        assert result["severity"] == "error"
        assert result["message"] == "Test message"

    def test_to_dict_full(self) -> None:
        """Test full serialization with all fields."""
        violation = InfoGateViolation(
            violation_type=InfoGateViolationType.REFERENCES_FUTURE_EVENT,
            severity=InfoGateSeverity.WARNING,
            message="Future reference",
            speaker="张三",
            dialogue_text="我知道明天会下雨",
            referenced_info="明天下雨",
            episode_number=1,
            scene_number=3,
            fix_suggestion="删除此对白",
        )
        result = violation.to_dict()
        assert result["speaker"] == "张三"
        assert result["dialogue_text"] == "我知道明天会下雨"
        assert result["episode_number"] == 1
        assert result["scene_number"] == 3


class TestInfoGateValidator:
    """Tests for InfoGateValidator."""

    @pytest.fixture
    def validator(self) -> InfoGateValidator:
        """Create a validator instance."""
        return InfoGateValidator()

    @pytest.fixture
    def sample_revealed_info(self) -> list[RevealedInfoItem]:
        """Create sample revealed info items."""
        return [
            RevealedInfoItem(
                info_key="secret_identity_lisi",
                info_content="李四是卧底警察",
                revealed_to=["张三"],
                revealed_at_episode=2,
                revealed_at_scene=5,
                info_type="identity",
                is_public=False,
            ),
            RevealedInfoItem(
                info_key="murder_weapon",
                info_content="凶器是一把匕首",
                revealed_to=["观众", "侦探王"],
                revealed_at_episode=1,
                revealed_at_scene=3,
                info_type="fact",
                is_public=False,
            ),
            RevealedInfoItem(
                info_key="company_name",
                info_content="公司名为天海集团",
                revealed_to=[],
                revealed_at_episode=1,
                revealed_at_scene=1,
                info_type="fact",
                is_public=True,
            ),
        ]

    def test_register_revealed_info(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test registering revealed info."""
        validator.register_revealed_info(sample_revealed_info)
        assert "secret_identity_lisi" in validator._info_registry
        assert "murder_weapon" in validator._info_registry
        assert "company_name" in validator._info_registry

    def test_extract_keywords(self, validator: InfoGateValidator) -> None:
        """Test keyword extraction."""
        keywords = validator._extract_keywords("李四是卧底警察")
        # Bi-grams and tri-grams should be extracted
        assert "李四" in keywords  # bi-gram
        assert "卧底" in keywords  # bi-gram
        assert "警察" in keywords  # bi-gram
        assert "卧底警" in keywords  # tri-gram
        # Common single chars should not be standalone keywords
        # (though they may appear in bi-grams like "四是")

    def test_extract_keywords_english(self, validator: InfoGateValidator) -> None:
        """Test keyword extraction for English text."""
        keywords = validator._extract_keywords("The detective found a clue")
        assert "detective" in keywords
        assert "found" in keywords
        assert "clue" in keywords
        # Common words should be filtered
        assert "The" not in keywords
        assert "the" not in keywords

    def test_build_context_episode_1(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test building context for episode 1."""
        validator.register_revealed_info(sample_revealed_info)
        context = validator.build_context(episode_number=1, scene_number=5)

        # Public info should be known to audience
        assert "company_name" in context.audience_knowledge
        # Murder weapon revealed in ep1 scene3, should be known
        assert "murder_weapon" in context.audience_knowledge
        # Secret identity not yet revealed (ep2)
        assert "secret_identity_lisi" not in context.audience_knowledge

    def test_build_context_episode_2(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test building context for episode 2."""
        validator.register_revealed_info(sample_revealed_info)
        context = validator.build_context(episode_number=2, scene_number=6)

        # Secret identity revealed in ep2 scene5, should be known to 张三
        assert "张三" in context.character_knowledge
        assert "secret_identity_lisi" in context.character_knowledge["张三"]

    def test_build_context_scene_boundary(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test context respects scene boundaries within same episode."""
        validator.register_revealed_info(sample_revealed_info)

        # Before reveal scene
        context_before = validator.build_context(episode_number=2, scene_number=4)
        assert "secret_identity_lisi" not in context_before.character_knowledge.get(
            "张三", set()
        )

        # After reveal scene
        context_after = validator.build_context(episode_number=2, scene_number=6)
        assert "secret_identity_lisi" in context_after.character_knowledge.get(
            "张三", set()
        )

    def test_validate_dialogue_no_violation(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test dialogue with no violations."""
        validator.register_revealed_info(sample_revealed_info)
        context = validator.build_context(episode_number=2, scene_number=6)

        # 张三 knows about 李四 after ep2 scene5
        violations = validator.validate_dialogue(
            speaker="张三",
            dialogue_text="我知道李四是卧底警察",
            context=context,
        )
        assert len(violations) == 0

    def test_validate_dialogue_character_knows_too_much(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test detection of character knowing unrevealed info."""
        validator.register_revealed_info(sample_revealed_info)
        context = validator.build_context(episode_number=1, scene_number=1)

        # 侦探王 shouldn't know about 李四 being undercover in ep1
        violations = validator.validate_dialogue(
            speaker="侦探王",
            dialogue_text="李四是卧底警察",
            context=context,
        )
        assert len(violations) > 0
        assert violations[0].violation_type == InfoGateViolationType.REFERENCES_FUTURE_EVENT

    def test_validate_dialogue_future_event(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test detection of referencing future events."""
        validator.register_revealed_info(sample_revealed_info)
        context = validator.build_context(episode_number=1, scene_number=2)

        # Anyone mentioning undercover info in ep1 is referencing future
        # Use dialogue that contains keywords from the revealed info
        violations = validator.validate_dialogue(
            speaker="路人甲",
            dialogue_text="我听说李四是卧底",  # "卧底" matches info keywords
            context=context,
        )
        # "卧底" keyword matches "李四是卧底警察"
        assert len(violations) > 0

    def test_validate_dialogue_public_info_ok(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test that public info doesn't cause violations."""
        validator.register_revealed_info(sample_revealed_info)
        context = validator.build_context(episode_number=1, scene_number=2)

        # Company name is public
        violations = validator.validate_dialogue(
            speaker="路人甲",
            dialogue_text="天海集团是一家大公司",
            context=context,
        )
        # Should not trigger violation for public info
        assert all(
            v.referenced_info != "公司名为天海集团" for v in violations
        )

    def test_validate_script_content(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test validating entire script content."""
        validator.register_revealed_info(sample_revealed_info)

        script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "dialogues": [
                        {"speaker": "张三", "text": "你好"},
                        {"speaker": "李四", "text": "今天天气不错"},
                    ],
                },
                {
                    "scene_number": 2,
                    "dialogues": [
                        {"speaker": "路人", "text": "听说李四是卧底警察"},  # Violation!
                    ],
                },
            ]
        }

        violations = validator.validate_script_content(script, episode_number=1)
        assert len(violations) > 0
        # The violation should be about 李四/卧底
        assert any("卧底" in (v.referenced_info or "") for v in violations)

    def test_validate_script_content_alternative_keys(
        self, validator: InfoGateValidator, sample_revealed_info: list[RevealedInfoItem]
    ) -> None:
        """Test script validation with alternative dialogue keys."""
        validator.register_revealed_info(sample_revealed_info)

        # Using "character" and "content" instead of "speaker" and "text"
        script = {
            "scenes": [
                {
                    "scene_number": 1,
                    "dialogue": [
                        {"character": "张三", "content": "你好"},
                    ],
                },
            ]
        }

        violations = validator.validate_script_content(script, episode_number=1)
        # Should handle alternative keys without error
        assert isinstance(violations, list)

    def test_generate_fix_suggestions(
        self, validator: InfoGateValidator
    ) -> None:
        """Test fix suggestion generation."""
        violations = [
            InfoGateViolation(
                violation_type=InfoGateViolationType.CHARACTER_KNOWS_TOO_MUCH,
                severity=InfoGateSeverity.ERROR,
                message="角色知道太多",
                speaker="张三",
                referenced_info="秘密信息",
            ),
            InfoGateViolation(
                violation_type=InfoGateViolationType.REFERENCES_FUTURE_EVENT,
                severity=InfoGateSeverity.ERROR,
                message="引用未来事件",
            ),
        ]

        suggestions = validator.generate_fix_suggestions(violations)
        assert len(suggestions) == 2
        assert "suggested_actions" in suggestions[0]
        assert len(suggestions[0]["suggested_actions"]) > 0


class TestInfoGateContext:
    """Tests for InfoGateContext dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        context = InfoGateContext(current_episode=1)
        assert context.current_episode == 1
        assert context.current_scene is None
        assert context.character_knowledge == {}
        assert context.audience_knowledge == set()
        assert context.revealed_items == []

    def test_with_values(self) -> None:
        """Test with populated values."""
        context = InfoGateContext(
            current_episode=3,
            current_scene=5,
            character_knowledge={"张三": {"info1", "info2"}},
            audience_knowledge={"info1"},
        )
        assert context.current_episode == 3
        assert context.current_scene == 5
        assert "info1" in context.character_knowledge["张三"]
        assert "info1" in context.audience_knowledge
