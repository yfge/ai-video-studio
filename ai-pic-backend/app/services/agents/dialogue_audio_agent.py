"""
Dialogue Audio Agent

Agent-based service for dialogue audio generation with:
- Character voice registry management
- Emotion-dialogue alignment validation
- Speech rate/rhythm naturalness detection
- Multi-character dialogue rendering coordination
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class EmotionCategory(str, Enum):
    """Emotion categories for TTS."""

    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"
    CALM = "calm"
    FLUENT = "fluent"
    WHISPER = "whisper"
    NEUTRAL = "neutral"


class DialogueQualityIssueType(str, Enum):
    """Types of dialogue audio quality issues."""

    # Voice registry issues
    VOICE_NOT_ASSIGNED = "voice_not_assigned"
    VOICE_MISMATCH = "voice_mismatch"

    # Emotion alignment issues
    EMOTION_MISMATCH = "emotion_mismatch"
    EMOTION_TRANSITION_ABRUPT = "emotion_transition_abrupt"

    # Rhythm issues
    SPEECH_TOO_FAST = "speech_too_fast"
    SPEECH_TOO_SLOW = "speech_too_slow"
    RHYTHM_UNNATURAL = "rhythm_unnatural"

    # Multi-character issues
    DIALOGUE_OVERLAP = "dialogue_overlap"
    TURN_TAKING_UNNATURAL = "turn_taking_unnatural"
    SPEAKER_CHANGE_TOO_FAST = "speaker_change_too_fast"


class DialogueQualitySeverity(str, Enum):
    """Severity levels for dialogue quality issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DialogueQualityIssue:
    """Represents a dialogue audio quality issue."""

    issue_type: DialogueQualityIssueType
    severity: DialogueQualitySeverity
    message: str
    dialogue_index: Optional[int] = None
    character: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "dialogue_index": self.dialogue_index,
            "character": self.character,
            "details": self.details,
            "suggestions": self.suggestions,
        }


@dataclass
class CharacterVoiceProfile:
    """Voice profile for a character."""

    character_name: str
    voice_id: str
    voice_name: Optional[str] = None
    language: str = "zh"
    gender: Optional[str] = None
    age_group: Optional[str] = None
    voice_traits: List[str] = field(default_factory=list)
    default_emotion: EmotionCategory = EmotionCategory.CALM
    default_speed: float = 1.0
    pitch_offset: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "character_name": self.character_name,
            "voice_id": self.voice_id,
            "voice_name": self.voice_name,
            "language": self.language,
            "gender": self.gender,
            "age_group": self.age_group,
            "voice_traits": self.voice_traits,
            "default_emotion": self.default_emotion.value,
            "default_speed": self.default_speed,
            "pitch_offset": self.pitch_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterVoiceProfile":
        """Create from dictionary."""
        emotion_str = data.get("default_emotion", "calm")
        try:
            emotion = EmotionCategory(emotion_str)
        except ValueError:
            emotion = EmotionCategory.CALM

        return cls(
            character_name=data.get("character_name", ""),
            voice_id=data.get("voice_id", ""),
            voice_name=data.get("voice_name"),
            language=data.get("language", "zh"),
            gender=data.get("gender"),
            age_group=data.get("age_group"),
            voice_traits=data.get("voice_traits", []),
            default_emotion=emotion,
            default_speed=data.get("default_speed", 1.0),
            pitch_offset=data.get("pitch_offset", 0.0),
        )


@dataclass
class DialogueRenderPlan:
    """Plan for rendering a single dialogue."""

    dialogue_index: int
    character_name: str
    content: str
    voice_id: str
    emotion: EmotionCategory
    speed: float = 1.0
    start_time_ms: Optional[int] = None
    estimated_duration_ms: Optional[int] = None
    action_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dialogue_index": self.dialogue_index,
            "character_name": self.character_name,
            "content": self.content,
            "voice_id": self.voice_id,
            "emotion": self.emotion.value,
            "speed": self.speed,
            "start_time_ms": self.start_time_ms,
            "estimated_duration_ms": self.estimated_duration_ms,
            "action_hint": self.action_hint,
        }


@dataclass
class DialogueAudioResult:
    """Result of dialogue audio processing."""

    success: bool = True
    render_plans: List[DialogueRenderPlan] = field(default_factory=list)
    issues: List[DialogueQualityIssue] = field(default_factory=list)
    voice_registry: Dict[str, CharacterVoiceProfile] = field(default_factory=dict)
    total_estimated_duration_ms: int = 0
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "render_plans": [p.to_dict() for p in self.render_plans],
            "issues": [i.to_dict() for i in self.issues],
            "voice_registry": {
                k: v.to_dict() for k, v in self.voice_registry.items()
            },
            "total_estimated_duration_ms": self.total_estimated_duration_ms,
            "statistics": self.statistics,
        }


class DialogueAudioAgent:
    """
    Dialogue Audio Agent for coordinated multi-character audio generation.

    Features:
    - Character voice registry management
    - Emotion-dialogue alignment validation
    - Speech rate/rhythm naturalness detection
    - Multi-character dialogue rendering coordination
    """

    # Emotion keywords mapping
    EMOTION_KEYWORDS: Dict[EmotionCategory, Dict[str, List[str]]] = {
        EmotionCategory.HAPPY: {
            "zh": ["开心", "高兴", "兴奋", "喜悦", "愉快", "欢乐", "笑"],
            "en": ["happy", "excited", "joyful", "delighted", "pleased"],
        },
        EmotionCategory.SAD: {
            "zh": ["悲伤", "难过", "伤心", "沮丧", "忧郁", "哭泣", "失落"],
            "en": ["sad", "sorrowful", "melancholy", "depressed", "upset"],
        },
        EmotionCategory.ANGRY: {
            "zh": ["愤怒", "生气", "恼怒", "暴怒", "怒吼", "气愤"],
            "en": ["angry", "furious", "enraged", "mad", "irritated"],
        },
        EmotionCategory.FEARFUL: {
            "zh": ["害怕", "恐惧", "惊恐", "胆怯", "紧张", "担忧"],
            "en": ["fearful", "scared", "terrified", "anxious", "worried"],
        },
        EmotionCategory.SURPRISED: {
            "zh": ["惊讶", "震惊", "吃惊", "意外", "诧异"],
            "en": ["surprised", "shocked", "astonished", "amazed"],
        },
        EmotionCategory.CALM: {
            "zh": ["平静", "冷静", "淡定", "从容", "镇定"],
            "en": ["calm", "composed", "serene", "peaceful"],
        },
        EmotionCategory.WHISPER: {
            "zh": ["低声", "悄悄", "耳语", "小声", "轻声"],
            "en": ["whisper", "murmur", "quietly", "softly"],
        },
    }

    # Dialogue emotion mismatches (dialogue emotion vs TTS emotion should match)
    EMOTION_COMPATIBILITY: Dict[str, Set[EmotionCategory]] = {
        "happy": {EmotionCategory.HAPPY, EmotionCategory.SURPRISED, EmotionCategory.FLUENT},
        "sad": {EmotionCategory.SAD, EmotionCategory.CALM, EmotionCategory.WHISPER},
        "angry": {EmotionCategory.ANGRY, EmotionCategory.DISGUSTED},
        "scared": {EmotionCategory.FEARFUL, EmotionCategory.WHISPER},
        "excited": {EmotionCategory.HAPPY, EmotionCategory.SURPRISED},
        "calm": {EmotionCategory.CALM, EmotionCategory.FLUENT, EmotionCategory.NEUTRAL},
        "neutral": {EmotionCategory.CALM, EmotionCategory.NEUTRAL, EmotionCategory.FLUENT},
    }

    # Speech rate thresholds (characters per second)
    SPEECH_RATE_THRESHOLDS = {
        "zh": {"slow": 2.5, "normal_low": 3.5, "normal_high": 5.5, "fast": 7.0},
        "en": {"slow": 2.0, "normal_low": 2.8, "normal_high": 4.0, "fast": 5.0},
    }

    # Minimum pause between different speakers (ms)
    MIN_SPEAKER_CHANGE_GAP_MS = 200

    # Maximum speech overlap allowed (ms)
    MAX_OVERLAP_MS = 50

    def __init__(
        self,
        default_language: str = "zh",
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        """
        Initialize the Dialogue Audio Agent.

        Args:
            default_language: Default language for processing
            progress_callback: Optional progress callback function
        """
        self.default_language = default_language
        self.progress_callback = progress_callback
        self._voice_registry: Dict[str, CharacterVoiceProfile] = {}

    def register_voice(self, profile: CharacterVoiceProfile) -> None:
        """Register a voice profile for a character."""
        normalized_name = self._normalize_name(profile.character_name)
        self._voice_registry[normalized_name] = profile
        logger.info(
            f"Registered voice for {profile.character_name}: {profile.voice_id}"
        )

    def register_voices_from_config(
        self, voice_configs: List[Dict[str, Any]]
    ) -> List[DialogueQualityIssue]:
        """
        Register multiple voices from configuration.

        Args:
            voice_configs: List of voice configuration dictionaries

        Returns:
            List of issues encountered during registration
        """
        issues: List[DialogueQualityIssue] = []

        for config in voice_configs:
            try:
                profile = CharacterVoiceProfile.from_dict(config)
                self.register_voice(profile)
            except Exception as e:
                issues.append(
                    DialogueQualityIssue(
                        issue_type=DialogueQualityIssueType.VOICE_NOT_ASSIGNED,
                        severity=DialogueQualitySeverity.WARNING,
                        message=f"Failed to register voice: {e}",
                        character=config.get("character_name"),
                        details={"config": config, "error": str(e)},
                    )
                )

        return issues

    def get_voice_profile(
        self, character_name: str
    ) -> Optional[CharacterVoiceProfile]:
        """Get voice profile for a character."""
        normalized = self._normalize_name(character_name)
        return self._voice_registry.get(normalized)

    def get_voice_registry(self) -> Dict[str, CharacterVoiceProfile]:
        """Get the full voice registry."""
        return self._voice_registry.copy()

    def detect_dialogue_emotion(
        self,
        content: str,
        action_hint: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Tuple[EmotionCategory, float]:
        """
        Detect emotion from dialogue content and action hint.

        Args:
            content: Dialogue text content
            action_hint: Optional action/stage direction hint
            language: Language code

        Returns:
            Tuple of (detected_emotion, confidence)
        """
        lang = language or self.default_language
        combined = f"{content} {action_hint or ''}".lower()

        best_emotion = EmotionCategory.CALM
        best_score = 0.0

        for emotion, lang_keywords in self.EMOTION_KEYWORDS.items():
            keywords = lang_keywords.get(lang, []) + lang_keywords.get("en", [])
            score = sum(1 for kw in keywords if kw in combined)
            if score > best_score:
                best_score = score
                best_emotion = emotion

        confidence = min(best_score / 3.0, 1.0) if best_score > 0 else 0.5
        return best_emotion, confidence

    def validate_emotion_alignment(
        self,
        dialogues: List[Dict[str, Any]],
    ) -> List[DialogueQualityIssue]:
        """
        Validate emotion-dialogue alignment.

        Args:
            dialogues: List of dialogue dictionaries

        Returns:
            List of alignment issues
        """
        issues: List[DialogueQualityIssue] = []

        for i, dlg in enumerate(dialogues):
            content = dlg.get("content", "") or dlg.get("text", "")
            action = dlg.get("action", "")
            tts_emotion = dlg.get("tts_emotion", "") or dlg.get("emotion", "")

            # Detect emotion from content
            detected, confidence = self.detect_dialogue_emotion(content, action)

            # Check if TTS emotion is compatible
            if tts_emotion:
                tts_emotion_lower = tts_emotion.lower()
                compatible_emotions = self.EMOTION_COMPATIBILITY.get(
                    tts_emotion_lower, set()
                )

                if detected not in compatible_emotions and confidence > 0.6:
                    issues.append(
                        DialogueQualityIssue(
                            issue_type=DialogueQualityIssueType.EMOTION_MISMATCH,
                            severity=DialogueQualitySeverity.WARNING,
                            message=(
                                f"Dialogue emotion mismatch: content suggests "
                                f"'{detected.value}' but TTS set to '{tts_emotion}'"
                            ),
                            dialogue_index=i,
                            character=dlg.get("character"),
                            details={
                                "detected_emotion": detected.value,
                                "tts_emotion": tts_emotion,
                                "confidence": confidence,
                            },
                            suggestions=[
                                f"Consider changing TTS emotion to '{detected.value}'",
                                "Review dialogue content for emotional cues",
                            ],
                        )
                    )

        # Check for abrupt emotion transitions
        issues.extend(self._check_emotion_transitions(dialogues))

        return issues

    def _check_emotion_transitions(
        self,
        dialogues: List[Dict[str, Any]],
    ) -> List[DialogueQualityIssue]:
        """Check for abrupt emotion transitions within same character."""
        issues: List[DialogueQualityIssue] = []

        # Group dialogues by character
        char_sequences: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
        for i, dlg in enumerate(dialogues):
            char = self._normalize_name(dlg.get("character", "unknown"))
            if char not in char_sequences:
                char_sequences[char] = []
            char_sequences[char].append((i, dlg))

        # Check each character's sequence
        for char, sequence in char_sequences.items():
            if len(sequence) < 2:
                continue

            for j in range(1, len(sequence)):
                prev_idx, prev_dlg = sequence[j - 1]
                curr_idx, curr_dlg = sequence[j]

                prev_emotion, _ = self.detect_dialogue_emotion(
                    prev_dlg.get("content", ""),
                    prev_dlg.get("action", ""),
                )
                curr_emotion, _ = self.detect_dialogue_emotion(
                    curr_dlg.get("content", ""),
                    curr_dlg.get("action", ""),
                )

                # Check for abrupt transitions (e.g., happy → angry without transition)
                if self._is_abrupt_transition(prev_emotion, curr_emotion):
                    issues.append(
                        DialogueQualityIssue(
                            issue_type=DialogueQualityIssueType.EMOTION_TRANSITION_ABRUPT,
                            severity=DialogueQualitySeverity.INFO,
                            message=(
                                f"Abrupt emotion transition for {char}: "
                                f"{prev_emotion.value} → {curr_emotion.value}"
                            ),
                            dialogue_index=curr_idx,
                            character=char,
                            details={
                                "prev_emotion": prev_emotion.value,
                                "curr_emotion": curr_emotion.value,
                                "prev_index": prev_idx,
                            },
                            suggestions=[
                                "Add transitional dialogue between emotional extremes",
                                "Use 'calm' or 'neutral' as intermediate state",
                            ],
                        )
                    )

        return issues

    def _is_abrupt_transition(
        self, prev: EmotionCategory, curr: EmotionCategory
    ) -> bool:
        """Check if emotion transition is abrupt."""
        # Define incompatible direct transitions
        abrupt_pairs = {
            (EmotionCategory.HAPPY, EmotionCategory.ANGRY),
            (EmotionCategory.ANGRY, EmotionCategory.HAPPY),
            (EmotionCategory.HAPPY, EmotionCategory.SAD),
            (EmotionCategory.FEARFUL, EmotionCategory.ANGRY),
        }
        return (prev, curr) in abrupt_pairs

    def validate_speech_rhythm(
        self,
        dialogues: List[Dict[str, Any]],
        language: Optional[str] = None,
    ) -> List[DialogueQualityIssue]:
        """
        Validate speech rate and rhythm naturalness.

        Args:
            dialogues: List of dialogue dictionaries
            language: Language code

        Returns:
            List of rhythm issues
        """
        issues: List[DialogueQualityIssue] = []
        lang = language or self.default_language
        thresholds = self.SPEECH_RATE_THRESHOLDS.get(
            lang, self.SPEECH_RATE_THRESHOLDS["zh"]
        )

        for i, dlg in enumerate(dialogues):
            content = dlg.get("content", "") or dlg.get("text", "")
            duration_ms = dlg.get("duration_ms") or dlg.get("estimated_duration_ms")

            if not content or not duration_ms:
                continue

            # Calculate speech rate
            char_count = len(content.replace(" ", ""))
            duration_seconds = duration_ms / 1000.0
            rate = char_count / duration_seconds if duration_seconds > 0 else 0

            # Check rate bounds
            if rate < thresholds["slow"]:
                issues.append(
                    DialogueQualityIssue(
                        issue_type=DialogueQualityIssueType.SPEECH_TOO_SLOW,
                        severity=DialogueQualitySeverity.WARNING,
                        message=(
                            f"Speech rate too slow: {rate:.1f} chars/sec "
                            f"(min: {thresholds['slow']})"
                        ),
                        dialogue_index=i,
                        character=dlg.get("character"),
                        details={
                            "rate": rate,
                            "threshold": thresholds["slow"],
                            "char_count": char_count,
                            "duration_ms": duration_ms,
                        },
                        suggestions=[
                            "Increase TTS speed",
                            "Shorten pause durations",
                        ],
                    )
                )
            elif rate > thresholds["fast"]:
                issues.append(
                    DialogueQualityIssue(
                        issue_type=DialogueQualityIssueType.SPEECH_TOO_FAST,
                        severity=DialogueQualitySeverity.WARNING,
                        message=(
                            f"Speech rate too fast: {rate:.1f} chars/sec "
                            f"(max: {thresholds['fast']})"
                        ),
                        dialogue_index=i,
                        character=dlg.get("character"),
                        details={
                            "rate": rate,
                            "threshold": thresholds["fast"],
                            "char_count": char_count,
                            "duration_ms": duration_ms,
                        },
                        suggestions=[
                            "Decrease TTS speed",
                            "Add pauses between phrases",
                        ],
                    )
                )

        return issues

    def validate_turn_taking(
        self,
        dialogues: List[Dict[str, Any]],
    ) -> List[DialogueQualityIssue]:
        """
        Validate multi-character turn-taking patterns.

        Args:
            dialogues: List of dialogue dictionaries with timing info

        Returns:
            List of turn-taking issues
        """
        issues: List[DialogueQualityIssue] = []

        for i in range(1, len(dialogues)):
            prev_dlg = dialogues[i - 1]
            curr_dlg = dialogues[i]

            prev_end = prev_dlg.get("end_time_ms") or (
                (prev_dlg.get("start_time_ms") or 0)
                + (prev_dlg.get("duration_ms") or 0)
            )
            curr_start = curr_dlg.get("start_time_ms")

            if prev_end is None or curr_start is None:
                continue

            prev_char = self._normalize_name(prev_dlg.get("character", ""))
            curr_char = self._normalize_name(curr_dlg.get("character", ""))

            gap = curr_start - prev_end

            # Check for overlap
            if gap < -self.MAX_OVERLAP_MS:
                issues.append(
                    DialogueQualityIssue(
                        issue_type=DialogueQualityIssueType.DIALOGUE_OVERLAP,
                        severity=DialogueQualitySeverity.ERROR,
                        message=(
                            f"Dialogues overlap by {abs(gap)}ms "
                            f"(max allowed: {self.MAX_OVERLAP_MS}ms)"
                        ),
                        dialogue_index=i,
                        details={
                            "prev_end_ms": prev_end,
                            "curr_start_ms": curr_start,
                            "overlap_ms": abs(gap),
                        },
                        suggestions=[
                            "Adjust timing to remove overlap",
                            "Reduce previous dialogue duration",
                        ],
                    )
                )

            # Check for speaker change gap
            if prev_char != curr_char:
                if 0 <= gap < self.MIN_SPEAKER_CHANGE_GAP_MS:
                    issues.append(
                        DialogueQualityIssue(
                            issue_type=DialogueQualityIssueType.SPEAKER_CHANGE_TOO_FAST,
                            severity=DialogueQualitySeverity.INFO,
                            message=(
                                f"Speaker change gap too short: {gap}ms "
                                f"(min: {self.MIN_SPEAKER_CHANGE_GAP_MS}ms)"
                            ),
                            dialogue_index=i,
                            character=curr_dlg.get("character"),
                            details={
                                "gap_ms": gap,
                                "min_gap_ms": self.MIN_SPEAKER_CHANGE_GAP_MS,
                                "prev_character": prev_dlg.get("character"),
                            },
                            suggestions=[
                                "Add brief pause between speakers",
                                "Allows audience to register speaker change",
                            ],
                        )
                    )

        return issues

    def create_render_plan(
        self,
        dialogues: List[Dict[str, Any]],
        language: Optional[str] = None,
    ) -> DialogueAudioResult:
        """
        Create a comprehensive render plan for dialogues.

        Args:
            dialogues: List of dialogue dictionaries
            language: Language code

        Returns:
            DialogueAudioResult with render plans and issues
        """
        result = DialogueAudioResult()
        result.voice_registry = self._voice_registry.copy()

        render_plans: List[DialogueRenderPlan] = []
        total_duration = 0

        for i, dlg in enumerate(dialogues):
            character = dlg.get("character", "unknown")
            content = dlg.get("content", "") or dlg.get("text", "")
            action = dlg.get("action", "")

            # Get voice profile
            profile = self.get_voice_profile(character)
            if not profile:
                result.issues.append(
                    DialogueQualityIssue(
                        issue_type=DialogueQualityIssueType.VOICE_NOT_ASSIGNED,
                        severity=DialogueQualitySeverity.ERROR,
                        message=f"No voice assigned for character '{character}'",
                        dialogue_index=i,
                        character=character,
                        suggestions=[
                            "Register voice profile for character",
                            "Use default voice as fallback",
                        ],
                    )
                )
                continue

            # Detect emotion
            emotion, _ = self.detect_dialogue_emotion(content, action, language)

            # Create render plan
            plan = DialogueRenderPlan(
                dialogue_index=i,
                character_name=character,
                content=content,
                voice_id=profile.voice_id,
                emotion=emotion,
                speed=profile.default_speed,
                start_time_ms=dlg.get("start_time_ms"),
                estimated_duration_ms=dlg.get("duration_ms"),
                action_hint=action if action else None,
            )
            render_plans.append(plan)

            if plan.estimated_duration_ms:
                total_duration += plan.estimated_duration_ms

        result.render_plans = render_plans
        result.total_estimated_duration_ms = total_duration

        # Run validations
        result.issues.extend(self.validate_emotion_alignment(dialogues))
        result.issues.extend(self.validate_speech_rhythm(dialogues, language))
        result.issues.extend(self.validate_turn_taking(dialogues))

        # Determine success
        error_count = sum(
            1 for i in result.issues
            if i.severity == DialogueQualitySeverity.ERROR
        )
        result.success = error_count == 0

        # Statistics
        result.statistics = {
            "dialogue_count": len(dialogues),
            "render_plan_count": len(render_plans),
            "total_duration_ms": total_duration,
            "issue_count": len(result.issues),
            "error_count": error_count,
            "warning_count": sum(
                1 for i in result.issues
                if i.severity == DialogueQualitySeverity.WARNING
            ),
            "characters": list(set(
                dlg.get("character", "unknown") for dlg in dialogues
            )),
        }

        return result

    def _normalize_name(self, name: str) -> str:
        """Normalize character name for matching."""
        return "".join((name or "").strip().lower().split())
