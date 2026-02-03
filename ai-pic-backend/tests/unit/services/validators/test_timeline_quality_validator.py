"""Unit tests for TimelineQualityValidator."""

from __future__ import annotations

import pytest

from app.services.validators.timeline_quality_validator import (
    EmotionCurveAnalysis,
    EmotionPoint,
    TimelineQualityIssue,
    TimelineQualityIssueType,
    TimelineQualityResult,
    TimelineQualitySeverity,
    TimelineQualityValidator,
)


@pytest.fixture
def validator() -> TimelineQualityValidator:
    """Create a validator instance."""
    return TimelineQualityValidator()


class TestTimelineQualityIssue:
    """Tests for TimelineQualityIssue dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        issue = TimelineQualityIssue(
            issue_type=TimelineQualityIssueType.RHYTHM_TOO_FAST,
            severity=TimelineQualitySeverity.WARNING,
            message="Test message",
            beat_index=5,
            time_range_ms=(1000, 2000),
            details={"key": "value"},
            suggestions=["Fix it"],
        )
        result = issue.to_dict()
        assert result["issue_type"] == "rhythm_too_fast"
        assert result["severity"] == "warning"
        assert result["beat_index"] == 5
        assert result["time_range_ms"] == (1000, 2000)


class TestEmotionCurveAnalysis:
    """Tests for EmotionCurveAnalysis dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        analysis = EmotionCurveAnalysis(
            points=[
                EmotionPoint(time_ms=0, emotion_value=0.0),
                EmotionPoint(time_ms=1000, emotion_value=0.5),
                EmotionPoint(time_ms=2000, emotion_value=1.0),
            ],
            average_intensity=0.5,
            variance=0.25,
            peaks=[2],
            valleys=[0],
            has_arc=True,
        )
        d = analysis.to_dict()
        assert d["point_count"] == 3
        assert d["average_intensity"] == 0.5
        assert d["has_arc"] is True


class TestTimelineQualityResult:
    """Tests for TimelineQualityResult dataclass."""

    def test_to_dict_minimal(self) -> None:
        """Test serialization with minimal data."""
        result = TimelineQualityResult(passed=True)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["issues"] == []
        assert d["emotion_curve"] is None

    def test_to_dict_full(self) -> None:
        """Test serialization with full data."""
        result = TimelineQualityResult(
            passed=True,
            average_wps=4.5,
            detected_language="zh",
            total_duration_ms=60000,
            pause_ratio=0.1,
        )
        d = result.to_dict()
        assert d["average_wps"] == 4.5
        assert d["detected_language"] == "zh"


class TestTimelineQualityValidator:
    """Tests for TimelineQualityValidator."""

    def test_validate_empty_beats(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test validation with empty beats."""
        result = validator.validate([])
        assert result.passed is True
        assert len(result.issues) == 0

    def test_calculate_total_duration(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test total duration calculation."""
        beats = [
            {"start_ms": 0, "end_ms": 1000},
            {"start_ms": 1000, "end_ms": 3000},
            {"start_ms": 3000, "end_ms": 5000},
        ]
        duration = validator._calculate_total_duration(beats)
        assert duration == 5000

    def test_detect_language_chinese(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test Chinese language detection."""
        beats = [
            {"text": "这是一段中文对白"},
            {"text": "测试语言检测功能"},
        ]
        lang = validator._detect_language(beats)
        assert lang == "zh"

    def test_detect_language_english(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test English language detection."""
        beats = [
            {"text": "This is English dialogue"},
            {"text": "Testing language detection"},
        ]
        lang = validator._detect_language(beats)
        assert lang == "en"

    def test_detect_language_japanese(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test Japanese language detection."""
        beats = [
            {"text": "これは日本語のテストです"},
            {"text": "言語検出をテストしています"},
        ]
        lang = validator._detect_language(beats)
        assert lang == "ja"

    def test_calculate_average_wps(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test WPS calculation."""
        beats = [
            {
                "beat_type": "dialogue",
                "text": "这是十个字的测试",  # 8 chars
                "start_ms": 0,
                "end_ms": 2000,  # 2 seconds
            },
        ]
        wps = validator._calculate_average_wps(beats, "zh")
        assert wps == 4.0  # 8 chars / 2 sec = 4 chars/sec

    def test_check_rhythm_normal(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test rhythm check with normal speed."""
        issues = validator._check_rhythm(4.5, "zh")
        assert len(issues) == 0  # 4.5 is within normal range

    def test_check_rhythm_too_slow(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test rhythm check with slow speed."""
        issues = validator._check_rhythm(2.0, "zh")
        assert len(issues) > 0
        assert issues[0].issue_type == TimelineQualityIssueType.RHYTHM_TOO_SLOW

    def test_check_rhythm_too_fast(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test rhythm check with fast speed."""
        issues = validator._check_rhythm(8.0, "zh")
        assert len(issues) > 0
        assert issues[0].issue_type == TimelineQualityIssueType.RHYTHM_TOO_FAST

    def test_calculate_emotion_intensity_high(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test emotion intensity for high intensity content."""
        intensity = validator._calculate_emotion_intensity(
            "震惊！危机爆发了！", "愤怒"
        )
        assert intensity > 0.3

    def test_calculate_emotion_intensity_low(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test emotion intensity for low intensity content."""
        intensity = validator._calculate_emotion_intensity(
            "平静的一天", "冷静"
        )
        assert intensity < 0.3

    def test_analyze_emotion_curve(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test emotion curve analysis."""
        beats = [
            {"start_ms": 0, "text": "平静的开始", "emotion": "平静"},
            {"start_ms": 1000, "text": "紧张起来", "emotion": "紧张"},
            {"start_ms": 2000, "text": "高潮爆发！危机！", "emotion": "愤怒"},
            {"start_ms": 3000, "text": "平静结束", "emotion": "平静"},
        ]
        analysis = validator._analyze_emotion_curve(beats)
        assert len(analysis.points) == 4
        assert analysis.variance > 0

    def test_check_emotion_curve_flat(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test emotion curve check with flat curve."""
        analysis = EmotionCurveAnalysis(
            points=[
                EmotionPoint(time_ms=0, emotion_value=0.2),
                EmotionPoint(time_ms=1000, emotion_value=0.2),
                EmotionPoint(time_ms=2000, emotion_value=0.2),
            ],
            variance=0.0,
        )
        issues = validator._check_emotion_curve(analysis)
        flat_issues = [
            i for i in issues
            if i.issue_type == TimelineQualityIssueType.EMOTION_CURVE_FLAT
        ]
        assert len(flat_issues) > 0

    def test_check_emotion_curve_choppy(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test emotion curve check with choppy curve."""
        analysis = EmotionCurveAnalysis(
            points=[EmotionPoint(time_ms=i * 100, emotion_value=0.5) for i in range(10)],
            peaks=[1, 3, 5, 7, 9],  # Too many peaks
            variance=0.5,
        )
        issues = validator._check_emotion_curve(analysis)
        choppy_issues = [
            i for i in issues
            if i.issue_type == TimelineQualityIssueType.EMOTION_CURVE_CHOPPY
        ]
        assert len(choppy_issues) > 0

    def test_calculate_pause_ratio(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test pause ratio calculation."""
        beats = [
            {"beat_type": "dialogue", "start_ms": 0, "end_ms": 1000},
            {"beat_type": "pause", "start_ms": 1000, "end_ms": 1500},
            {"beat_type": "dialogue", "start_ms": 1500, "end_ms": 2500},
        ]
        ratio = validator._calculate_pause_ratio(beats)
        assert ratio == 0.2  # 500ms pause / 2500ms total

    def test_check_dramatic_pauses_missing(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test missing dramatic pause detection."""
        beats = [
            {"beat_type": "dialogue", "text": "这是一个笑点哈哈", "start_ms": 0, "end_ms": 1000},
            {"beat_type": "dialogue", "text": "继续说", "start_ms": 1000, "end_ms": 2000},
        ]
        issues = validator._check_dramatic_pauses(beats)
        missing_issues = [
            i for i in issues
            if i.issue_type == TimelineQualityIssueType.MISSING_DRAMATIC_PAUSE
        ]
        assert len(missing_issues) > 0

    def test_check_dramatic_pauses_present(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test when dramatic pause is present."""
        beats = [
            {"beat_type": "dialogue", "text": "这是一个笑点哈哈", "start_ms": 0, "end_ms": 1000},
            {"beat_type": "pause", "start_ms": 1000, "end_ms": 1800},  # 800ms pause
            {"beat_type": "dialogue", "text": "继续说", "start_ms": 1800, "end_ms": 2800},
        ]
        issues = validator._check_dramatic_pauses(beats)
        missing_issues = [
            i for i in issues
            if i.issue_type == TimelineQualityIssueType.MISSING_DRAMATIC_PAUSE
        ]
        assert len(missing_issues) == 0

    def test_check_excessive_pause(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test excessive pause detection."""
        beats = [
            {"beat_type": "dialogue", "text": "说话", "start_ms": 0, "end_ms": 1000},
            {"beat_type": "pause", "start_ms": 1000, "end_ms": 5000},  # 4000ms pause
            {"beat_type": "dialogue", "text": "继续", "start_ms": 5000, "end_ms": 6000},
        ]
        issues = validator._check_dramatic_pauses(beats)
        excessive_issues = [
            i for i in issues
            if i.issue_type == TimelineQualityIssueType.EXCESSIVE_PAUSE
        ]
        assert len(excessive_issues) > 0

    def test_check_duration_drift(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test duration drift detection."""
        # 50% drift (150000 vs 100000)
        issues = validator._check_duration_drift(150000, 100000)
        assert len(issues) > 0
        assert issues[0].issue_type == TimelineQualityIssueType.DURATION_ESTIMATE_DRIFT

    def test_check_duration_drift_acceptable(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test acceptable duration drift."""
        # 10% drift (110000 vs 100000)
        issues = validator._check_duration_drift(110000, 100000)
        assert len(issues) == 0

    def test_estimate_duration_syllable_level_chinese(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test syllable-level duration estimation for Chinese."""
        text = "这是一段测试文本，用于验证时长估算。"
        duration = validator.estimate_duration_syllable_level(text, "zh", "normal")
        # ~16 chars + 2 punctuation pauses
        assert duration > 3000  # Should be around 3-4 seconds

    def test_estimate_duration_syllable_level_english(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test syllable-level duration estimation for English."""
        text = "This is a test sentence for duration estimation."
        duration = validator.estimate_duration_syllable_level(text, "en", "normal")
        assert duration > 0

    def test_validate_full_timeline_good(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test full validation with good timeline."""
        beats = [
            {
                "beat_type": "dialogue",
                "text": "平静的开场对白",
                "emotion": "平静",
                "start_ms": 0,
                "end_ms": 2000,
            },
            {
                "beat_type": "dialogue",
                "text": "紧张起来了！",
                "emotion": "紧张",
                "start_ms": 2000,
                "end_ms": 4000,
            },
            {
                "beat_type": "pause",
                "start_ms": 4000,
                "end_ms": 4500,
            },
            {
                "beat_type": "dialogue",
                "text": "高潮爆发！危机！",
                "emotion": "愤怒",
                "start_ms": 4500,
                "end_ms": 6500,
            },
        ]

        result = validator.validate(beats, "zh")

        assert result.passed is True
        assert result.detected_language == "zh"
        assert result.total_duration_ms == 6500
        assert result.emotion_curve is not None

    def test_validate_full_timeline_with_issues(
        self, validator: TimelineQualityValidator
    ) -> None:
        """Test full validation with problematic timeline."""
        beats = [
            {
                "beat_type": "dialogue",
                "text": "短",  # Very short
                "emotion": "平静",
                "start_ms": 0,
                "end_ms": 100,  # Very fast
            },
            {
                "beat_type": "pause",
                "start_ms": 100,
                "end_ms": 5000,  # Excessive pause
            },
        ]

        result = validator.validate(beats, "zh", target_duration_ms=60000)

        # Should have issues for:
        # - Rhythm too fast
        # - Excessive pause
        # - Duration drift
        assert len(result.issues) > 0
