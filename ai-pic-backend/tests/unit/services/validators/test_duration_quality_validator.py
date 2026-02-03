"""Unit tests for DurationQualityValidator."""

from __future__ import annotations

import pytest

from app.services.validators.duration_quality_validator import (
    DurationQualityIssue,
    DurationQualityIssueType,
    DurationQualityResult,
    DurationQualitySeverity,
    DurationQualityValidator,
    RetryAnalysis,
    WordDistributionAnalysis,
)


@pytest.fixture
def validator() -> DurationQualityValidator:
    """Create a validator instance."""
    return DurationQualityValidator()


class TestDurationQualityIssue:
    """Tests for DurationQualityIssue dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        issue = DurationQualityIssue(
            issue_type=DurationQualityIssueType.WPS_PROVIDER_MISMATCH,
            severity=DurationQualitySeverity.WARNING,
            message="Test message",
            episode_index=1,
            scene_index=5,
            details={"key": "value"},
            suggestions=["Fix it"],
        )
        result = issue.to_dict()
        assert result["issue_type"] == "wps_provider_mismatch"
        assert result["severity"] == "warning"
        assert result["episode_index"] == 1
        assert result["scene_index"] == 5


class TestRetryAnalysis:
    """Tests for RetryAnalysis dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        analysis = RetryAnalysis(
            scene_index=0,
            attempt_count=3,
            duration_history=[28.0, 32.0, 30.5],
            is_converging=True,
            is_oscillating=False,
            convergence_rate=0.25,
        )
        d = analysis.to_dict()
        assert d["scene_index"] == 0
        assert d["attempt_count"] == 3
        assert d["is_converging"] is True
        assert d["convergence_rate"] == 0.25


class TestWordDistributionAnalysis:
    """Tests for WordDistributionAnalysis dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        analysis = WordDistributionAnalysis(
            total_words=500,
            scene_word_counts=[100, 150, 120, 130],
            mean_words=125.0,
            std_dev=18.7,
            coefficient_of_variation=0.15,
            front_half_ratio=0.5,
        )
        d = analysis.to_dict()
        assert d["total_words"] == 500
        assert d["scene_count"] == 4
        assert d["mean_words"] == 125.0


class TestDurationQualityResult:
    """Tests for DurationQualityResult dataclass."""

    def test_to_dict_minimal(self) -> None:
        """Test serialization with minimal data."""
        result = DurationQualityResult(passed=True)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["issues"] == []
        assert d["word_distribution"] is None

    def test_to_dict_full(self) -> None:
        """Test serialization with full data."""
        result = DurationQualityResult(
            passed=True,
            calibrated_wps=4.7,
            provider_used="volcengine",
        )
        d = result.to_dict()
        assert d["calibrated_wps"] == 4.7
        assert d["provider_used"] == "volcengine"


class TestDurationQualityValidator:
    """Tests for DurationQualityValidator."""

    # ============================================
    # WPS Calibration Tests
    # ============================================

    def test_get_calibrated_wps_default(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test getting default WPS."""
        wps, provider, issues = validator.get_calibrated_wps()
        assert wps == 4.7  # Default Chinese normal speed
        assert provider == "default"
        assert len(issues) == 0

    def test_get_calibrated_wps_volcengine(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test getting VolcEngine WPS."""
        wps, provider, issues = validator.get_calibrated_wps(
            provider="volcengine", language="zh", speed="normal"
        )
        assert wps == 4.5
        assert provider == "volcengine"
        assert len(issues) == 0

    def test_get_calibrated_wps_google(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test getting Google TTS WPS."""
        wps, provider, issues = validator.get_calibrated_wps(
            provider="google", language="en", speed="normal"
        )
        assert wps == 3.2
        assert provider == "google"

    def test_get_calibrated_wps_minimax(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test getting MiniMax TTS WPS."""
        wps, provider, issues = validator.get_calibrated_wps(
            provider="minimax", language="ja", speed="fast"
        )
        assert wps == 6.2
        assert provider == "minimax"

    def test_get_calibrated_wps_unknown_provider(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test unknown provider fallback."""
        wps, provider, issues = validator.get_calibrated_wps(
            provider="unknown_tts"
        )
        assert provider == "default"
        assert len(issues) == 1
        assert issues[0].issue_type == DurationQualityIssueType.WPS_PROVIDER_MISMATCH

    def test_get_calibrated_wps_unknown_language(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test unknown language fallback."""
        wps, provider, issues = validator.get_calibrated_wps(
            language="fr"  # French not supported
        )
        assert len(issues) == 1
        assert issues[0].issue_type == DurationQualityIssueType.WPS_LANGUAGE_UNSUPPORTED

    def test_get_calibrated_wps_all_speeds(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test all speed levels."""
        slow_wps, _, _ = validator.get_calibrated_wps(speed="slow")
        normal_wps, _, _ = validator.get_calibrated_wps(speed="normal")
        fast_wps, _, _ = validator.get_calibrated_wps(speed="fast")

        assert slow_wps < normal_wps < fast_wps

    # ============================================
    # Duration Estimation Tests
    # ============================================

    def test_estimate_duration_chinese(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test duration estimation for Chinese."""
        text = "这是一段测试文本"  # 8 characters
        duration_ms, result = validator.estimate_duration_with_provider(
            text, provider="default", language="zh"
        )
        # 8 chars / 4.7 WPS ≈ 1.7 seconds ≈ 1700ms
        assert 1500 < duration_ms < 2000
        assert result.passed is True

    def test_estimate_duration_english(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test duration estimation for English."""
        text = "This is a test sentence with several words"  # 8 words
        duration_ms, result = validator.estimate_duration_with_provider(
            text, provider="google", language="en"
        )
        # 8 words / 3.2 WPS ≈ 2.5 seconds ≈ 2500ms
        assert 2000 < duration_ms < 3000
        assert result.provider_used == "google"

    def test_estimate_duration_different_providers(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test that different providers give different estimates."""
        text = "这是测试文本"

        volc_ms, _ = validator.estimate_duration_with_provider(
            text, provider="volcengine", language="zh"
        )
        minimax_ms, _ = validator.estimate_duration_with_provider(
            text, provider="minimax", language="zh"
        )

        # MiniMax has higher WPS (5.0 vs 4.5), so should be shorter
        assert volc_ms > minimax_ms

    # ============================================
    # Word Distribution Tests
    # ============================================

    def test_analyze_word_distribution_basic(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test basic word distribution analysis."""
        scenes = [
            {"dialogues": [{"content": "这是第一场的对白"}]},  # 8 chars
            {"dialogues": [{"content": "第二场对白内容"}]},  # 7 chars
            {"dialogues": [{"content": "第三场"}]},  # 3 chars
            {"dialogues": [{"content": "第四场结尾对白"}]},  # 7 chars
        ]
        analysis = validator.analyze_word_distribution(scenes, "zh")

        assert analysis.total_words == 25
        assert len(analysis.scene_word_counts) == 4
        assert analysis.mean_words > 0
        assert analysis.std_dev >= 0

    def test_analyze_word_distribution_front_heavy(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test front-heavy distribution detection."""
        scenes = [
            {"dialogues": [{"content": "这是很长很长很长的第一场对白内容！"}]},  # 16 chars
            {"dialogues": [{"content": "第二场也很长很长很长的对白！"}]},  # 14 chars
            {"dialogues": [{"content": "短"}]},  # 1 char
            {"dialogues": [{"content": "短短"}]},  # 2 chars
        ]
        analysis = validator.analyze_word_distribution(scenes, "zh")

        assert analysis.is_front_heavy is True
        assert analysis.front_half_ratio > 0.65

    def test_analyze_word_distribution_back_heavy(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test back-heavy distribution detection."""
        scenes = [
            {"dialogues": [{"content": "短"}]},  # 1 char
            {"dialogues": [{"content": "短短"}]},  # 2 chars
            {"dialogues": [{"content": "这是很长很长很长的第三场对白内容！"}]},  # 16 chars
            {"dialogues": [{"content": "第四场也很长很长很长的对白！"}]},  # 14 chars
        ]
        analysis = validator.analyze_word_distribution(scenes, "zh")

        assert analysis.is_back_heavy is True
        assert analysis.front_half_ratio < 0.35

    def test_analyze_word_distribution_balanced(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test balanced distribution."""
        scenes = [
            {"dialogues": [{"content": "这是第一场对白"}]},
            {"dialogues": [{"content": "这是第二场对白"}]},
            {"dialogues": [{"content": "这是第三场对白"}]},
            {"dialogues": [{"content": "这是第四场对白"}]},
        ]
        analysis = validator.analyze_word_distribution(scenes, "zh")

        assert analysis.is_front_heavy is False
        assert analysis.is_back_heavy is False

    def test_check_word_distribution_issues(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test word distribution issue detection."""
        # Front-heavy scenes
        scenes = [
            {"dialogues": [{"content": "这是非常非常非常长的第一场对白内容！"}]},
            {"dialogues": [{"content": "第二场也是非常非常长的对白！"}]},
            {"dialogues": [{"content": "短"}]},
            {"dialogues": [{"content": "短"}]},
        ]
        analysis, issues = validator.check_word_distribution(scenes, "zh")

        front_heavy_issues = [
            i for i in issues
            if i.issue_type == DurationQualityIssueType.SCENE_DISTRIBUTION_FRONT_HEAVY
        ]
        assert len(front_heavy_issues) > 0

    def test_analyze_word_distribution_english(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test word distribution analysis for English."""
        scenes = [
            {"dialogues": [{"content": "This is scene one dialogue"}]},  # 5 words
            {"dialogues": [{"content": "Scene two has more words here"}]},  # 6 words
            {"dialogues": [{"content": "Short"}]},  # 1 word
            {"dialogues": [{"content": "Final scene dialogue"}]},  # 3 words
        ]
        analysis = validator.analyze_word_distribution(scenes, "en")

        assert analysis.total_words == 15
        assert len(analysis.scene_word_counts) == 4

    # ============================================
    # Retry Convergence Tests
    # ============================================

    def test_analyze_retry_convergence_no_retries(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test convergence analysis with no retries."""
        scene_budgets = [
            {"attempt_count": 1, "actual_duration_seconds": 30},
            {"attempt_count": 1, "actual_duration_seconds": 25},
        ]
        analyses = validator.analyze_retry_convergence(scene_budgets)

        assert len(analyses) == 0  # No retries = no analyses

    def test_analyze_retry_convergence_converging(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test detection of converging scene."""
        scene_budgets = [
            {
                "attempt_count": 3,
                "target_duration_seconds": 30,
                "duration_history": [25, 28, 29.5],  # Getting closer to 30
                "actual_duration_seconds": 29.5,
            }
        ]
        analyses = validator.analyze_retry_convergence(scene_budgets)

        assert len(analyses) == 1
        assert analyses[0].is_converging is True

    def test_analyze_retry_convergence_not_converging(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test detection of non-converging scene."""
        scene_budgets = [
            {
                "attempt_count": 3,
                "target_duration_seconds": 30,
                "duration_history": [25, 20, 18],  # Getting worse
                "actual_duration_seconds": 18,
            }
        ]
        analyses = validator.analyze_retry_convergence(scene_budgets)

        assert len(analyses) == 1
        assert analyses[0].is_converging is False

    def test_analyze_retry_convergence_oscillating(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test detection of oscillating scene."""
        scene_budgets = [
            {
                "attempt_count": 5,
                "target_duration_seconds": 30,
                "duration_history": [25, 35, 22, 38, 20],  # Bouncing up and down
                "actual_duration_seconds": 20,
            }
        ]
        analyses = validator.analyze_retry_convergence(scene_budgets)

        assert len(analyses) == 1
        assert analyses[0].is_oscillating is True

    def test_check_retry_convergence_issues(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test retry convergence issue detection."""
        scene_budgets = [
            {
                "attempt_count": 4,
                "target_duration_seconds": 30,
                "duration_history": [25, 20, 15, 10],  # Diverging
                "actual_duration_seconds": 10,
            }
        ]
        analyses, issues = validator.check_retry_convergence(scene_budgets)

        pathological_issues = [
            i for i in issues
            if i.issue_type == DurationQualityIssueType.SCENE_PATHOLOGICAL
        ]
        assert len(pathological_issues) > 0

    def test_check_high_retry_rate(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test high retry rate detection."""
        # All scenes have high retry counts
        scene_budgets = [
            {"attempt_count": 3, "actual_duration_seconds": 30},
            {"attempt_count": 3, "actual_duration_seconds": 25},
            {"attempt_count": 3, "actual_duration_seconds": 28},
        ]
        analyses, issues = validator.check_retry_convergence(scene_budgets)

        high_retry_issues = [
            i for i in issues
            if i.issue_type == DurationQualityIssueType.EPISODE_HIGH_RETRY_RATE
        ]
        assert len(high_retry_issues) > 0

    # ============================================
    # Episode Balance Tests
    # ============================================

    def test_analyze_episode_balance_single(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test balance analysis with single episode."""
        episodes = [{"actual_duration_seconds": 300}]
        metrics, issues = validator.analyze_episode_balance(episodes)

        assert metrics["episode_count"] == 1
        assert metrics["balanced"] is True
        assert len(issues) == 0

    def test_analyze_episode_balance_balanced(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test detection of balanced episodes."""
        episodes = [
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 305},
            {"actual_duration_seconds": 295},
            {"actual_duration_seconds": 302},
        ]
        metrics, issues = validator.analyze_episode_balance(episodes)

        assert metrics["balanced"] is True
        assert metrics["coefficient_of_variation"] < 0.15

    def test_analyze_episode_balance_imbalanced(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test detection of imbalanced episodes."""
        episodes = [
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 200},  # Too short
            {"actual_duration_seconds": 400},  # Too long
            {"actual_duration_seconds": 300},
        ]
        metrics, issues = validator.analyze_episode_balance(episodes)

        assert metrics["balanced"] is False
        imbalance_issues = [
            i for i in issues
            if i.issue_type == DurationQualityIssueType.EPISODE_DURATION_IMBALANCE
        ]
        assert len(imbalance_issues) > 0

    def test_analyze_episode_balance_outliers(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test outlier episode detection."""
        # Need more data points to get z-score > 2.0 for outlier detection
        # With small samples, the outlier itself affects mean/std too much
        episodes = [
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 1200},  # Extreme outlier (z-score ~2.04)
        ]
        metrics, issues = validator.analyze_episode_balance(episodes)

        outlier_issues = [
            i for i in issues
            if i.issue_type == DurationQualityIssueType.EPISODE_DURATION_OUTLIER
        ]
        assert len(outlier_issues) > 0
        assert 5 in metrics["outlier_episodes"]  # Episode index 5 is outlier

    # ============================================
    # Full Validation Tests
    # ============================================

    def test_validate_empty(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test validation with empty data."""
        result = validator.validate([])
        assert result.passed is True
        assert result.calibrated_wps is not None

    def test_validate_full(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test full validation."""
        scenes = [
            {"dialogues": [{"content": "场景一对白"}]},
            {"dialogues": [{"content": "场景二对白"}]},
            {"dialogues": [{"content": "场景三对白"}]},
        ]
        scene_budgets = [
            {"attempt_count": 1, "actual_duration_seconds": 10},
            {"attempt_count": 2, "actual_duration_seconds": 12},
            {"attempt_count": 1, "actual_duration_seconds": 11},
        ]
        episodes = [
            {"actual_duration_seconds": 300},
            {"actual_duration_seconds": 310},
        ]

        result = validator.validate(
            scenes=scenes,
            scene_budgets=scene_budgets,
            episodes=episodes,
            provider="volcengine",
            language="zh",
        )

        assert result.calibrated_wps == 4.5
        assert result.provider_used == "volcengine"
        assert result.word_distribution is not None
        assert result.episode_balance is not None

    def test_validate_with_issues(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test validation detects issues."""
        # Front-heavy distribution
        scenes = [
            {"dialogues": [{"content": "这是非常非常长的第一场对白内容！！！"}]},
            {"dialogues": [{"content": "短"}]},
        ]
        # Non-converging scene
        scene_budgets = [
            {
                "attempt_count": 4,
                "target_duration_seconds": 30,
                "duration_history": [25, 20, 15, 10],
                "actual_duration_seconds": 10,
            },
            {"attempt_count": 1, "actual_duration_seconds": 5},
        ]

        result = validator.validate(
            scenes=scenes,
            scene_budgets=scene_budgets,
        )

        assert result.passed is False  # Should have ERROR level issues
        assert len(result.issues) > 0

    def test_validate_to_dict(
        self, validator: DurationQualityValidator
    ) -> None:
        """Test result serialization."""
        scenes = [{"dialogues": [{"content": "测试"}]}]
        result = validator.validate(scenes=scenes)
        d = result.to_dict()

        assert "passed" in d
        assert "issues" in d
        assert "calibrated_wps" in d
        assert "provider_used" in d
