"""
Unit tests for the Timeline Agent.

Tests the intelligent timing calculation for dialogue gaps.
"""

from __future__ import annotations

import pytest

from app.services.timeline_agent.constants import (
    EMOTION_TRANSITION_WEIGHTS,
    MAX_GAP_MS,
    MIN_GAP_MS,
)
from app.services.timeline_agent.schemas import (
    DialogueContext,
    SceneContext,
    TimingDecision,
    TimingPlan,
)
from app.services.timeline_agent.utils import (
    build_dialogue_contexts,
    build_scene_context,
    calculate_fallback_timing,
    calculate_rhythm_score,
    extract_dominant_mood,
    get_emotion_transition_weight,
    infer_conflict_level,
    infer_pacing,
)


class TestSceneContextBuilding:
    """Tests for scene context extraction."""

    def test_extract_dominant_mood_with_emotions(self):
        """Should return most common emotion."""
        dialogues = [
            {"character": "A", "content": "Hi", "emotion": "happy"},
            {"character": "B", "content": "Hello", "emotion": "happy"},
            {"character": "A", "content": "Bye", "emotion": "sad"},
        ]
        mood = extract_dominant_mood(dialogues)
        assert mood == "happy"

    def test_extract_dominant_mood_no_emotions(self):
        """Should return None when no emotions tagged."""
        dialogues = [
            {"character": "A", "content": "Hi"},
            {"character": "B", "content": "Hello"},
        ]
        mood = extract_dominant_mood(dialogues)
        assert mood is None

    def test_infer_conflict_level_high(self):
        """Should detect high conflict keywords."""
        assert infer_conflict_level("激烈的对峙") == "high"
        assert infer_conflict_level("紧张的场面") == "high"

    def test_infer_conflict_level_low(self):
        """Should detect low conflict keywords."""
        assert infer_conflict_level("平静的早晨") == "low"
        assert infer_conflict_level("温馨的家庭") == "low"

    def test_infer_conflict_level_default(self):
        """Should return medium for unknown."""
        assert infer_conflict_level(None) == "medium"
        assert infer_conflict_level("普通对话") == "medium"

    def test_infer_pacing_fast(self):
        """Should infer fast pacing for many dialogues."""
        assert infer_pacing(15) == "fast"

    def test_infer_pacing_slow(self):
        """Should infer slow pacing for few dialogues."""
        assert infer_pacing(2) == "slow"

    def test_infer_pacing_medium(self):
        """Should infer medium pacing for moderate dialogues."""
        assert infer_pacing(6) == "medium"


class TestDialogueContextBuilding:
    """Tests for dialogue context extraction."""

    def test_build_dialogue_contexts_basic(self):
        """Should build contexts with transitions."""
        dialogues = [
            {"character": "小明", "content": "你好", "emotion": "happy"},
            {"character": "小红", "content": "你也好", "emotion": "calm"},
        ]
        contexts = build_dialogue_contexts(dialogues)

        assert len(contexts) == 2
        assert contexts[0].speaker == "小明"
        assert contexts[0].emotion == "happy"
        assert contexts[0].prev_emotion is None
        assert contexts[0].is_first is True

        assert contexts[1].speaker == "小红"
        assert contexts[1].prev_emotion == "happy"
        assert contexts[1].is_last is True

    def test_build_scene_context(self):
        """Should build complete scene context."""
        dialogues = [
            {"character": "A", "content": "Hi", "emotion": "angry"},
            {"character": "B", "content": "What?", "emotion": "angry"},
        ]
        context = build_scene_context(
            scene_id=1,
            scene_number=1,
            dialogues=dialogues,
            conflict_notes="激烈争吵",
        )

        assert context.scene_id == 1
        assert context.mood == "angry"
        assert context.conflict_level == "high"
        assert context.character_count == 2
        assert context.dialogue_count == 2


class TestEmotionTransitionWeights:
    """Tests for emotion transition weight calculation."""

    def test_known_transition(self):
        """Should return correct weight for known transitions."""
        weight = get_emotion_transition_weight("angry", "calm")
        assert weight == EMOTION_TRANSITION_WEIGHTS[("angry", "calm")]
        assert weight > 1.0  # Should need longer pause

    def test_same_emotion(self):
        """Should return lower weight for same emotion."""
        weight = get_emotion_transition_weight("calm", "calm")
        assert weight < 1.0  # Should be shorter pause

    def test_unknown_transition(self):
        """Should return 1.0 for unknown transitions."""
        weight = get_emotion_transition_weight("unknown1", "unknown2")
        assert weight == 1.0

    def test_none_emotions(self):
        """Should handle None emotions."""
        weight = get_emotion_transition_weight(None, None)
        assert weight == 1.0


class TestFallbackTiming:
    """Tests for rule-based fallback timing."""

    def test_fallback_timing_basic(self):
        """Should generate valid timing decisions."""
        dialogues = [
            {"character": "A", "content": "Hi", "emotion": "happy"},
            {"character": "B", "content": "Hello"},
        ]
        dialogue_contexts = build_dialogue_contexts(dialogues)
        scene_context = build_scene_context(
            scene_id=1,
            scene_number=1,
            dialogues=dialogues,
        )

        decisions = calculate_fallback_timing(dialogue_contexts, scene_context)

        assert len(decisions) == 2
        for d in decisions:
            assert MIN_GAP_MS <= d.adjusted_duration_ms <= MAX_GAP_MS
            assert d.gap_type == "post_dialogue"

    def test_fallback_timing_respects_pacing(self):
        """Should adjust timing based on pacing."""
        fast_dialogues = [{"character": f"C{i}", "content": f"Line {i}"} for i in range(12)]
        slow_dialogues = [{"character": "A", "content": "Hello"}]

        fast_contexts = build_dialogue_contexts(fast_dialogues)
        slow_contexts = build_dialogue_contexts(slow_dialogues)

        fast_scene = build_scene_context(1, 1, fast_dialogues)
        slow_scene = build_scene_context(2, 2, slow_dialogues)

        fast_decisions = calculate_fallback_timing(fast_contexts, fast_scene)
        slow_decisions = calculate_fallback_timing(slow_contexts, slow_scene)

        # Fast scene should have shorter average gap
        fast_avg = sum(d.adjusted_duration_ms for d in fast_decisions) / len(fast_decisions)
        slow_avg = sum(d.adjusted_duration_ms for d in slow_decisions) / len(slow_decisions)

        assert fast_avg < slow_avg


class TestRhythmScore:
    """Tests for rhythm variety scoring."""

    def test_monotonous_rhythm(self):
        """Should score low for identical durations."""
        decisions = [
            TimingDecision(segment_index=i, adjusted_duration_ms=300, base_duration_ms=300)
            for i in range(5)
        ]
        score = calculate_rhythm_score(decisions)
        assert score < 0.3  # Low score for monotonous

    def test_varied_rhythm(self):
        """Should score higher for varied durations."""
        decisions = [
            TimingDecision(segment_index=0, adjusted_duration_ms=200, base_duration_ms=300),
            TimingDecision(segment_index=1, adjusted_duration_ms=500, base_duration_ms=300),
            TimingDecision(segment_index=2, adjusted_duration_ms=300, base_duration_ms=300),
            TimingDecision(segment_index=3, adjusted_duration_ms=800, base_duration_ms=300),
        ]
        score = calculate_rhythm_score(decisions)
        assert score > 0.3  # Higher score for varied

    def test_single_decision(self):
        """Should return 0.5 for single decision."""
        decisions = [TimingDecision(segment_index=0, adjusted_duration_ms=300, base_duration_ms=300)]
        score = calculate_rhythm_score(decisions)
        assert score == 0.5


class TestTimingPlanValidation:
    """Tests for TimingPlan schema validation."""

    def test_timing_plan_creation(self):
        """Should create valid timing plan."""
        decisions = [
            TimingDecision(
                segment_index=0,
                gap_type="post_dialogue",
                base_duration_ms=300,
                adjusted_duration_ms=350,
                reasoning="Emotion transition",
            )
        ]
        plan = TimingPlan(
            scene_id=1,
            decisions=decisions,
            total_gap_ms=350,
            avg_gap_ms=350.0,
            rhythm_score=0.5,
        )

        assert plan.scene_id == 1
        assert len(plan.decisions) == 1
        assert plan.fallback_used is False

    def test_timing_decision_constraints(self):
        """Should enforce value constraints."""
        # Valid decision
        valid = TimingDecision(
            segment_index=0,
            gap_type="post_dialogue",
            base_duration_ms=300,
            adjusted_duration_ms=500,
        )
        assert valid.emotion_factor == 1.0  # Default

        # Emotion factor limits
        with pytest.raises(ValueError):
            TimingDecision(
                segment_index=0,
                gap_type="post_dialogue",
                base_duration_ms=300,
                adjusted_duration_ms=500,
                emotion_factor=5.0,  # > 3.0 limit
            )


class TestSceneContext:
    """Tests for SceneContext schema."""

    def test_scene_context_defaults(self):
        """Should have sensible defaults."""
        context = SceneContext(scene_number=1, scene_id=1)

        assert context.mood is None
        assert context.conflict_level == "medium"
        assert context.pacing == "medium"
        assert context.character_count == 1
        assert context.dialogue_count == 0
        assert context.has_dramatic_question is False

    def test_scene_context_validation(self):
        """Should validate field constraints."""
        with pytest.raises(ValueError):
            SceneContext(
                scene_number=1,
                scene_id=1,
                character_count=0,  # Must be >= 1
            )
