"""Unit tests for EpisodeQualityValidator."""

from __future__ import annotations

import pytest

from app.services.validators.episode_quality_validator import (
    CharacterArc,
    EpisodeQualityIssue,
    EpisodeQualityIssueType,
    EpisodeQualityResult,
    EpisodeQualitySeverity,
    EpisodeQualityValidator,
    ForeshadowingItem,
)


@pytest.fixture
def validator() -> EpisodeQualityValidator:
    """Create a validator instance."""
    return EpisodeQualityValidator()


class TestEpisodeQualityIssue:
    """Tests for EpisodeQualityIssue dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        issue = EpisodeQualityIssue(
            issue_type=EpisodeQualityIssueType.CHARACTER_ARC_STAGNANT,
            severity=EpisodeQualitySeverity.WARNING,
            message="Test message",
            episode_number=1,
            character_name="Alice",
            details={"key": "value"},
            suggestions=["Fix it"],
        )
        result = issue.to_dict()
        assert result["issue_type"] == "character_arc_stagnant"
        assert result["severity"] == "warning"
        assert result["message"] == "Test message"
        assert result["episode_number"] == 1
        assert result["character_name"] == "Alice"


class TestCharacterArc:
    """Tests for CharacterArc dataclass."""

    def test_has_progression_with_changes(self) -> None:
        """Test progression detection with changes."""
        arc = CharacterArc(
            character_name="Alice",
            episode_goals={1: "找到真相", 2: "逃离危险", 3: "战胜敌人"},
            episode_states={1: "迷茫", 2: "觉醒", 3: "成熟"},
        )
        assert arc.has_progression() is True

    def test_has_progression_stagnant(self) -> None:
        """Test progression detection with stagnant character."""
        arc = CharacterArc(
            character_name="Bob",
            episode_goals={1: "帮助朋友", 2: "帮助朋友", 3: "帮助朋友"},
            episode_states={1: "忠诚", 2: "忠诚", 3: "忠诚"},
        )
        assert arc.has_progression() is False

    def test_has_progression_insufficient_data(self) -> None:
        """Test progression with insufficient data."""
        arc = CharacterArc(
            character_name="Carol",
            episode_goals={1: "探索世界"},
        )
        # Not enough data to judge, default to True
        assert arc.has_progression() is True


class TestForeshadowingItem:
    """Tests for ForeshadowingItem dataclass."""

    def test_resolved_item(self) -> None:
        """Test resolved foreshadowing item."""
        item = ForeshadowingItem(
            setup_id="test_1",
            setup_description="神秘信件",
            setup_episode=1,
            payoff_episode=5,
            is_resolved=True,
        )
        assert item.is_resolved
        assert item.payoff_episode == 5

    def test_unresolved_item(self) -> None:
        """Test unresolved foreshadowing item."""
        item = ForeshadowingItem(
            setup_id="test_2",
            setup_description="隐藏的宝藏",
            setup_episode=2,
        )
        assert not item.is_resolved
        assert item.payoff_episode is None


class TestEpisodeQualityResult:
    """Tests for EpisodeQualityResult dataclass."""

    def test_to_dict_minimal(self) -> None:
        """Test serialization with minimal data."""
        result = EpisodeQualityResult(passed=True)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["issues"] == []
        assert d["character_arcs"] == {}

    def test_to_dict_with_arcs(self) -> None:
        """Test serialization with character arcs."""
        result = EpisodeQualityResult(
            passed=True,
            character_arcs={
                "Alice": CharacterArc(
                    character_name="Alice",
                    episode_goals={1: "目标A", 2: "目标B"},
                )
            },
        )
        d = result.to_dict()
        assert "Alice" in d["character_arcs"]
        assert d["character_arcs"]["Alice"]["has_progression"] is True


class TestEpisodeQualityValidator:
    """Tests for EpisodeQualityValidator."""

    def test_validate_empty_episodes(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test validation with empty episodes."""
        result = validator.validate([])
        assert result.passed is True
        assert len(result.issues) == 0

    def test_track_character_arcs(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test character arc tracking."""
        episodes = [
            {
                "episode_number": 1,
                "characters": [
                    {"name": "Alice", "goal": "寻找真相", "status": "迷茫"},
                ],
            },
            {
                "episode_number": 2,
                "characters": [
                    {"name": "Alice", "goal": "逃离危险", "status": "觉醒"},
                ],
            },
        ]
        story_characters = [{"name": "Alice"}]

        arcs = validator._track_character_arcs(episodes, story_characters)

        assert "Alice" in arcs
        assert arcs["Alice"].episode_goals[1] == "寻找真相"
        assert arcs["Alice"].episode_goals[2] == "逃离危险"
        assert arcs["Alice"].has_progression()

    def test_track_character_arcs_from_continuity(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test arc tracking from continuity data."""
        episodes = [
            {
                "episode_number": 1,
                "continuity": {
                    "characters": {
                        "Bob": {"goal": "保护家人", "status": "紧张"},
                    }
                },
            },
        ]

        arcs = validator._track_character_arcs(episodes, [])

        assert "Bob" in arcs
        assert arcs["Bob"].episode_goals[1] == "保护家人"

    def test_check_arc_progression_stagnant(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test stagnant arc detection."""
        arcs = {
            "Alice": CharacterArc(
                character_name="Alice",
                episode_goals={1: "相同目标", 2: "相同目标", 3: "相同目标"},
            )
        }
        issues = validator._check_arc_progression(arcs)
        assert len(issues) == 1
        assert issues[0].issue_type == EpisodeQualityIssueType.CHARACTER_ARC_STAGNANT

    def test_analyze_subplot_balance(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test subplot balance analysis."""
        episodes = [
            {"summary": "主角核心任务的关键突破"},
            {"summary": "恋爱感情线发展，主角约会"},
            {"summary": "主线剧情推进，冲突矛盾升级"},
        ]
        ratios = validator._analyze_subplot_balance(episodes)
        assert "main" in ratios
        assert "romance" in ratios
        assert ratios["main"] > 0  # Should have main plot presence

    def test_check_subplot_balance_low_main(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test subplot imbalance detection when main plot is low."""
        ratios = {"main": 0.1, "romance": 0.5, "conflict": 0.2, "mystery": 0.1, "growth": 0.1}
        issues = validator._check_subplot_balance(ratios)
        assert len(issues) == 1
        assert issues[0].issue_type == EpisodeQualityIssueType.SUBPLOT_IMBALANCE
        assert "主线" in issues[0].message

    def test_check_subplot_balance_no_subplot(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test subplot imbalance detection when no subplots."""
        ratios = {"main": 0.9, "romance": 0.02, "conflict": 0.02, "mystery": 0.03, "growth": 0.03}
        issues = validator._check_subplot_balance(ratios)
        assert len(issues) == 1
        assert "支线" in issues[0].message

    def test_calculate_episode_tension(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test tension score calculation."""
        high_tension_ep = {
            "summary": "危机爆发，生死对决，角色陷入绝望的挣扎",
            "climax": "最终对抗，真相揭露",
        }
        low_tension_ep = {
            "summary": "平静的一天，角色在家休息",
        }

        high_score = validator._calculate_episode_tension(high_tension_ep)
        low_score = validator._calculate_episode_tension(low_tension_ep)

        assert high_score > low_score

    def test_analyze_tension_progression(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test tension progression analysis."""
        episodes = [
            {"summary": "平静开场"},
            {"summary": "冲突出现，紧张感升级"},
            {"summary": "危机爆发，高潮对决"},
        ]
        scores = validator._analyze_tension_progression(episodes)
        assert len(scores) == 3
        # Should generally increase
        assert scores[2] >= scores[0]

    def test_check_tension_plateau(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test tension plateau detection."""
        tension_scores = [0.5, 0.5, 0.5, 0.5]
        issues = validator._check_tension_progression(tension_scores)
        plateau_issues = [
            i for i in issues
            if i.issue_type == EpisodeQualityIssueType.TENSION_PLATEAU
        ]
        assert len(plateau_issues) > 0

    def test_check_tension_drop(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test tension drop detection."""
        tension_scores = [0.3, 0.7, 0.3, 0.6]  # Significant drop at position 2
        issues = validator._check_tension_progression(tension_scores)
        drop_issues = [
            i for i in issues
            if i.issue_type == EpisodeQualityIssueType.TENSION_DROP
        ]
        assert len(drop_issues) > 0

    def test_track_foreshadowing_from_ledger(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test foreshadowing tracking from continuity ledger."""
        episodes = [{"episode_number": 1}, {"episode_number": 2}]
        ledger = {
            "open_threads": ["神秘人物身份", "隐藏的宝藏位置"],
            "resolved_threads": ["第一个谜团"],
        }
        items = validator._track_foreshadowing(episodes, ledger)
        assert len(items) >= 3
        unresolved = [i for i in items if not i.is_resolved]
        resolved = [i for i in items if i.is_resolved]
        assert len(unresolved) >= 2
        assert len(resolved) >= 1

    def test_track_foreshadowing_from_content(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test foreshadowing detection from episode content."""
        episodes = [
            {"episode_number": 1, "summary": "埋下伏笔，暗示了神秘事件"},
            {"episode_number": 3, "summary": "真相揭示，原来是这样"},
        ]
        items = validator._track_foreshadowing(episodes, None)
        assert len(items) > 0

    def test_check_foreshadowing_too_many_unresolved(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test detection of too many unresolved setups."""
        items = [
            ForeshadowingItem(
                setup_id=f"test_{i}",
                setup_description=f"悬念 {i}",
                setup_episode=1,
                is_resolved=False,
            )
            for i in range(5)
        ]
        issues = validator._check_foreshadowing(items)
        chekhov_issues = [
            i for i in issues
            if i.issue_type == EpisodeQualityIssueType.UNFIRED_CHEKHOV
        ]
        assert len(chekhov_issues) > 0

    def test_check_foreshadowing_premature_payoff(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test detection of premature payoff."""
        items = [
            ForeshadowingItem(
                setup_id="test_1",
                setup_description="伏笔",
                setup_episode=2,
                payoff_episode=2,  # Same episode = premature
                is_resolved=True,
            )
        ]
        issues = validator._check_foreshadowing(items)
        premature_issues = [
            i for i in issues
            if i.issue_type == EpisodeQualityIssueType.PREMATURE_PAYOFF
        ]
        assert len(premature_issues) > 0

    def test_validate_full_episodes_good(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test full validation with good episodes."""
        episodes = [
            {
                "episode_number": 1,
                "summary": "主角发现危机，紧张气氛开始",
                "characters": [{"name": "Alice", "goal": "调查真相", "status": "好奇"}],
            },
            {
                "episode_number": 2,
                "summary": "核心冲突升级，主角陷入困境",
                "characters": [{"name": "Alice", "goal": "求生", "status": "恐惧"}],
            },
            {
                "episode_number": 3,
                "summary": "关键对决，高潮爆发，真相大白",
                "characters": [{"name": "Alice", "goal": "战胜敌人", "status": "决心"}],
            },
        ]
        story_characters = [{"name": "Alice"}]

        result = validator.validate(episodes, story_characters)

        assert result.passed is True
        assert "Alice" in result.character_arcs
        assert result.character_arcs["Alice"].has_progression()
        assert len(result.tension_scores) == 3

    def test_validate_full_episodes_with_issues(
        self, validator: EpisodeQualityValidator
    ) -> None:
        """Test full validation with problematic episodes."""
        episodes = [
            {
                "episode_number": 1,
                "summary": "平静的一天",
                "characters": [{"name": "Bob", "goal": "帮助", "status": "忠诚"}],
            },
            {
                "episode_number": 2,
                "summary": "又一个平静的一天",
                "characters": [{"name": "Bob", "goal": "帮助", "status": "忠诚"}],
            },
            {
                "episode_number": 3,
                "summary": "依然平静",
                "characters": [{"name": "Bob", "goal": "帮助", "status": "忠诚"}],
            },
        ]
        story_characters = [{"name": "Bob"}]

        result = validator.validate(episodes, story_characters)

        # Should have issues for stagnant arc and/or tension
        assert len(result.issues) > 0
