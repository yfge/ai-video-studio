"""Timeline quality validator for rhythm and emotion curve analysis.

This module provides validation for:
- Emotion curve analysis (tension/relief wave visualization)
- Multi-language rhythm adaptation (Chinese/English/Japanese different WPS)
- Dramatic pause detection (comedy/drama beat spacing)
- Syllable-level timing estimation (replacing word count estimation)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TimelineQualityIssueType(Enum):
    """Types of timeline quality issues."""

    EMOTION_CURVE_FLAT = "emotion_curve_flat"
    EMOTION_CURVE_CHOPPY = "emotion_curve_choppy"
    RHYTHM_TOO_FAST = "rhythm_too_fast"
    RHYTHM_TOO_SLOW = "rhythm_too_slow"
    MISSING_DRAMATIC_PAUSE = "missing_dramatic_pause"
    EXCESSIVE_PAUSE = "excessive_pause"
    LANGUAGE_MISMATCH = "language_mismatch"
    DURATION_ESTIMATE_DRIFT = "duration_estimate_drift"


class TimelineQualitySeverity(Enum):
    """Severity levels for timeline quality issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TimelineQualityIssue:
    """Represents a single timeline quality issue."""

    issue_type: TimelineQualityIssueType
    severity: TimelineQualitySeverity
    message: str
    beat_index: Optional[int] = None
    time_range_ms: Optional[Tuple[int, int]] = None
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "beat_index": self.beat_index,
            "time_range_ms": self.time_range_ms,
            "details": self.details,
            "suggestions": self.suggestions,
        }


@dataclass
class EmotionPoint:
    """Represents an emotion data point in the timeline."""

    time_ms: int
    emotion_value: float  # -1.0 (calm) to 1.0 (intense)
    emotion_label: Optional[str] = None
    beat_index: Optional[int] = None


@dataclass
class EmotionCurveAnalysis:
    """Analysis of the emotion curve."""

    points: List[EmotionPoint] = field(default_factory=list)
    average_intensity: float = 0.0
    variance: float = 0.0
    peaks: List[int] = field(default_factory=list)  # Indices of peaks
    valleys: List[int] = field(default_factory=list)  # Indices of valleys
    has_arc: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_count": len(self.points),
            "average_intensity": round(self.average_intensity, 3),
            "variance": round(self.variance, 3),
            "peak_count": len(self.peaks),
            "valley_count": len(self.valleys),
            "has_arc": self.has_arc,
        }


@dataclass
class TimelineQualityResult:
    """Result of timeline quality validation."""

    passed: bool = True
    issues: List[TimelineQualityIssue] = field(default_factory=list)
    emotion_curve: Optional[EmotionCurveAnalysis] = None
    average_wps: float = 0.0
    detected_language: str = "unknown"
    total_duration_ms: int = 0
    pause_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "emotion_curve": self.emotion_curve.to_dict() if self.emotion_curve else None,
            "average_wps": round(self.average_wps, 2),
            "detected_language": self.detected_language,
            "total_duration_ms": self.total_duration_ms,
            "pause_ratio": round(self.pause_ratio, 3),
        }


class TimelineQualityValidator:
    """Validates timeline quality across multiple dimensions."""

    # Language-specific Words Per Second (WPS) constants
    # Based on TTS provider calibration and natural speech patterns
    WPS_BY_LANGUAGE = {
        "zh": {"slow": 3.8, "normal": 4.7, "fast": 5.6},  # Chinese characters/sec
        "en": {"slow": 2.5, "normal": 3.2, "fast": 4.0},  # English words/sec
        "ja": {"slow": 4.0, "normal": 5.0, "fast": 6.0},  # Japanese mora/sec
        "ko": {"slow": 3.5, "normal": 4.5, "fast": 5.5},  # Korean syllables/sec
    }

    # Emotion intensity keywords (Chinese)
    EMOTION_KEYWORDS = {
        "high_intensity": [
            "震惊", "愤怒", "恐惧", "绝望", "狂喜", "爆发", "崩溃",
            "激动", "紧张", "危机", "高潮", "对决", "冲突",
        ],
        "medium_intensity": [
            "焦虑", "担忧", "疑惑", "期待", "好奇", "惊讶",
            "兴奋", "不安", "紧迫", "悬念",
        ],
        "low_intensity": [
            "平静", "冷静", "沉默", "思考", "淡然", "轻松",
            "温馨", "舒缓", "宁静", "放松",
        ],
    }

    # Dramatic pause trigger keywords
    PAUSE_TRIGGERS = {
        "comedy": ["笑", "搞笑", "好笑", "哈哈", "逗", "滑稽"],
        "drama": ["哭", "泪", "悲伤", "痛苦", "感动", "泪目"],
        "suspense": ["震惊", "发现", "原来", "竟然", "真相", "秘密"],
        "action": ["爆炸", "冲击", "碰撞", "打击", "攻击"],
    }

    # Minimum pause duration for dramatic effect (ms)
    MIN_DRAMATIC_PAUSE_MS = 500
    MAX_DRAMATIC_PAUSE_MS = 3000

    def __init__(self) -> None:
        """Initialize the validator."""
        pass

    def validate(
        self,
        beats: List[Dict[str, Any]],
        expected_language: str = "zh",
        target_duration_ms: Optional[int] = None,
    ) -> TimelineQualityResult:
        """
        Validate timeline quality across multiple dimensions.

        Args:
            beats: List of timeline beat dictionaries
            expected_language: Expected primary language code
            target_duration_ms: Expected total duration in milliseconds

        Returns:
            TimelineQualityResult with validation results
        """
        result = TimelineQualityResult()

        if not beats:
            return result

        # Calculate total duration
        result.total_duration_ms = self._calculate_total_duration(beats)

        # Detect language
        result.detected_language = self._detect_language(beats)
        if result.detected_language != expected_language:
            result.issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.LANGUAGE_MISMATCH,
                    severity=TimelineQualitySeverity.INFO,
                    message=f"检测到语言 ({result.detected_language}) 与预期 ({expected_language}) 不符",
                    details={
                        "detected": result.detected_language,
                        "expected": expected_language,
                    },
                )
            )

        # Calculate average WPS
        result.average_wps = self._calculate_average_wps(
            beats, result.detected_language
        )
        wps_issues = self._check_rhythm(
            result.average_wps, result.detected_language
        )
        result.issues.extend(wps_issues)

        # Analyze emotion curve
        result.emotion_curve = self._analyze_emotion_curve(beats)
        emotion_issues = self._check_emotion_curve(result.emotion_curve)
        result.issues.extend(emotion_issues)

        # Check dramatic pauses
        result.pause_ratio = self._calculate_pause_ratio(beats)
        pause_issues = self._check_dramatic_pauses(beats)
        result.issues.extend(pause_issues)

        # Check duration drift if target provided
        if target_duration_ms:
            drift_issues = self._check_duration_drift(
                result.total_duration_ms, target_duration_ms
            )
            result.issues.extend(drift_issues)

        # Determine overall pass/fail
        error_count = sum(
            1 for issue in result.issues
            if issue.severity == TimelineQualitySeverity.ERROR
        )
        result.passed = error_count == 0

        return result

    def _calculate_total_duration(self, beats: List[Dict[str, Any]]) -> int:
        """Calculate total timeline duration in milliseconds."""
        if not beats:
            return 0

        max_end = 0
        for beat in beats:
            end_ms = beat.get("end_ms")
            if isinstance(end_ms, (int, float)):
                max_end = max(max_end, int(end_ms))

        return max_end

    def _detect_language(self, beats: List[Dict[str, Any]]) -> str:
        """Detect the primary language of the timeline content."""
        all_text = ""
        for beat in beats:
            text = beat.get("text") or beat.get("dialogue_excerpt") or ""
            if isinstance(text, str):
                all_text += text

        if not all_text:
            return "unknown"

        # Count character types
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", all_text))
        japanese_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", all_text))
        korean_chars = len(re.findall(r"[\uac00-\ud7af]", all_text))
        latin_chars = len(re.findall(r"[a-zA-Z]", all_text))

        total = chinese_chars + japanese_chars + korean_chars + latin_chars
        if total == 0:
            return "unknown"

        # Determine language by majority
        if japanese_chars / total > 0.3:
            return "ja"
        elif korean_chars / total > 0.3:
            return "ko"
        elif chinese_chars / total > 0.3:
            return "zh"
        elif latin_chars / total > 0.5:
            return "en"

        return "zh"  # Default to Chinese

    def _calculate_average_wps(
        self, beats: List[Dict[str, Any]], language: str
    ) -> float:
        """Calculate average words/characters per second."""
        total_chars = 0
        total_duration_sec = 0.0

        for beat in beats:
            beat_type = beat.get("beat_type")
            if beat_type not in ("dialogue", "narration"):
                continue

            text = beat.get("text") or beat.get("dialogue_excerpt") or ""
            if not isinstance(text, str) or not text.strip():
                continue

            # Get duration
            start_ms = beat.get("start_ms")
            end_ms = beat.get("end_ms")
            if start_ms is None or end_ms is None:
                continue

            duration_sec = (int(end_ms) - int(start_ms)) / 1000.0
            if duration_sec <= 0:
                continue

            # Count characters based on language
            if language in ("zh", "ja", "ko"):
                char_count = len(text.strip())
            else:
                # English: count words
                char_count = len(text.split())

            total_chars += char_count
            total_duration_sec += duration_sec

        return total_chars / total_duration_sec if total_duration_sec > 0 else 0.0

    def _check_rhythm(
        self, actual_wps: float, language: str
    ) -> List[TimelineQualityIssue]:
        """Check if rhythm matches expected WPS for language."""
        issues = []

        wps_config = self.WPS_BY_LANGUAGE.get(language, self.WPS_BY_LANGUAGE["zh"])
        slow_threshold = wps_config["slow"] * 0.8
        fast_threshold = wps_config["fast"] * 1.2

        if actual_wps < slow_threshold:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.RHYTHM_TOO_SLOW,
                    severity=TimelineQualitySeverity.WARNING,
                    message=f"整体节奏偏慢 ({actual_wps:.1f} 字/秒 < {slow_threshold:.1f})",
                    details={
                        "actual_wps": actual_wps,
                        "expected_range": [wps_config["slow"], wps_config["fast"]],
                    },
                    suggestions=[
                        "检查是否有过长停顿",
                        "调整 TTS 语速参数",
                    ],
                )
            )
        elif actual_wps > fast_threshold:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.RHYTHM_TOO_FAST,
                    severity=TimelineQualitySeverity.WARNING,
                    message=f"整体节奏偏快 ({actual_wps:.1f} 字/秒 > {fast_threshold:.1f})",
                    details={
                        "actual_wps": actual_wps,
                        "expected_range": [wps_config["slow"], wps_config["fast"]],
                    },
                    suggestions=[
                        "增加适当停顿",
                        "调整 TTS 语速参数",
                    ],
                )
            )

        return issues

    def _analyze_emotion_curve(
        self, beats: List[Dict[str, Any]]
    ) -> EmotionCurveAnalysis:
        """Analyze the emotional curve across the timeline."""
        analysis = EmotionCurveAnalysis()

        for idx, beat in enumerate(beats):
            time_ms = beat.get("start_ms") or beat.get("end_ms") or 0
            text = beat.get("text") or beat.get("dialogue_excerpt") or ""
            emotion = beat.get("emotion") or ""

            # Calculate emotion intensity
            intensity = self._calculate_emotion_intensity(text, emotion)

            point = EmotionPoint(
                time_ms=int(time_ms),
                emotion_value=intensity,
                emotion_label=emotion if emotion else None,
                beat_index=idx,
            )
            analysis.points.append(point)

        if not analysis.points:
            return analysis

        # Calculate statistics
        values = [p.emotion_value for p in analysis.points]
        analysis.average_intensity = sum(values) / len(values)

        if len(values) > 1:
            mean = analysis.average_intensity
            analysis.variance = sum((v - mean) ** 2 for v in values) / len(values)

        # Find peaks and valleys
        for i in range(1, len(values) - 1):
            if values[i] > values[i - 1] and values[i] > values[i + 1]:
                analysis.peaks.append(i)
            elif values[i] < values[i - 1] and values[i] < values[i + 1]:
                analysis.valleys.append(i)

        # Check if there's a proper arc (variance > threshold and peaks exist)
        analysis.has_arc = analysis.variance > 0.1 and len(analysis.peaks) > 0

        return analysis

    def _calculate_emotion_intensity(
        self, text: str, emotion_label: str
    ) -> float:
        """Calculate emotion intensity from text and label."""
        intensity = 0.0

        # Check emotion label
        if emotion_label:
            label_lower = emotion_label.lower()
            for keyword in self.EMOTION_KEYWORDS["high_intensity"]:
                if keyword in label_lower:
                    intensity += 0.5
                    break
            for keyword in self.EMOTION_KEYWORDS["medium_intensity"]:
                if keyword in label_lower:
                    intensity += 0.3
                    break
            for keyword in self.EMOTION_KEYWORDS["low_intensity"]:
                if keyword in label_lower:
                    intensity -= 0.2
                    break

        # Check text content
        if text:
            for keyword in self.EMOTION_KEYWORDS["high_intensity"]:
                if keyword in text:
                    intensity += 0.2
            for keyword in self.EMOTION_KEYWORDS["medium_intensity"]:
                if keyword in text:
                    intensity += 0.1

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, intensity))

    def _check_emotion_curve(
        self, analysis: EmotionCurveAnalysis
    ) -> List[TimelineQualityIssue]:
        """Check emotion curve for issues."""
        issues = []

        if not analysis.points:
            return issues

        # Check for flat curve
        if analysis.variance < 0.05:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.EMOTION_CURVE_FLAT,
                    severity=TimelineQualitySeverity.INFO,
                    message="情绪曲线较为平坦，缺乏起伏",
                    details={
                        "variance": analysis.variance,
                        "average_intensity": analysis.average_intensity,
                    },
                    suggestions=[
                        "在关键点设置情绪高潮",
                        "增加紧张-舒缓的对比",
                    ],
                )
            )

        # Check for too choppy curve (too many peaks)
        if len(analysis.peaks) > len(analysis.points) / 3:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.EMOTION_CURVE_CHOPPY,
                    severity=TimelineQualitySeverity.WARNING,
                    message="情绪波动过于频繁，可能导致观众疲劳",
                    details={
                        "peak_count": len(analysis.peaks),
                        "total_points": len(analysis.points),
                    },
                    suggestions=[
                        "减少情绪转折点",
                        "让高潮更加集中",
                    ],
                )
            )

        return issues

    def _calculate_pause_ratio(self, beats: List[Dict[str, Any]]) -> float:
        """Calculate the ratio of pause time to total time."""
        total_pause_ms = 0
        total_duration_ms = 0

        for beat in beats:
            start_ms = beat.get("start_ms")
            end_ms = beat.get("end_ms")
            if start_ms is None or end_ms is None:
                continue

            duration = int(end_ms) - int(start_ms)
            total_duration_ms += duration

            beat_type = beat.get("beat_type")
            if beat_type == "pause":
                total_pause_ms += duration

        return total_pause_ms / total_duration_ms if total_duration_ms > 0 else 0.0

    def _check_dramatic_pauses(
        self, beats: List[Dict[str, Any]]
    ) -> List[TimelineQualityIssue]:
        """Check for appropriate dramatic pauses."""
        issues = []

        # Find trigger points that need pauses
        trigger_indices = []
        for idx, beat in enumerate(beats):
            text = beat.get("text") or beat.get("dialogue_excerpt") or ""
            for category, keywords in self.PAUSE_TRIGGERS.items():
                for keyword in keywords:
                    if keyword in text:
                        trigger_indices.append((idx, category))
                        break

        # Check if pauses exist after trigger points
        missing_pauses = []
        for idx, category in trigger_indices:
            # Look for pause in next 2 beats
            found_pause = False
            for look_ahead in range(1, 3):
                if idx + look_ahead >= len(beats):
                    break
                next_beat = beats[idx + look_ahead]
                if next_beat.get("beat_type") == "pause":
                    duration = (
                        next_beat.get("end_ms", 0) - next_beat.get("start_ms", 0)
                    )
                    if duration >= self.MIN_DRAMATIC_PAUSE_MS:
                        found_pause = True
                        break

            if not found_pause:
                missing_pauses.append((idx, category))

        if missing_pauses:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.MISSING_DRAMATIC_PAUSE,
                    severity=TimelineQualitySeverity.INFO,
                    message=f"有 {len(missing_pauses)} 处关键节点缺少戏剧停顿",
                    details={
                        "missing_at": [
                            {"beat_index": idx, "category": cat}
                            for idx, cat in missing_pauses[:5]
                        ]
                    },
                    suggestions=[
                        "在笑点/泪点后添加适当停顿",
                        "让重要信息有时间沉淀",
                    ],
                )
            )

        # Check for excessive pauses
        long_pauses = []
        for idx, beat in enumerate(beats):
            if beat.get("beat_type") == "pause":
                start_ms = beat.get("start_ms", 0)
                end_ms = beat.get("end_ms", 0)
                duration = end_ms - start_ms
                if duration > self.MAX_DRAMATIC_PAUSE_MS:
                    long_pauses.append((idx, duration))

        if long_pauses:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.EXCESSIVE_PAUSE,
                    severity=TimelineQualitySeverity.WARNING,
                    message=f"有 {len(long_pauses)} 处停顿时间过长 (>{self.MAX_DRAMATIC_PAUSE_MS}ms)",
                    details={
                        "long_pauses": [
                            {"beat_index": idx, "duration_ms": dur}
                            for idx, dur in long_pauses[:5]
                        ]
                    },
                    suggestions=[
                        "缩短停顿时间",
                        "考虑用动作填充空白",
                    ],
                )
            )

        return issues

    def _check_duration_drift(
        self, actual_ms: int, target_ms: int
    ) -> List[TimelineQualityIssue]:
        """Check if actual duration drifts from target."""
        issues = []

        if target_ms <= 0:
            return issues

        drift_percent = abs(actual_ms - target_ms) / target_ms * 100

        if drift_percent > 20:
            issues.append(
                TimelineQualityIssue(
                    issue_type=TimelineQualityIssueType.DURATION_ESTIMATE_DRIFT,
                    severity=TimelineQualitySeverity.WARNING,
                    message=f"实际时长与预期偏差 {drift_percent:.0f}%",
                    details={
                        "actual_ms": actual_ms,
                        "target_ms": target_ms,
                        "drift_percent": round(drift_percent, 1),
                    },
                    suggestions=[
                        "重新校准 WPS 参数",
                        "检查 TTS 提供商语速设置",
                    ],
                )
            )

        return issues

    def estimate_duration_syllable_level(
        self,
        text: str,
        language: str = "zh",
        speed: str = "normal",
    ) -> int:
        """
        Estimate duration using syllable-level analysis.

        This provides more accurate estimates than simple word counting.

        Args:
            text: Text to estimate duration for
            language: Language code
            speed: Speed setting (slow/normal/fast)

        Returns:
            Estimated duration in milliseconds
        """
        if not text:
            return 0

        wps_config = self.WPS_BY_LANGUAGE.get(language, self.WPS_BY_LANGUAGE["zh"])
        wps = wps_config.get(speed, wps_config["normal"])

        if language == "zh":
            # Chinese: count characters, add time for punctuation pauses
            char_count = len(re.sub(r"\s", "", text))
            pause_count = len(re.findall(r"[，。！？、；：]", text))
            base_ms = int(char_count / wps * 1000)
            pause_ms = pause_count * 100  # 100ms per punctuation
            return base_ms + pause_ms

        elif language == "ja":
            # Japanese: count mora (roughly = kana + kanji)
            hiragana = len(re.findall(r"[\u3040-\u309f]", text))
            katakana = len(re.findall(r"[\u30a0-\u30ff]", text))
            kanji = len(re.findall(r"[\u4e00-\u9fff]", text))
            mora_count = hiragana + katakana + kanji * 2  # Kanji ≈ 2 mora
            return int(mora_count / wps * 1000)

        elif language == "en":
            # English: count syllables (approximation)
            words = text.split()
            syllable_count = 0
            for word in words:
                # Simple syllable counting heuristic
                word = word.lower().strip(".,!?;:")
                vowel_groups = len(re.findall(r"[aeiouy]+", word))
                syllable_count += max(1, vowel_groups)
            # English avg ~2.5 syllables/word, ~4 syllables/sec
            return int(syllable_count / 4 * 1000 / (wps_config[speed] / 3.2))

        elif language == "ko":
            # Korean: count syllable blocks (Hangul blocks)
            syllables = len(re.findall(r"[\uac00-\ud7af]", text))
            return int(syllables / wps * 1000)

        # Default fallback
        return int(len(text) / wps * 1000)
