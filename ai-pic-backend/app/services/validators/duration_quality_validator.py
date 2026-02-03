"""
Duration Quality Validator

Provides advanced duration validation capabilities including:
- Multi-TTS provider WPS calibration (VolcEngine/Google/MiniMax)
- Cross-episode duration balance checking
- Scene word count distribution analysis
- Retry convergence analysis for pathological scene detection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import statistics


class DurationQualityIssueType(Enum):
    """Types of duration quality issues."""

    # WPS calibration issues
    WPS_PROVIDER_MISMATCH = "wps_provider_mismatch"
    WPS_LANGUAGE_UNSUPPORTED = "wps_language_unsupported"

    # Cross-episode balance issues
    EPISODE_DURATION_OUTLIER = "episode_duration_outlier"
    EPISODE_DURATION_IMBALANCE = "episode_duration_imbalance"

    # Scene distribution issues
    SCENE_DISTRIBUTION_FRONT_HEAVY = "scene_distribution_front_heavy"
    SCENE_DISTRIBUTION_BACK_HEAVY = "scene_distribution_back_heavy"
    SCENE_WORD_COUNT_OUTLIER = "scene_word_count_outlier"

    # Retry convergence issues
    SCENE_PATHOLOGICAL = "scene_pathological"
    SCENE_RETRY_OSCILLATION = "scene_retry_oscillation"
    EPISODE_HIGH_RETRY_RATE = "episode_high_retry_rate"


class DurationQualitySeverity(Enum):
    """Severity levels for duration quality issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DurationQualityIssue:
    """Represents a duration quality issue."""

    issue_type: DurationQualityIssueType
    severity: DurationQualitySeverity
    message: str
    episode_index: Optional[int] = None
    scene_index: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "episode_index": self.episode_index,
            "scene_index": self.scene_index,
            "details": self.details,
            "suggestions": self.suggestions,
        }


@dataclass
class RetryAnalysis:
    """Retry convergence analysis results."""

    scene_index: int
    attempt_count: int
    duration_history: List[float] = field(default_factory=list)
    is_converging: bool = True
    is_oscillating: bool = False
    convergence_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scene_index": self.scene_index,
            "attempt_count": self.attempt_count,
            "duration_history": self.duration_history,
            "is_converging": self.is_converging,
            "is_oscillating": self.is_oscillating,
            "convergence_rate": self.convergence_rate,
        }


@dataclass
class WordDistributionAnalysis:
    """Word count distribution analysis results."""

    total_words: int = 0
    scene_word_counts: List[int] = field(default_factory=list)
    mean_words: float = 0.0
    std_dev: float = 0.0
    coefficient_of_variation: float = 0.0
    front_half_ratio: float = 0.5
    is_front_heavy: bool = False
    is_back_heavy: bool = False
    outlier_scenes: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_words": self.total_words,
            "scene_count": len(self.scene_word_counts),
            "mean_words": round(self.mean_words, 2),
            "std_dev": round(self.std_dev, 2),
            "coefficient_of_variation": round(self.coefficient_of_variation, 4),
            "front_half_ratio": round(self.front_half_ratio, 4),
            "is_front_heavy": self.is_front_heavy,
            "is_back_heavy": self.is_back_heavy,
            "outlier_scenes": self.outlier_scenes,
        }


@dataclass
class DurationQualityResult:
    """Result of duration quality validation."""

    passed: bool = True
    issues: List[DurationQualityIssue] = field(default_factory=list)
    word_distribution: Optional[WordDistributionAnalysis] = None
    retry_analyses: List[RetryAnalysis] = field(default_factory=list)
    episode_balance: Optional[Dict[str, Any]] = None
    calibrated_wps: Optional[float] = None
    provider_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
            "word_distribution": (
                self.word_distribution.to_dict()
                if self.word_distribution
                else None
            ),
            "retry_analyses": [r.to_dict() for r in self.retry_analyses],
            "episode_balance": self.episode_balance,
            "calibrated_wps": self.calibrated_wps,
            "provider_used": self.provider_used,
        }


class DurationQualityValidator:
    """
    Duration quality validator with multi-TTS provider calibration.

    Features:
    - Multi-TTS provider WPS calibration
    - Cross-episode duration balance checking
    - Scene word count distribution analysis
    - Retry convergence analysis
    """

    # TTS Provider-specific WPS (Words Per Second) calibration
    # Based on actual TTS output measurements
    WPS_BY_PROVIDER: Dict[str, Dict[str, Dict[str, float]]] = {
        # VolcEngine TTS (火山引擎)
        "volcengine": {
            "zh": {"slow": 3.5, "normal": 4.5, "fast": 5.5},
            "en": {"slow": 2.3, "normal": 3.0, "fast": 3.8},
            "ja": {"slow": 3.8, "normal": 4.8, "fast": 5.8},
            "ko": {"slow": 3.3, "normal": 4.3, "fast": 5.3},
        },
        # Google Cloud TTS
        "google": {
            "zh": {"slow": 3.6, "normal": 4.6, "fast": 5.6},
            "en": {"slow": 2.4, "normal": 3.2, "fast": 4.0},
            "ja": {"slow": 3.9, "normal": 4.9, "fast": 5.9},
            "ko": {"slow": 3.4, "normal": 4.4, "fast": 5.4},
        },
        # MiniMax TTS
        "minimax": {
            "zh": {"slow": 4.0, "normal": 5.0, "fast": 6.0},
            "en": {"slow": 2.6, "normal": 3.4, "fast": 4.2},
            "ja": {"slow": 4.2, "normal": 5.2, "fast": 6.2},
            "ko": {"slow": 3.6, "normal": 4.6, "fast": 5.6},
        },
        # Default calibration (matches current system constants)
        "default": {
            "zh": {"slow": 3.8, "normal": 4.7, "fast": 5.6},
            "en": {"slow": 2.5, "normal": 3.2, "fast": 4.0},
            "ja": {"slow": 4.0, "normal": 5.0, "fast": 6.0},
            "ko": {"slow": 3.5, "normal": 4.5, "fast": 5.5},
        },
    }

    # Episode balance thresholds
    EPISODE_BALANCE_CV_THRESHOLD = 0.15  # Coefficient of variation
    EPISODE_OUTLIER_ZSCORE = 2.0  # Z-score for outlier detection

    # Scene distribution thresholds
    SCENE_FRONT_HEAVY_THRESHOLD = 0.65  # >65% in first half is front-heavy
    SCENE_BACK_HEAVY_THRESHOLD = 0.35  # <35% in first half is back-heavy
    SCENE_OUTLIER_ZSCORE = 2.0  # Z-score for outlier scenes

    # Retry convergence thresholds
    MAX_HEALTHY_RETRIES = 3
    OSCILLATION_THRESHOLD = 3  # >3 direction changes = oscillating
    CONVERGENCE_RATE_THRESHOLD = 0.1  # <10% improvement = not converging

    def __init__(
        self,
        default_provider: str = "default",
        default_language: str = "zh",
        default_speed: str = "normal",
    ):
        """
        Initialize the validator.

        Args:
            default_provider: Default TTS provider
            default_language: Default language code
            default_speed: Default speech speed
        """
        self.default_provider = default_provider
        self.default_language = default_language
        self.default_speed = default_speed

    def get_calibrated_wps(
        self,
        provider: Optional[str] = None,
        language: Optional[str] = None,
        speed: Optional[str] = None,
    ) -> Tuple[float, str, List[DurationQualityIssue]]:
        """
        Get calibrated WPS for a specific provider/language/speed combination.

        Args:
            provider: TTS provider name (volcengine/google/minimax/default)
            language: Language code (zh/en/ja/ko)
            speed: Speech speed (slow/normal/fast)

        Returns:
            Tuple of (wps_value, actual_provider_used, issues)
        """
        provider = provider or self.default_provider
        language = language or self.default_language
        speed = speed or self.default_speed
        issues: List[DurationQualityIssue] = []

        # Normalize provider name
        provider_lower = provider.lower()
        if provider_lower not in self.WPS_BY_PROVIDER:
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.WPS_PROVIDER_MISMATCH,
                    severity=DurationQualitySeverity.INFO,
                    message=f"Unknown provider '{provider}', using default",
                    details={"requested_provider": provider},
                )
            )
            provider_lower = "default"

        provider_config = self.WPS_BY_PROVIDER[provider_lower]

        # Check language support
        if language not in provider_config:
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.WPS_LANGUAGE_UNSUPPORTED,
                    severity=DurationQualitySeverity.WARNING,
                    message=f"Language '{language}' not supported, using 'zh'",
                    details={"requested_language": language},
                )
            )
            language = "zh"

        lang_config = provider_config[language]

        # Validate speed
        if speed not in lang_config:
            speed = "normal"

        return lang_config[speed], provider_lower, issues

    def estimate_duration_with_provider(
        self,
        text: str,
        provider: Optional[str] = None,
        language: Optional[str] = None,
        speed: Optional[str] = None,
    ) -> Tuple[int, DurationQualityResult]:
        """
        Estimate duration using provider-specific WPS calibration.

        Args:
            text: Text to estimate duration for
            provider: TTS provider
            language: Language code
            speed: Speech speed

        Returns:
            Tuple of (duration_ms, validation_result)
        """
        wps, actual_provider, issues = self.get_calibrated_wps(
            provider, language, speed
        )

        # Count characters/words based on language
        language = language or self.default_language
        if language == "zh":
            word_count = len(text.replace(" ", ""))
        elif language == "ja":
            word_count = len(text.replace(" ", ""))
        elif language == "ko":
            word_count = len(text.replace(" ", ""))
        else:
            word_count = len(text.split())

        duration_seconds = word_count / wps if wps > 0 else 0
        duration_ms = int(duration_seconds * 1000)

        result = DurationQualityResult(
            passed=len([i for i in issues if i.severity == DurationQualitySeverity.ERROR]) == 0,
            issues=issues,
            calibrated_wps=wps,
            provider_used=actual_provider,
        )

        return duration_ms, result

    def analyze_word_distribution(
        self,
        scenes: List[Dict[str, Any]],
        language: Optional[str] = None,
    ) -> WordDistributionAnalysis:
        """
        Analyze word count distribution across scenes.

        Detects "front-heavy" or "back-heavy" patterns where word counts
        are unevenly distributed.

        Args:
            scenes: List of scene dictionaries with dialogues
            language: Language code for word counting

        Returns:
            WordDistributionAnalysis with distribution metrics
        """
        language = language or self.default_language
        scene_word_counts: List[int] = []

        for scene in scenes:
            dialogues = scene.get("dialogues", [])
            scene_words = 0
            for dlg in dialogues:
                content = dlg.get("content", "") or dlg.get("text", "")
                if language in ("zh", "ja", "ko"):
                    scene_words += len(content.replace(" ", ""))
                else:
                    scene_words += len(content.split())
            scene_word_counts.append(scene_words)

        analysis = WordDistributionAnalysis(scene_word_counts=scene_word_counts)

        if not scene_word_counts:
            return analysis

        analysis.total_words = sum(scene_word_counts)
        analysis.mean_words = statistics.mean(scene_word_counts)

        if len(scene_word_counts) > 1:
            analysis.std_dev = statistics.stdev(scene_word_counts)
            if analysis.mean_words > 0:
                analysis.coefficient_of_variation = (
                    analysis.std_dev / analysis.mean_words
                )

            # Calculate front-half ratio
            mid_point = len(scene_word_counts) // 2
            front_half_words = sum(scene_word_counts[:mid_point])
            analysis.front_half_ratio = (
                front_half_words / analysis.total_words
                if analysis.total_words > 0
                else 0.5
            )

            # Check for imbalance
            analysis.is_front_heavy = (
                analysis.front_half_ratio > self.SCENE_FRONT_HEAVY_THRESHOLD
            )
            analysis.is_back_heavy = (
                analysis.front_half_ratio < self.SCENE_BACK_HEAVY_THRESHOLD
            )

            # Find outlier scenes
            if analysis.std_dev > 0:
                for i, count in enumerate(scene_word_counts):
                    z_score = abs(count - analysis.mean_words) / analysis.std_dev
                    if z_score > self.SCENE_OUTLIER_ZSCORE:
                        analysis.outlier_scenes.append(i)

        return analysis

    def check_word_distribution(
        self,
        scenes: List[Dict[str, Any]],
        language: Optional[str] = None,
    ) -> Tuple[WordDistributionAnalysis, List[DurationQualityIssue]]:
        """
        Check word distribution and generate issues.

        Args:
            scenes: List of scene dictionaries
            language: Language code

        Returns:
            Tuple of (analysis, issues)
        """
        analysis = self.analyze_word_distribution(scenes, language)
        issues: List[DurationQualityIssue] = []

        if analysis.is_front_heavy:
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.SCENE_DISTRIBUTION_FRONT_HEAVY,
                    severity=DurationQualitySeverity.WARNING,
                    message=(
                        f"Word distribution is front-heavy "
                        f"({analysis.front_half_ratio:.0%} in first half)"
                    ),
                    details={
                        "front_half_ratio": analysis.front_half_ratio,
                        "threshold": self.SCENE_FRONT_HEAVY_THRESHOLD,
                    },
                    suggestions=[
                        "Consider redistributing dialogue to later scenes",
                        "Add more content to scenes in the second half",
                    ],
                )
            )

        if analysis.is_back_heavy:
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.SCENE_DISTRIBUTION_BACK_HEAVY,
                    severity=DurationQualitySeverity.WARNING,
                    message=(
                        f"Word distribution is back-heavy "
                        f"({1-analysis.front_half_ratio:.0%} in second half)"
                    ),
                    details={
                        "front_half_ratio": analysis.front_half_ratio,
                        "threshold": self.SCENE_BACK_HEAVY_THRESHOLD,
                    },
                    suggestions=[
                        "Consider redistributing dialogue to earlier scenes",
                        "Add more content to opening scenes",
                    ],
                )
            )

        for scene_idx in analysis.outlier_scenes:
            word_count = analysis.scene_word_counts[scene_idx]
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.SCENE_WORD_COUNT_OUTLIER,
                    severity=DurationQualitySeverity.INFO,
                    message=(
                        f"Scene {scene_idx + 1} has outlier word count "
                        f"({word_count} vs mean {analysis.mean_words:.0f})"
                    ),
                    scene_index=scene_idx,
                    details={
                        "word_count": word_count,
                        "mean": analysis.mean_words,
                        "std_dev": analysis.std_dev,
                    },
                )
            )

        return analysis, issues

    def analyze_retry_convergence(
        self,
        scene_budgets: List[Dict[str, Any]],
    ) -> List[RetryAnalysis]:
        """
        Analyze retry convergence patterns for scenes.

        Args:
            scene_budgets: List of scene budget dictionaries with retry history

        Returns:
            List of RetryAnalysis for each scene with retries
        """
        analyses: List[RetryAnalysis] = []

        for i, budget in enumerate(scene_budgets):
            attempt_count = budget.get("attempt_count", 1)
            if attempt_count <= 1:
                continue

            duration_history = budget.get("duration_history", [])
            if not duration_history:
                # Reconstruct from available data
                actual = budget.get("actual_duration_seconds")
                if actual:
                    duration_history = [actual]

            analysis = RetryAnalysis(
                scene_index=i,
                attempt_count=attempt_count,
                duration_history=duration_history,
            )

            if len(duration_history) >= 2:
                # Check for oscillation
                direction_changes = 0
                for j in range(1, len(duration_history) - 1):
                    prev_diff = duration_history[j] - duration_history[j - 1]
                    next_diff = duration_history[j + 1] - duration_history[j]
                    if (prev_diff > 0 and next_diff < 0) or (
                        prev_diff < 0 and next_diff > 0
                    ):
                        direction_changes += 1

                analysis.is_oscillating = (
                    direction_changes >= self.OSCILLATION_THRESHOLD
                )

                # Check convergence rate
                target = budget.get("target_duration_seconds", 0)
                if target > 0 and len(duration_history) >= 2:
                    first_error = abs(duration_history[0] - target)
                    last_error = abs(duration_history[-1] - target)
                    if first_error > 0:
                        convergence_rate = (first_error - last_error) / first_error
                        analysis.convergence_rate = convergence_rate
                        analysis.is_converging = (
                            convergence_rate > self.CONVERGENCE_RATE_THRESHOLD
                        )

            analyses.append(analysis)

        return analyses

    def check_retry_convergence(
        self,
        scene_budgets: List[Dict[str, Any]],
    ) -> Tuple[List[RetryAnalysis], List[DurationQualityIssue]]:
        """
        Check retry convergence and generate issues.

        Args:
            scene_budgets: List of scene budget dictionaries

        Returns:
            Tuple of (analyses, issues)
        """
        analyses = self.analyze_retry_convergence(scene_budgets)
        issues: List[DurationQualityIssue] = []

        total_retries = sum(
            max(0, b.get("attempt_count", 1) - 1) for b in scene_budgets
        )
        scene_count = len(scene_budgets)
        avg_retries = total_retries / scene_count if scene_count > 0 else 0

        # Check episode-level retry rate
        if avg_retries > 1.0:
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.EPISODE_HIGH_RETRY_RATE,
                    severity=DurationQualitySeverity.WARNING,
                    message=(
                        f"High retry rate: {avg_retries:.1f} retries/scene "
                        f"({total_retries} total across {scene_count} scenes)"
                    ),
                    details={
                        "total_retries": total_retries,
                        "scene_count": scene_count,
                        "avg_retries": avg_retries,
                    },
                    suggestions=[
                        "Review word count targets for scenes",
                        "Check if TTS WPS calibration matches actual provider",
                    ],
                )
            )

        # Check individual scene issues
        for analysis in analyses:
            if analysis.attempt_count >= self.MAX_HEALTHY_RETRIES:
                if not analysis.is_converging:
                    issues.append(
                        DurationQualityIssue(
                            issue_type=DurationQualityIssueType.SCENE_PATHOLOGICAL,
                            severity=DurationQualitySeverity.ERROR,
                            message=(
                                f"Scene {analysis.scene_index + 1} failed to converge "
                                f"after {analysis.attempt_count} attempts"
                            ),
                            scene_index=analysis.scene_index,
                            details={
                                "attempt_count": analysis.attempt_count,
                                "convergence_rate": analysis.convergence_rate,
                                "duration_history": analysis.duration_history,
                            },
                            suggestions=[
                                "Scene may need manual intervention",
                                "Consider adjusting target duration",
                                "Check for structural issues in dialogue",
                            ],
                        )
                    )

            if analysis.is_oscillating:
                issues.append(
                    DurationQualityIssue(
                        issue_type=DurationQualityIssueType.SCENE_RETRY_OSCILLATION,
                        severity=DurationQualitySeverity.WARNING,
                        message=(
                            f"Scene {analysis.scene_index + 1} shows oscillating "
                            f"duration pattern"
                        ),
                        scene_index=analysis.scene_index,
                        details={
                            "duration_history": analysis.duration_history,
                        },
                        suggestions=[
                            "Use smaller adjustment increments",
                            "Consider clamping adjustments",
                        ],
                    )
                )

        return analyses, issues

    def analyze_episode_balance(
        self,
        episodes: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[DurationQualityIssue]]:
        """
        Analyze duration balance across multiple episodes.

        Args:
            episodes: List of episode dictionaries with duration info

        Returns:
            Tuple of (balance_metrics, issues)
        """
        issues: List[DurationQualityIssue] = []
        durations: List[float] = []

        for ep in episodes:
            duration = ep.get("actual_duration_seconds") or ep.get(
                "total_duration_seconds", 0
            )
            durations.append(float(duration))

        if len(durations) < 2:
            return {"episode_count": len(durations), "balanced": True}, issues

        mean_duration = statistics.mean(durations)
        std_dev = statistics.stdev(durations)
        cv = std_dev / mean_duration if mean_duration > 0 else 0

        balance_metrics = {
            "episode_count": len(durations),
            "durations": durations,
            "mean_duration": round(mean_duration, 2),
            "std_dev": round(std_dev, 2),
            "coefficient_of_variation": round(cv, 4),
            "balanced": cv <= self.EPISODE_BALANCE_CV_THRESHOLD,
            "outlier_episodes": [],
        }

        # Check overall balance
        if cv > self.EPISODE_BALANCE_CV_THRESHOLD:
            issues.append(
                DurationQualityIssue(
                    issue_type=DurationQualityIssueType.EPISODE_DURATION_IMBALANCE,
                    severity=DurationQualitySeverity.WARNING,
                    message=(
                        f"Episode durations are imbalanced "
                        f"(CV={cv:.2%}, threshold={self.EPISODE_BALANCE_CV_THRESHOLD:.0%})"
                    ),
                    details={
                        "coefficient_of_variation": cv,
                        "threshold": self.EPISODE_BALANCE_CV_THRESHOLD,
                        "durations": durations,
                    },
                    suggestions=[
                        "Consider adjusting target durations for outlier episodes",
                        "Review content distribution across episodes",
                    ],
                )
            )

        # Find outlier episodes
        if std_dev > 0:
            for i, duration in enumerate(durations):
                z_score = abs(duration - mean_duration) / std_dev
                if z_score > self.EPISODE_OUTLIER_ZSCORE:
                    balance_metrics["outlier_episodes"].append(i)
                    direction = "too long" if duration > mean_duration else "too short"
                    issues.append(
                        DurationQualityIssue(
                            issue_type=DurationQualityIssueType.EPISODE_DURATION_OUTLIER,
                            severity=DurationQualitySeverity.INFO,
                            message=(
                                f"Episode {i + 1} is {direction} "
                                f"({duration:.0f}s vs mean {mean_duration:.0f}s)"
                            ),
                            episode_index=i,
                            details={
                                "duration": duration,
                                "mean": mean_duration,
                                "z_score": z_score,
                            },
                        )
                    )

        return balance_metrics, issues

    def validate(
        self,
        scenes: List[Dict[str, Any]],
        scene_budgets: Optional[List[Dict[str, Any]]] = None,
        episodes: Optional[List[Dict[str, Any]]] = None,
        provider: Optional[str] = None,
        language: Optional[str] = None,
    ) -> DurationQualityResult:
        """
        Perform comprehensive duration quality validation.

        Args:
            scenes: List of scene dictionaries with dialogues
            scene_budgets: Optional list of scene budget dictionaries
            episodes: Optional list of episode dictionaries for balance check
            provider: TTS provider for WPS calibration
            language: Language code

        Returns:
            DurationQualityResult with all findings
        """
        result = DurationQualityResult()

        # Get calibrated WPS
        wps, actual_provider, wps_issues = self.get_calibrated_wps(
            provider, language
        )
        result.calibrated_wps = wps
        result.provider_used = actual_provider
        result.issues.extend(wps_issues)

        # Analyze word distribution
        if scenes:
            word_dist, dist_issues = self.check_word_distribution(scenes, language)
            result.word_distribution = word_dist
            result.issues.extend(dist_issues)

        # Analyze retry convergence
        if scene_budgets:
            retry_analyses, retry_issues = self.check_retry_convergence(scene_budgets)
            result.retry_analyses = retry_analyses
            result.issues.extend(retry_issues)

        # Analyze episode balance
        if episodes and len(episodes) > 1:
            balance_metrics, balance_issues = self.analyze_episode_balance(episodes)
            result.episode_balance = balance_metrics
            result.issues.extend(balance_issues)

        # Determine overall pass/fail
        error_count = sum(
            1 for i in result.issues
            if i.severity == DurationQualitySeverity.ERROR
        )
        result.passed = error_count == 0

        return result
