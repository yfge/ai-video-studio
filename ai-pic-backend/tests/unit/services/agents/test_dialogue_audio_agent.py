"""Unit tests for DialogueAudioAgent."""

from __future__ import annotations

import pytest

from app.services.agents.dialogue_audio_agent import (
    CharacterVoiceProfile,
    DialogueAudioAgent,
    DialogueAudioResult,
    DialogueQualityIssue,
    DialogueQualityIssueType,
    DialogueQualitySeverity,
    DialogueRenderPlan,
    EmotionCategory,
)


@pytest.fixture
def agent() -> DialogueAudioAgent:
    """Create an agent instance."""
    return DialogueAudioAgent()


@pytest.fixture
def agent_with_voices() -> DialogueAudioAgent:
    """Create an agent with pre-registered voices."""
    agent = DialogueAudioAgent()
    agent.register_voice(
        CharacterVoiceProfile(
            character_name="Alice",
            voice_id="female_alice_01",
            voice_name="Alice Voice",
            gender="female",
            age_group="adult",
        )
    )
    agent.register_voice(
        CharacterVoiceProfile(
            character_name="Bob",
            voice_id="male_bob_01",
            voice_name="Bob Voice",
            gender="male",
            age_group="adult",
        )
    )
    return agent


class TestCharacterVoiceProfile:
    """Tests for CharacterVoiceProfile dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        profile = CharacterVoiceProfile(
            character_name="Test",
            voice_id="test_voice",
            voice_name="Test Voice",
            gender="female",
            age_group="adult",
            voice_traits=["gentle", "warm"],
            default_emotion=EmotionCategory.CALM,
            default_speed=1.1,
        )
        d = profile.to_dict()
        assert d["character_name"] == "Test"
        assert d["voice_id"] == "test_voice"
        assert d["default_emotion"] == "calm"
        assert d["default_speed"] == 1.1

    def test_from_dict(self) -> None:
        """Test deserialization."""
        data = {
            "character_name": "Test",
            "voice_id": "test_voice",
            "default_emotion": "happy",
            "default_speed": 1.2,
        }
        profile = CharacterVoiceProfile.from_dict(data)
        assert profile.character_name == "Test"
        assert profile.voice_id == "test_voice"
        assert profile.default_emotion == EmotionCategory.HAPPY
        assert profile.default_speed == 1.2

    def test_from_dict_invalid_emotion(self) -> None:
        """Test deserialization with invalid emotion defaults to calm."""
        data = {
            "character_name": "Test",
            "voice_id": "test_voice",
            "default_emotion": "invalid_emotion",
        }
        profile = CharacterVoiceProfile.from_dict(data)
        assert profile.default_emotion == EmotionCategory.CALM


class TestDialogueRenderPlan:
    """Tests for DialogueRenderPlan dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        plan = DialogueRenderPlan(
            dialogue_index=0,
            character_name="Alice",
            content="Hello world",
            voice_id="alice_voice",
            emotion=EmotionCategory.HAPPY,
            speed=1.0,
            start_time_ms=0,
            estimated_duration_ms=1500,
        )
        d = plan.to_dict()
        assert d["dialogue_index"] == 0
        assert d["character_name"] == "Alice"
        assert d["emotion"] == "happy"


class TestDialogueQualityIssue:
    """Tests for DialogueQualityIssue dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        issue = DialogueQualityIssue(
            issue_type=DialogueQualityIssueType.EMOTION_MISMATCH,
            severity=DialogueQualitySeverity.WARNING,
            message="Test message",
            dialogue_index=5,
            character="Alice",
            details={"key": "value"},
            suggestions=["Fix it"],
        )
        d = issue.to_dict()
        assert d["issue_type"] == "emotion_mismatch"
        assert d["severity"] == "warning"
        assert d["dialogue_index"] == 5


class TestDialogueAudioAgent:
    """Tests for DialogueAudioAgent."""

    # ============================================
    # Voice Registry Tests
    # ============================================

    def test_register_voice(self, agent: DialogueAudioAgent) -> None:
        """Test voice registration."""
        profile = CharacterVoiceProfile(
            character_name="Test Character",
            voice_id="test_voice_01",
        )
        agent.register_voice(profile)

        retrieved = agent.get_voice_profile("Test Character")
        assert retrieved is not None
        assert retrieved.voice_id == "test_voice_01"

    def test_register_voice_case_insensitive(self, agent: DialogueAudioAgent) -> None:
        """Test voice registration is case insensitive."""
        profile = CharacterVoiceProfile(
            character_name="Alice",
            voice_id="alice_voice",
        )
        agent.register_voice(profile)

        # Should find with different case
        assert agent.get_voice_profile("ALICE") is not None
        assert agent.get_voice_profile("alice") is not None
        assert agent.get_voice_profile("Alice") is not None

    def test_register_voices_from_config(self, agent: DialogueAudioAgent) -> None:
        """Test bulk voice registration from config."""
        configs = [
            {"character_name": "Alice", "voice_id": "alice_01"},
            {"character_name": "Bob", "voice_id": "bob_01"},
        ]
        issues = agent.register_voices_from_config(configs)

        assert len(issues) == 0
        assert agent.get_voice_profile("Alice") is not None
        assert agent.get_voice_profile("Bob") is not None

    def test_get_voice_registry(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test getting full voice registry."""
        registry = agent_with_voices.get_voice_registry()
        assert len(registry) == 2
        assert "alice" in registry
        assert "bob" in registry

    # ============================================
    # Emotion Detection Tests
    # ============================================

    def test_detect_emotion_happy(self, agent: DialogueAudioAgent) -> None:
        """Test happy emotion detection."""
        emotion, confidence = agent.detect_dialogue_emotion(
            "太好了！我太开心了！", language="zh"
        )
        assert emotion == EmotionCategory.HAPPY
        assert confidence > 0.3

    def test_detect_emotion_sad(self, agent: DialogueAudioAgent) -> None:
        """Test sad emotion detection."""
        emotion, confidence = agent.detect_dialogue_emotion(
            "我好伤心，真的太难过了", language="zh"
        )
        assert emotion == EmotionCategory.SAD
        assert confidence > 0.3

    def test_detect_emotion_angry(self, agent: DialogueAudioAgent) -> None:
        """Test angry emotion detection."""
        emotion, confidence = agent.detect_dialogue_emotion(
            "我非常愤怒！太气愤了！", language="zh"
        )
        assert emotion == EmotionCategory.ANGRY
        assert confidence > 0.3

    def test_detect_emotion_with_action(self, agent: DialogueAudioAgent) -> None:
        """Test emotion detection with action hint."""
        emotion, _ = agent.detect_dialogue_emotion(
            "好的", action_hint="低声说道", language="zh"
        )
        assert emotion == EmotionCategory.WHISPER

    def test_detect_emotion_neutral(self, agent: DialogueAudioAgent) -> None:
        """Test neutral emotion detection."""
        emotion, _ = agent.detect_dialogue_emotion(
            "今天天气不错", language="zh"
        )
        assert emotion == EmotionCategory.CALM  # Default

    def test_detect_emotion_english(self, agent: DialogueAudioAgent) -> None:
        """Test emotion detection in English."""
        emotion, _ = agent.detect_dialogue_emotion(
            "I'm so happy and excited!", language="en"
        )
        assert emotion == EmotionCategory.HAPPY

    # ============================================
    # Emotion Alignment Validation Tests
    # ============================================

    def test_validate_emotion_alignment_pass(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test emotion alignment with matching emotions."""
        dialogues = [
            {
                "character": "Alice",
                "content": "我太开心了！",
                "tts_emotion": "happy",
            },
            {
                "character": "Bob",
                "content": "我也很高兴",
                "tts_emotion": "happy",
            },
        ]
        issues = agent.validate_emotion_alignment(dialogues)

        mismatch_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.EMOTION_MISMATCH
        ]
        assert len(mismatch_issues) == 0

    def test_validate_emotion_alignment_mismatch(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test emotion alignment with mismatched emotions."""
        dialogues = [
            {
                "character": "Alice",
                "content": "我非常愤怒！太生气了！",
                "tts_emotion": "happy",  # Mismatch
            },
        ]
        issues = agent.validate_emotion_alignment(dialogues)

        mismatch_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.EMOTION_MISMATCH
        ]
        assert len(mismatch_issues) > 0

    def test_validate_emotion_transition_abrupt(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test abrupt emotion transition detection."""
        dialogues = [
            {"character": "Alice", "content": "我太开心了！哈哈！"},
            {"character": "Alice", "content": "我非常愤怒！"},  # Abrupt change
        ]
        issues = agent.validate_emotion_alignment(dialogues)

        transition_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.EMOTION_TRANSITION_ABRUPT
        ]
        assert len(transition_issues) > 0

    # ============================================
    # Speech Rhythm Validation Tests
    # ============================================

    def test_validate_speech_rhythm_normal(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test normal speech rhythm."""
        dialogues = [
            {
                "character": "Alice",
                "content": "这是一段正常语速的对白",  # 10 chars
                "duration_ms": 2200,  # ~4.5 chars/sec
            },
        ]
        issues = agent.validate_speech_rhythm(dialogues, "zh")

        rhythm_issues = [
            i for i in issues
            if i.issue_type in (
                DialogueQualityIssueType.SPEECH_TOO_FAST,
                DialogueQualityIssueType.SPEECH_TOO_SLOW,
            )
        ]
        assert len(rhythm_issues) == 0

    def test_validate_speech_rhythm_too_fast(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test detection of too fast speech."""
        dialogues = [
            {
                "character": "Alice",
                "content": "这是一段非常非常长的对白内容需要很快说完",  # ~20 chars
                "duration_ms": 1000,  # 20 chars/sec - way too fast
            },
        ]
        issues = agent.validate_speech_rhythm(dialogues, "zh")

        fast_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.SPEECH_TOO_FAST
        ]
        assert len(fast_issues) > 0

    def test_validate_speech_rhythm_too_slow(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test detection of too slow speech."""
        dialogues = [
            {
                "character": "Alice",
                "content": "短",  # 1 char
                "duration_ms": 5000,  # 0.2 chars/sec - way too slow
            },
        ]
        issues = agent.validate_speech_rhythm(dialogues, "zh")

        slow_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.SPEECH_TOO_SLOW
        ]
        assert len(slow_issues) > 0

    # ============================================
    # Turn Taking Validation Tests
    # ============================================

    def test_validate_turn_taking_normal(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test normal turn taking."""
        dialogues = [
            {
                "character": "Alice",
                "start_time_ms": 0,
                "duration_ms": 1000,
            },
            {
                "character": "Bob",
                "start_time_ms": 1300,  # 300ms gap
                "duration_ms": 1000,
            },
        ]
        issues = agent.validate_turn_taking(dialogues)

        turn_issues = [
            i for i in issues
            if i.issue_type in (
                DialogueQualityIssueType.DIALOGUE_OVERLAP,
                DialogueQualityIssueType.SPEAKER_CHANGE_TOO_FAST,
            )
        ]
        assert len(turn_issues) == 0

    def test_validate_turn_taking_overlap(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test overlap detection."""
        dialogues = [
            {
                "character": "Alice",
                "start_time_ms": 0,
                "duration_ms": 1000,
                "end_time_ms": 1000,
            },
            {
                "character": "Bob",
                "start_time_ms": 800,  # 200ms overlap
                "duration_ms": 1000,
            },
        ]
        issues = agent.validate_turn_taking(dialogues)

        overlap_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.DIALOGUE_OVERLAP
        ]
        assert len(overlap_issues) > 0

    def test_validate_turn_taking_fast_change(
        self, agent: DialogueAudioAgent
    ) -> None:
        """Test detection of too fast speaker change."""
        dialogues = [
            {
                "character": "Alice",
                "start_time_ms": 0,
                "duration_ms": 1000,
                "end_time_ms": 1000,
            },
            {
                "character": "Bob",
                "start_time_ms": 1050,  # Only 50ms gap
                "duration_ms": 1000,
            },
        ]
        issues = agent.validate_turn_taking(dialogues)

        fast_change_issues = [
            i for i in issues
            if i.issue_type == DialogueQualityIssueType.SPEAKER_CHANGE_TOO_FAST
        ]
        assert len(fast_change_issues) > 0

    # ============================================
    # Render Plan Tests
    # ============================================

    def test_create_render_plan_success(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test successful render plan creation."""
        dialogues = [
            {
                "character": "Alice",
                "content": "你好",
                "start_time_ms": 0,
                "duration_ms": 1000,
            },
            {
                "character": "Bob",
                "content": "你好",
                "start_time_ms": 1200,
                "duration_ms": 1000,
            },
        ]
        result = agent_with_voices.create_render_plan(dialogues)

        assert result.success is True
        assert len(result.render_plans) == 2
        assert result.total_estimated_duration_ms == 2000

    def test_create_render_plan_missing_voice(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test render plan with missing voice."""
        dialogues = [
            {
                "character": "Unknown",  # No voice registered
                "content": "你好",
            },
        ]
        result = agent_with_voices.create_render_plan(dialogues)

        assert result.success is False
        voice_issues = [
            i for i in result.issues
            if i.issue_type == DialogueQualityIssueType.VOICE_NOT_ASSIGNED
        ]
        assert len(voice_issues) > 0

    def test_create_render_plan_statistics(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test render plan statistics."""
        dialogues = [
            {
                "character": "Alice",
                "content": "你好",
                "duration_ms": 1000,
            },
            {
                "character": "Bob",
                "content": "你好",
                "duration_ms": 1000,
            },
            {
                "character": "Alice",
                "content": "再见",
                "duration_ms": 800,
            },
        ]
        result = agent_with_voices.create_render_plan(dialogues)

        assert result.statistics["dialogue_count"] == 3
        assert result.statistics["render_plan_count"] == 3
        assert "Alice" in result.statistics["characters"]
        assert "Bob" in result.statistics["characters"]

    def test_create_render_plan_emotion_detection(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test emotion detection in render plan."""
        dialogues = [
            {
                "character": "Alice",
                "content": "太开心了！我好高兴！",
            },
        ]
        result = agent_with_voices.create_render_plan(dialogues)

        assert len(result.render_plans) == 1
        assert result.render_plans[0].emotion == EmotionCategory.HAPPY

    # ============================================
    # Integration Tests
    # ============================================

    def test_full_workflow(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test full dialogue audio workflow."""
        dialogues = [
            {
                "character": "Alice",
                "content": "你好，很高兴认识你",
                "start_time_ms": 0,
                "duration_ms": 1500,
            },
            {
                "character": "Bob",
                "content": "你好，我也很高兴",
                "start_time_ms": 1800,
                "duration_ms": 1200,
            },
            {
                "character": "Alice",
                "content": "那我们开始吧",
                "start_time_ms": 3200,
                "duration_ms": 1000,
            },
        ]

        result = agent_with_voices.create_render_plan(dialogues)

        assert result.success is True
        assert len(result.render_plans) == 3
        assert len(result.voice_registry) == 2

        # Check render plan details
        for plan in result.render_plans:
            assert plan.voice_id is not None
            assert plan.emotion is not None

    def test_result_to_dict(
        self, agent_with_voices: DialogueAudioAgent
    ) -> None:
        """Test result serialization."""
        dialogues = [
            {
                "character": "Alice",
                "content": "你好",
                "duration_ms": 1000,
            },
        ]
        result = agent_with_voices.create_render_plan(dialogues)
        d = result.to_dict()

        assert "success" in d
        assert "render_plans" in d
        assert "issues" in d
        assert "voice_registry" in d
        assert "statistics" in d
