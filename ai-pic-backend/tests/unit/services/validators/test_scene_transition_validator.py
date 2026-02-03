"""Unit tests for SceneTransitionValidator."""

from __future__ import annotations

import pytest

from app.services.validators.scene_transition_validator import (
    SceneInfo,
    SceneTransitionValidator,
    TransitionIssue,
    TransitionIssueType,
    TransitionSeverity,
)


class TestTransitionIssue:
    """Tests for TransitionIssue dataclass."""

    def test_to_dict_basic(self) -> None:
        """Test basic serialization."""
        issue = TransitionIssue(
            issue_type=TransitionIssueType.TIME_DISCONTINUITY,
            severity=TransitionSeverity.WARNING,
            message="Time jump detected",
            from_scene=1,
            to_scene=2,
        )
        result = issue.to_dict()
        assert result["issue_type"] == "time_discontinuity"
        assert result["severity"] == "warning"
        assert result["message"] == "Time jump detected"
        assert result["from_scene"] == 1
        assert result["to_scene"] == 2

    def test_to_dict_full(self) -> None:
        """Test full serialization with all fields."""
        issue = TransitionIssue(
            issue_type=TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY,
            severity=TransitionSeverity.ERROR,
            message="Impossible travel",
            from_scene=3,
            to_scene=4,
            from_location="北京市",
            to_location="上海市",
            affected_characters=["张三"],
            fix_suggestion="添加旅途场景",
        )
        result = issue.to_dict()
        assert result["from_location"] == "北京市"
        assert result["to_location"] == "上海市"
        assert result["affected_characters"] == ["张三"]
        assert result["fix_suggestion"] == "添加旅途场景"


class TestSceneTransitionValidator:
    """Tests for SceneTransitionValidator."""

    @pytest.fixture
    def validator(self) -> SceneTransitionValidator:
        """Create a validator instance."""
        return SceneTransitionValidator()

    def test_normalize_time_morning(self, validator: SceneTransitionValidator) -> None:
        """Test time normalization for morning."""
        assert validator._normalize_time("morning") == "morning"
        assert validator._normalize_time("早上") == "morning"
        assert validator._normalize_time("上午") == "morning"

    def test_normalize_time_night(self, validator: SceneTransitionValidator) -> None:
        """Test time normalization for night."""
        assert validator._normalize_time("night") == "night"
        assert validator._normalize_time("夜晚") == "night"
        assert validator._normalize_time("深夜") == "night"

    def test_normalize_time_unknown(self, validator: SceneTransitionValidator) -> None:
        """Test time normalization for unknown time."""
        assert validator._normalize_time("random") is None
        assert validator._normalize_time(None) is None

    def test_extract_city_chinese(self, validator: SceneTransitionValidator) -> None:
        """Test city extraction from Chinese location."""
        assert validator._extract_city("北京市朝阳区") == "北京"
        assert validator._extract_city("上海市浦东新区") == "上海"
        assert validator._extract_city("广州天河区") == "广州"

    def test_extract_city_unknown(self, validator: SceneTransitionValidator) -> None:
        """Test city extraction for unknown location."""
        assert validator._extract_city("某个小镇") is None
        assert validator._extract_city(None) is None

    def test_check_time_transition_valid(self, validator: SceneTransitionValidator) -> None:
        """Test valid time transitions."""
        from_scene = SceneInfo(scene_number=1, time_of_day="早上")
        to_scene = SceneInfo(scene_number=2, time_of_day="中午")
        issue = validator._check_time_transition(from_scene, to_scene)
        assert issue is None

    def test_check_time_transition_invalid(self, validator: SceneTransitionValidator) -> None:
        """Test invalid time transition (afternoon to morning)."""
        from_scene = SceneInfo(scene_number=1, time_of_day="下午")
        to_scene = SceneInfo(scene_number=2, time_of_day="早上")
        issue = validator._check_time_transition(from_scene, to_scene)
        assert issue is not None
        assert issue.issue_type == TransitionIssueType.TIME_DISCONTINUITY
        assert issue.severity == TransitionSeverity.WARNING

    def test_check_time_transition_night_to_dawn_valid(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test valid night to dawn transition."""
        from_scene = SceneInfo(scene_number=1, time_of_day="夜晚")
        to_scene = SceneInfo(scene_number=2, time_of_day="黎明")
        issue = validator._check_time_transition(from_scene, to_scene)
        assert issue is None

    def test_check_geographic_transition_same_city(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test transition within same city."""
        from_scene = SceneInfo(scene_number=1, location="北京市朝阳区")
        to_scene = SceneInfo(scene_number=2, location="北京市海淀区")
        issue = validator._check_geographic_transition(from_scene, to_scene)
        assert issue is None

    def test_check_geographic_transition_different_city_error(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test transition between different cities with same time (impossible)."""
        from_scene = SceneInfo(
            scene_number=1, location="北京市朝阳区", time_of_day="早上"
        )
        to_scene = SceneInfo(
            scene_number=2, location="上海市浦东", time_of_day="早上"
        )
        issue = validator._check_geographic_transition(from_scene, to_scene)
        assert issue is not None
        assert issue.issue_type == TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY
        assert issue.severity == TransitionSeverity.ERROR

    def test_check_geographic_transition_different_city_warning(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test transition between different cities with different time (warning)."""
        from_scene = SceneInfo(
            scene_number=1, location="北京市朝阳区", time_of_day="早上"
        )
        to_scene = SceneInfo(
            scene_number=2, location="上海市浦东", time_of_day="傍晚"
        )
        issue = validator._check_geographic_transition(from_scene, to_scene)
        # With enough time difference, it should be OK (5 hours Beijing to Shanghai)
        assert issue is None

    def test_detect_character_state_injured(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test detection of injured state."""
        assert validator._detect_character_state("张三受伤倒地") == "injured"
        assert validator._detect_character_state("He was injured badly") == "injured"

    def test_detect_character_state_unconscious(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test detection of unconscious state."""
        assert validator._detect_character_state("李四昏迷不醒") == "unconscious"
        assert validator._detect_character_state("She passed out") == "unconscious"

    def test_detect_character_state_none(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test no state detected."""
        assert validator._detect_character_state("张三走进房间") is None

    def test_extract_scene_info(self, validator: SceneTransitionValidator) -> None:
        """Test scene info extraction."""
        scene = {
            "scene_number": 1,
            "location": "北京市朝阳区咖啡馆",
            "time_of_day": "下午",
            "dialogues": [
                {"character": "张三", "content": "你好"},
                {"character": "李四", "content": "你好"},
            ],
            "stage_directions": [
                {"content": "张三受伤后慢慢坐下"},
            ],
        }
        info = validator.extract_scene_info(scene)
        assert info.scene_number == 1
        assert info.city == "北京"
        assert info.time_of_day == "下午"
        assert "张三" in info.characters_present
        assert "李四" in info.characters_present
        assert info.character_states.get("张三") == "injured"

    def test_validate_transitions_no_issues(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test validation with no issues."""
        scenes = [
            {
                "scene_number": 1,
                "location": "北京市朝阳区",
                "time_of_day": "早上",
            },
            {
                "scene_number": 2,
                "location": "北京市海淀区",
                "time_of_day": "中午",
            },
        ]
        issues = validator.validate_transitions(scenes)
        assert len(issues) == 0

    def test_validate_transitions_time_issue(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test validation detecting time discontinuity."""
        scenes = [
            {
                "scene_number": 1,
                "location": "办公室",
                "time_of_day": "傍晚",
            },
            {
                "scene_number": 2,
                "location": "办公室",
                "time_of_day": "早上",
            },
        ]
        issues = validator.validate_transitions(scenes)
        assert len(issues) > 0
        assert any(i.issue_type == TransitionIssueType.TIME_DISCONTINUITY for i in issues)

    def test_validate_transitions_geographic_issue(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test validation detecting geographic impossibility."""
        scenes = [
            {
                "scene_number": 1,
                "location": "北京市中心",
                "time_of_day": "下午",
            },
            {
                "scene_number": 2,
                "location": "上海市中心",
                "time_of_day": "下午",
            },
        ]
        issues = validator.validate_transitions(scenes)
        assert len(issues) > 0
        assert any(
            i.issue_type == TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY for i in issues
        )

    def test_validate_transitions_single_scene(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test validation with single scene (no transitions)."""
        scenes = [{"scene_number": 1, "location": "办公室"}]
        issues = validator.validate_transitions(scenes)
        assert len(issues) == 0

    def test_generate_fix_suggestions(
        self, validator: SceneTransitionValidator
    ) -> None:
        """Test fix suggestion generation."""
        issues = [
            TransitionIssue(
                issue_type=TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY,
                severity=TransitionSeverity.ERROR,
                message="地理不可能",
                from_scene=1,
                to_scene=2,
            ),
            TransitionIssue(
                issue_type=TransitionIssueType.TIME_DISCONTINUITY,
                severity=TransitionSeverity.WARNING,
                message="时间跳跃",
                from_scene=2,
                to_scene=3,
            ),
        ]
        suggestions = validator.generate_fix_suggestions(issues)
        assert len(suggestions) == 2
        assert "suggested_actions" in suggestions[0]
        assert len(suggestions[0]["suggested_actions"]) > 0


class TestSceneInfo:
    """Tests for SceneInfo dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        info = SceneInfo(scene_number=1)
        assert info.scene_number == 1
        assert info.location is None
        assert info.city is None
        assert info.time_of_day is None
        assert info.characters_present == []
        assert info.character_states == {}

    def test_with_values(self) -> None:
        """Test with populated values."""
        info = SceneInfo(
            scene_number=3,
            location="上海市",
            city="上海",
            time_of_day="夜晚",
            characters_present=["张三", "李四"],
            character_states={"张三": "injured"},
        )
        assert info.scene_number == 3
        assert info.city == "上海"
        assert "张三" in info.characters_present
        assert info.character_states["张三"] == "injured"
