"""Unit tests for ScriptQualityValidator."""

from __future__ import annotations

import pytest

from app.services.validators.script_quality_validator import (
    SceneEmotionalArc,
    ScriptQualityIssue,
    ScriptQualityIssueType,
    ScriptQualityResult,
    ScriptQualitySeverity,
    ScriptQualityValidator,
)


@pytest.fixture
def validator() -> ScriptQualityValidator:
    """Create a validator instance."""
    return ScriptQualityValidator()


class TestScriptQualityIssue:
    """Tests for ScriptQualityIssue dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization."""
        issue = ScriptQualityIssue(
            issue_type=ScriptQualityIssueType.UNNATURAL_DIALOGUE,
            severity=ScriptQualitySeverity.WARNING,
            message="Test message",
            scene_number=1,
            dialogue_index=5,
            details={"key": "value"},
            suggestions=["Fix it"],
        )
        result = issue.to_dict()
        assert result["issue_type"] == "unnatural_dialogue"
        assert result["severity"] == "warning"
        assert result["message"] == "Test message"
        assert result["scene_number"] == 1
        assert result["dialogue_index"] == 5


class TestSceneEmotionalArc:
    """Tests for SceneEmotionalArc dataclass."""

    def test_to_dict_with_progression(self) -> None:
        """Test serialization with emotion progression."""
        arc = SceneEmotionalArc(
            scene_number=1,
            entry_emotion="平静",
            exit_emotion="愤怒",
            emotion_sequence=["平静", "疑惑", "愤怒"],
            has_progression=True,
        )
        d = arc.to_dict()
        assert d["scene_number"] == 1
        assert d["entry_emotion"] == "平静"
        assert d["exit_emotion"] == "愤怒"
        assert d["has_progression"] is True

    def test_to_dict_flat(self) -> None:
        """Test serialization with flat emotion."""
        arc = SceneEmotionalArc(
            scene_number=2,
            entry_emotion="开心",
            exit_emotion="开心",
            emotion_sequence=["开心", "开心", "开心"],
            has_progression=False,
        )
        d = arc.to_dict()
        assert d["has_progression"] is False


class TestScriptQualityResult:
    """Tests for ScriptQualityResult dataclass."""

    def test_to_dict_minimal(self) -> None:
        """Test serialization with minimal data."""
        result = ScriptQualityResult(passed=True)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["issues"] == []
        assert d["dialogue_authenticity_score"] == 0.0

    def test_to_dict_full(self) -> None:
        """Test serialization with full data."""
        result = ScriptQualityResult(
            passed=True,
            dialogue_authenticity_score=0.75,
            exposition_ratio=0.15,
            dialogue_action_ratio=2.5,
        )
        d = result.to_dict()
        assert d["dialogue_authenticity_score"] == 0.75
        assert d["exposition_ratio"] == 0.15
        assert d["dialogue_action_ratio"] == 2.5


class TestScriptQualityValidator:
    """Tests for ScriptQualityValidator."""

    def test_validate_empty_content(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test validation with empty content."""
        result = validator.validate({"dialogues": []})
        assert result.passed is True
        assert len(result.issues) == 0

    def test_score_dialogue_authenticity_natural(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test authenticity scoring with natural dialogue."""
        dialogues = [
            {"content": "嗯...你说的对吧？我也不确定呢。"},
            {"content": "真的吗？太好了！"},
            {"content": "啊，那怎么办呢？"},
        ]
        score = validator._score_dialogue_authenticity(dialogues)
        assert score > 0.5  # Natural dialogue should score above average

    def test_score_dialogue_authenticity_unnatural(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test authenticity scoring with expository dialogue."""
        dialogues = [
            {"content": "正如你所知，我们的任务是非常重要的，因为它关系到整个计划的成败。"},
            {"content": "让我解释一下，事情是这样的，在很久以前发生了一件事情。"},
        ]
        score = validator._score_dialogue_authenticity(dialogues)
        assert score < 0.6  # Expository dialogue should score lower

    def test_score_single_dialogue_with_questions(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test single dialogue scoring with questions."""
        natural = "你怎么看？同意吗？"
        expository = "正如你所知，事实上，简单来说就是这样。"

        natural_score = validator._score_single_dialogue(natural)
        exp_score = validator._score_single_dialogue(expository)

        assert natural_score > exp_score

    def test_calculate_exposition_ratio(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test exposition ratio calculation."""
        dialogues = [
            {"content": "让我解释一下，事情是这样的。"},  # Expository
            {"content": "你好啊！"},  # Natural
            {"content": "正如你所知，我来告诉你原因。"},  # Expository
            {"content": "嗯，好的。"},  # Natural
        ]
        ratio = validator._calculate_exposition_ratio(dialogues)
        assert ratio == 0.5  # 2 out of 4 are expository

    def test_is_expository_true(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test expository detection with expository content."""
        content = "正如你所知，让我解释一下这件事情。"
        assert validator._is_expository(content) is True

    def test_is_expository_false(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test expository detection with natural content."""
        content = "你怎么了？发生什么事了？"
        assert validator._is_expository(content) is False

    def test_check_exposition_excessive(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test excessive exposition detection."""
        dialogues = [
            {"scene_number": 1, "content": "正如你所知，我来告诉你。"},
            {"scene_number": 1, "content": "让我解释一下事情是这样的。"},
            {"scene_number": 1, "content": "事实上简单来说就是这样。"},
            {"scene_number": 1, "content": "你可能不知道，其实原来是这样。"},
        ]
        issues = validator._check_exposition(dialogues)
        assert len(issues) > 0
        assert issues[0].issue_type == ScriptQualityIssueType.EXCESSIVE_EXPOSITION

    def test_calculate_dialogue_action_ratio(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test dialogue-action ratio calculation."""
        dialogues = [{"content": "a"}, {"content": "b"}, {"content": "c"}]
        stage_directions = [{"content": "x"}]

        ratio = validator._calculate_dialogue_action_ratio(dialogues, stage_directions)
        assert ratio == 3.0

    def test_check_dialogue_action_ratio_imbalanced(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test dialogue-action ratio with imbalance."""
        # Too many dialogues
        issues = validator._check_dialogue_action_ratio(10.0, [])
        assert len(issues) > 0
        assert issues[0].issue_type == ScriptQualityIssueType.TALKING_HEADS

    def test_check_dialogue_action_ratio_balanced(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test dialogue-action ratio with balanced content."""
        issues = validator._check_dialogue_action_ratio(2.0, [])
        assert len(issues) == 0

    def test_analyze_emotional_arcs(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test emotional arc analysis."""
        scenes = [{"scene_number": 1}, {"scene_number": 2}]
        dialogues = [
            {"scene_number": 1, "content": "a", "emotion": "平静"},
            {"scene_number": 1, "content": "b", "emotion": "疑惑"},
            {"scene_number": 1, "content": "c", "emotion": "愤怒"},
            {"scene_number": 2, "content": "d", "emotion": "开心"},
            {"scene_number": 2, "content": "e", "emotion": "开心"},
        ]

        arcs = validator._analyze_emotional_arcs(scenes, dialogues)

        assert len(arcs) == 2
        assert arcs[0].has_progression is True  # Scene 1 has progression
        assert arcs[1].has_progression is False  # Scene 2 is flat

    def test_check_emotional_arcs_flat(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test emotional arc check with flat emotion."""
        arcs = [
            SceneEmotionalArc(
                scene_number=1,
                entry_emotion="开心",
                exit_emotion="开心",
                emotion_sequence=["开心", "开心", "开心"],
                has_progression=False,
            )
        ]
        issues = validator._check_emotional_arcs(arcs)
        assert len(issues) > 0
        assert issues[0].issue_type == ScriptQualityIssueType.EMOTIONAL_ARC_FLAT

    def test_check_emotional_arcs_jump(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test emotional arc check with unreasonable jump."""
        arcs = [
            SceneEmotionalArc(
                scene_number=1,
                entry_emotion="开心",
                exit_emotion="震惊愤怒",
                emotion_sequence=["开心", "震惊愤怒"],
                has_progression=True,
            )
        ]
        issues = validator._check_emotional_arcs(arcs)
        jump_issues = [
            i for i in issues
            if i.issue_type == ScriptQualityIssueType.EMOTIONAL_ARC_JUMP
        ]
        assert len(jump_issues) > 0

    def test_categorize_emotion(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test emotion categorization."""
        assert validator._categorize_emotion("开心") == "positive"
        assert validator._categorize_emotion("愤怒") == "intense"
        assert validator._categorize_emotion("平静") == "neutral"
        assert validator._categorize_emotion("悲伤") == "negative"
        assert validator._categorize_emotion("未知") == "neutral"

    def test_check_subtext_missing(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test subtext check with missing subtext."""
        # Create 15 direct dialogues with no subtext
        dialogues = [
            {"content": f"直接表达 {i}。"} for i in range(15)
        ]
        issues = validator._check_subtext(dialogues)
        subtext_issues = [
            i for i in issues
            if i.issue_type == ScriptQualityIssueType.MISSING_SUBTEXT
        ]
        assert len(subtext_issues) > 0

    def test_check_subtext_present(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test subtext check with subtext present."""
        dialogues = [
            {"content": "没事，很好。但是..."},  # Has subtext
            {"content": "挺好的，不过我还是担心。"},  # Has subtext
            {"content": "没关系，然而心里很痛。"},  # Has subtext
        ]
        issues = validator._check_subtext(dialogues)
        # Should not report missing subtext
        subtext_issues = [
            i for i in issues
            if i.issue_type == ScriptQualityIssueType.MISSING_SUBTEXT
        ]
        assert len(subtext_issues) == 0

    def test_check_repetitive_dialogue(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test repetitive dialogue detection."""
        dialogues = [
            {"content": "你好啊，今天天气真好"},
            {"content": "你好啊，今天天气真好"},
            {"content": "你好啊，今天天气真好"},
            {"content": "不同的内容"},
        ]
        issues = validator._check_repetitive_dialogue(dialogues)
        assert len(issues) > 0
        assert issues[0].issue_type == ScriptQualityIssueType.REPETITIVE_DIALOGUE

    def test_validate_full_script_good(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test full validation with good script."""
        content = {
            "scenes": [{"scene_number": 1}],
            "dialogues": [
                {"scene_number": 1, "content": "嗯...你怎么看？", "emotion": "好奇"},
                {"scene_number": 1, "content": "我觉得...不太对劲！", "emotion": "疑惑"},
                {"scene_number": 1, "content": "天啊！原来是这样？", "emotion": "震惊"},
            ],
            "stage_directions": [
                {"scene_number": 1, "content": "角色A皱眉"},
                {"scene_number": 1, "content": "角色B站起身"},
            ],
        }

        result = validator.validate(content)

        assert result.passed is True
        assert result.dialogue_authenticity_score > 0.4
        assert result.dialogue_action_ratio > 0

    def test_validate_full_script_with_issues(
        self, validator: ScriptQualityValidator
    ) -> None:
        """Test full validation with problematic script."""
        content = {
            "scenes": [{"scene_number": 1}],
            "dialogues": [
                {"scene_number": 1, "content": "正如你所知，让我解释一下事情是这样的。", "emotion": "平静"},
                {"scene_number": 1, "content": "事实上简单来说，我来告诉你原因。", "emotion": "平静"},
                {"scene_number": 1, "content": "你可能不知道，其实原来是这样的。", "emotion": "平静"},
            ],
            "stage_directions": [],
        }

        result = validator.validate(content)

        # Should have issues for:
        # - Excessive exposition
        # - Talking heads (no stage directions)
        # - Flat emotional arc
        assert len(result.issues) > 0
        assert result.dialogue_authenticity_score < 0.6
