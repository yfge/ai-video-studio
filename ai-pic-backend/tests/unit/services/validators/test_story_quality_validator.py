"""Unit tests for StoryQualityValidator."""

from __future__ import annotations

import pytest

from app.services.validators.story_quality_validator import (
    PacingAnalysis,
    StoryQualityIssue,
    StoryQualityIssueType,
    StoryQualityResult,
    StoryQualitySeverity,
    StoryQualityValidator,
    ThreeActAnalysis,
)


@pytest.fixture
def validator() -> StoryQualityValidator:
    """Create a validator instance."""
    return StoryQualityValidator()


class TestStoryQualityIssue:
    """Tests for StoryQualityIssue dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        issue = StoryQualityIssue(
            issue_type=StoryQualityIssueType.STRUCTURE_IMBALANCE,
            severity=StoryQualitySeverity.WARNING,
            message="Test message",
            details={"key": "value"},
            suggestions=["Fix it"],
            location="act_1",
        )
        result = issue.to_dict()
        assert result["issue_type"] == "structure_imbalance"
        assert result["severity"] == "warning"
        assert result["message"] == "Test message"
        assert result["details"]["key"] == "value"
        assert result["suggestions"] == ["Fix it"]
        assert result["location"] == "act_1"


class TestStoryQualityResult:
    """Tests for StoryQualityResult dataclass."""

    def test_to_dict_minimal(self) -> None:
        """Test serialization with minimal data."""
        result = StoryQualityResult(passed=True)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["issues"] == []
        assert d["three_act_analysis"] is None

    def test_to_dict_full(self) -> None:
        """Test serialization with full data."""
        result = StoryQualityResult(
            passed=True,
            three_act_analysis=ThreeActAnalysis(
                act1_ratio=0.25,
                act2_ratio=0.50,
                act3_ratio=0.25,
                is_balanced=True,
            ),
            pacing_analysis=PacingAnalysis(
                opening_score=0.8,
                buildup_score=0.7,
                climax_score=0.9,
                resolution_score=0.8,
                overall_score=0.8,
            ),
            hook_score=0.75,
        )
        d = result.to_dict()
        assert d["three_act_analysis"]["act1_ratio"] == 0.25
        assert d["pacing_analysis"]["climax_score"] == 0.9
        assert d["hook_score"] == 0.75


class TestStoryQualityValidator:
    """Tests for StoryQualityValidator."""

    def test_analyze_three_act_structure_balanced(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test three-act analysis with balanced structure."""
        story = {
            "episodes": [{"id": i} for i in range(8)],  # 8 episodes
            "act_markers": {"act1_end": 2, "act2_end": 6},  # 2, 4, 2 episodes
        }
        analysis = validator._analyze_three_act_structure(story)
        assert analysis.is_balanced
        assert 0.20 <= analysis.act1_ratio <= 0.30
        assert 0.45 <= analysis.act2_ratio <= 0.55
        assert 0.20 <= analysis.act3_ratio <= 0.30

    def test_analyze_three_act_structure_imbalanced(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test three-act analysis with imbalanced structure."""
        story = {
            "episodes": [{"id": i} for i in range(10)],
            "act_markers": {"act1_end": 1, "act2_end": 9},  # 1, 8, 1 episodes
        }
        analysis = validator._analyze_three_act_structure(story)
        assert not analysis.is_balanced
        assert "第二幕" in analysis.imbalance_details

    def test_analyze_pacing_good(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test pacing analysis with good pacing."""
        story = {
            "summary": "突然发现一个神秘的危机正在逼近",
            "episodes": [
                {"summary": "紧张的冲突不断升级"},
                {"summary": "压力越来越大，危机四伏"},
                {"summary": "高潮对决，真相揭示"},
                {"summary": "结局圆满，一切解决"},
            ],
        }
        analysis = validator._analyze_pacing(story)
        assert analysis.overall_score > 0.5

    def test_evaluate_hook_quality_strong(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test hook evaluation with strong hook."""
        story = {
            "opening": "突然，一声巨响震惊了整个城市，神秘的危机降临",
            "episodes": [{"summary": "意外发现了惊人的秘密"}],
        }
        score = validator._evaluate_hook_quality(story, None)
        assert score > 0.5

    def test_evaluate_hook_quality_weak(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test hook evaluation with weak hook."""
        story = {
            "opening": "这是一个平静的日常生活故事",
            "episodes": [{"summary": "普通的一天开始了"}],
        }
        score = validator._evaluate_hook_quality(story, None)
        assert score < 0.7  # Weak hooks should score lower

    def test_evaluate_cliffhanger_quality_strong(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test cliffhanger evaluation with strong cliffhangers."""
        episodes = [
            {"ending": "但是，突然传来了一声枪响，悬念升级"},
            {"ending": "然而，谁知道真相竟然如此令人震惊"},
            {"ending": "最终的结局"},  # Last episode doesn't need cliffhanger
        ]
        score = validator._evaluate_cliffhanger_quality(episodes)
        assert score > 0.5

    def test_evaluate_cliffhanger_quality_weak(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test cliffhanger evaluation with weak cliffhangers."""
        episodes = [
            {"ending": "一切都解决了，大家开心地结束了一天"},
            {"ending": "问题完成了，日子平静地过去"},
            {"ending": "故事结束"},
        ]
        score = validator._evaluate_cliffhanger_quality(episodes)
        assert score < 0.7

    def test_check_worldbuilding_consistency_good(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test worldbuilding check with consistent setting."""
        story = {
            "setting": {
                "time_period": "现代都市",
                "technology": ["智能手机", "互联网"],
            },
        }
        score, issues = validator._check_worldbuilding_consistency(story)
        assert score == 1.0
        assert len(issues) == 0

    def test_check_worldbuilding_consistency_bad(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test worldbuilding check with inconsistent setting."""
        story = {
            "setting": {
                "time_period": "古代中国",
                "technology": ["手机", "电脑"],
            },
        }
        score, issues = validator._check_worldbuilding_consistency(story)
        assert score < 1.0
        assert len(issues) > 0
        assert issues[0].issue_type == StoryQualityIssueType.WORLDBUILDING_INCONSISTENCY

    def test_check_content_restrictions_pass(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test content check with clean content."""
        story = {
            "summary": "一个温暖的家庭故事",
            "episodes": [{"summary": "关于友情和成长"}],
        }
        passed, issues = validator._check_content_restrictions(story, None)
        assert passed is True
        assert len(issues) == 0

    def test_check_content_restrictions_fail(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test content check with prohibited content."""
        story = {
            "summary": "详细描述酷刑的过程",
        }
        passed, issues = validator._check_content_restrictions(story, None)
        assert passed is False
        assert len(issues) > 0
        assert issues[0].issue_type == StoryQualityIssueType.PROHIBITED_CONTENT

    def test_check_content_restrictions_custom(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test content check with custom restrictions."""
        story = {
            "summary": "一个关于魔法的故事",
        }
        passed, issues = validator._check_content_restrictions(
            story, ["魔法", "巫术"]
        )
        assert len(issues) > 0

    def test_validate_full_story_good(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test full validation with good story."""
        story = {
            "summary": "突然发现神秘危机，紧张冲突不断",
            "episodes": [
                {"summary": "神秘事件发生，冲突开始", "ending": "但是谁知道..."},
                {"summary": "紧张对抗升级，压力加大", "ending": "然而转折出现..."},
                {"summary": "高潮对决，真相揭示", "ending": "悬念继续..."},
                {"summary": "最终解决，结局收束"},
            ],
            "setting": {"time_period": "现代"},
        }
        result = validator.validate(story)
        assert result.passed is True
        assert result.three_act_analysis is not None
        assert result.pacing_analysis is not None

    def test_validate_full_story_issues(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test full validation with story that has issues."""
        story = {
            "summary": "普通的日常生活故事",
            "episodes": [{"summary": "平静的一天", "ending": "结束了"}],
            "setting": {
                "time_period": "古代",
                "technology": ["手机"],
            },
        }
        result = validator.validate(story)
        # Should have issues but not necessarily fail
        assert len(result.issues) > 0

    def test_score_text_engagement(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test text engagement scoring."""
        high_engagement = "突然发现神秘的危机，震惊了所有人"
        low_engagement = "普通的日常生活"

        high_score = validator._score_text_engagement(high_engagement)
        low_score = validator._score_text_engagement(low_engagement)

        assert high_score > low_score

    def test_count_keyword_density(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test keyword density counting."""
        text = "紧张的冲突不断升级，压力越来越大"
        keywords = ["紧张", "冲突", "压力", "升级"]
        density = validator._count_keyword_density(text, keywords)
        assert density > 0

    def test_get_pacing_suggestions(
        self, validator: StoryQualityValidator
    ) -> None:
        """Test pacing suggestion generation."""
        poor_pacing = PacingAnalysis(
            opening_score=0.3,
            buildup_score=0.3,
            climax_score=0.3,
            resolution_score=0.3,
            overall_score=0.3,
        )
        suggestions = validator._get_pacing_suggestions(poor_pacing)
        assert len(suggestions) == 4  # All areas need improvement

        good_pacing = PacingAnalysis(
            opening_score=0.8,
            buildup_score=0.8,
            climax_score=0.8,
            resolution_score=0.8,
            overall_score=0.8,
        )
        suggestions = validator._get_pacing_suggestions(good_pacing)
        assert len(suggestions) == 0


class TestThreeActAnalysis:
    """Tests for ThreeActAnalysis dataclass."""

    def test_balanced(self) -> None:
        """Test balanced analysis."""
        analysis = ThreeActAnalysis(
            act1_ratio=0.25,
            act2_ratio=0.50,
            act3_ratio=0.25,
            is_balanced=True,
        )
        assert analysis.is_balanced
        assert analysis.imbalance_details == ""

    def test_imbalanced(self) -> None:
        """Test imbalanced analysis."""
        analysis = ThreeActAnalysis(
            act1_ratio=0.10,
            act2_ratio=0.80,
            act3_ratio=0.10,
            is_balanced=False,
            imbalance_details="第一幕过短",
        )
        assert not analysis.is_balanced
        assert "过短" in analysis.imbalance_details


class TestPacingAnalysis:
    """Tests for PacingAnalysis dataclass."""

    def test_scores(self) -> None:
        """Test pacing scores."""
        analysis = PacingAnalysis(
            opening_score=0.8,
            buildup_score=0.7,
            climax_score=0.9,
            resolution_score=0.75,
            overall_score=0.79,
        )
        assert analysis.opening_score == 0.8
        assert analysis.climax_score == 0.9
        assert analysis.overall_score == 0.79
