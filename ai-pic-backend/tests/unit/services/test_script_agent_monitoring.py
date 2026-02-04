"""Unit tests for Script Agent monitoring integration.

Tests the integration of Universal Agent Framework monitoring
capabilities (RepairMonitor, FailurePatternMatcher) into the
ScriptLangGraphAgent.
"""

from unittest.mock import MagicMock

import pytest
from app.services.agent_core import FailureMode, FailurePatternMatcher, RepairMonitor
from app.services.script_agent import ScriptLangGraphAgent


class TestScriptAgentMonitoringInit:
    """Tests for monitoring infrastructure initialization."""

    @pytest.fixture
    def mock_service(self):
        """Create mock AIService."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """Create ScriptLangGraphAgent instance."""
        return ScriptLangGraphAgent(mock_service)

    def test_repair_monitor_initialized(self, agent):
        """RepairMonitor should be initialized with correct SLO."""
        assert hasattr(agent, "_repair_monitor")
        assert isinstance(agent._repair_monitor, RepairMonitor)
        assert agent._repair_monitor.slo_threshold == 0.7

    def test_failure_matcher_initialized(self, agent):
        """FailurePatternMatcher should be initialized."""
        assert hasattr(agent, "_failure_matcher")
        assert isinstance(agent._failure_matcher, FailurePatternMatcher)


class TestFailureModeClassification:
    """Tests for _classify_failure_mode method."""

    @pytest.fixture
    def mock_service(self):
        """Create mock AIService."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """Create ScriptLangGraphAgent instance."""
        return ScriptLangGraphAgent(mock_service)

    def test_duration_error_classified_as_content_constraint(self, agent):
        """Duration-related errors should be CONTENT_CONSTRAINT."""
        error = "时长不足：实际 15.0s < 目标 30s"
        mode = agent._classify_failure_mode(error)
        assert mode == FailureMode.CONTENT_CONSTRAINT

    def test_dialogue_error_classified_as_content_constraint(self, agent):
        """Dialogue-related errors should be CONTENT_CONSTRAINT."""
        error = "对白过短，需要增加内容"
        mode = agent._classify_failure_mode(error)
        assert mode == FailureMode.CONTENT_CONSTRAINT

    def test_character_error_classified_correctly(self, agent):
        """Character-related errors should be CHARACTER_INCONSISTENCY."""
        error = "角色不一致: 张三的台词不符合人设"
        mode = agent._classify_failure_mode(error)
        assert mode == FailureMode.CHARACTER_INCONSISTENCY

    def test_reused_content_classified_as_logic_error(self, agent):
        """Reused/repeated content errors should be LOGIC_ERROR."""
        # Use a clear repetition error without "对白" to avoid content constraint match
        error = "repeated content detected in scene 3"
        mode = agent._classify_failure_mode(error)
        assert mode == FailureMode.LOGIC_ERROR

    def test_json_error_classified_correctly(self, agent):
        """JSON parse errors should be JSON_PARSE via pattern matcher."""
        # This should match the unclosed_json_brace pattern
        error = "Expecting '}' delimiter"
        mode = agent._classify_failure_mode(error)
        assert mode == FailureMode.JSON_PARSE

    def test_unknown_error_returns_unknown(self, agent):
        """Unknown errors should return UNKNOWN."""
        error = "Some completely unrecognized error"
        mode = agent._classify_failure_mode(error)
        assert mode == FailureMode.UNKNOWN


class TestRepairMonitorRecording:
    """Tests for repair attempt recording."""

    @pytest.fixture
    def mock_service(self):
        """Create mock AIService."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """Create ScriptLangGraphAgent instance."""
        return ScriptLangGraphAgent(mock_service)

    def test_repair_monitor_starts_empty(self, agent):
        """RepairMonitor should start with no attempts."""
        metrics = agent._repair_monitor.get_metrics()
        assert metrics.total_attempts == 0
        assert metrics.successful_repairs == 0

    def test_can_record_repair_attempt(self, agent):
        """Should be able to record repair attempts."""
        agent._repair_monitor.record(
            failure_mode=FailureMode.CONTENT_CONSTRAINT,
            strategy="duration_retry",
            success=True,
            duration_ms=50.0,
            error_before="时长不足",
        )
        metrics = agent._repair_monitor.get_metrics()
        assert metrics.total_attempts == 1
        assert metrics.successful_repairs == 1

    def test_success_rate_calculated_correctly(self, agent):
        """Success rate should be calculated correctly."""
        # Record 3 successful, 2 failed
        for _ in range(3):
            agent._repair_monitor.record(
                failure_mode=FailureMode.CONTENT_CONSTRAINT,
                strategy="duration_retry",
                success=True,
                duration_ms=10.0,
                error_before="error",
            )
        for _ in range(2):
            agent._repair_monitor.record(
                failure_mode=FailureMode.CONTENT_CONSTRAINT,
                strategy="duration_retry",
                success=False,
                duration_ms=10.0,
                error_before="error",
            )

        metrics = agent._repair_monitor.get_metrics()
        assert metrics.total_attempts == 5
        assert metrics.success_rate == 0.6

    def test_metrics_tracked_by_failure_mode(self, agent):
        """Metrics should be tracked by failure mode."""
        # Record different failure modes
        agent._repair_monitor.record(
            failure_mode=FailureMode.CONTENT_CONSTRAINT,
            strategy="duration_retry",
            success=True,
            duration_ms=10.0,
            error_before="时长问题",
        )
        agent._repair_monitor.record(
            failure_mode=FailureMode.CHARACTER_INCONSISTENCY,
            strategy="character_fix",
            success=False,
            duration_ms=15.0,
            error_before="角色问题",
        )

        metrics = agent._repair_monitor.get_metrics()
        by_mode = metrics.to_dict()["by_failure_mode"]

        assert "content_constraint" in by_mode
        assert by_mode["content_constraint"]["success"] == 1
        assert "character_inconsistency" in by_mode
        assert by_mode["character_inconsistency"]["success"] == 0


class TestAgentMetricsOutput:
    """Tests for agent_metrics in generation result."""

    @pytest.fixture
    def mock_service(self):
        """Create mock AIService with no AI manager."""
        service = MagicMock()
        service.ai_manager = None
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """Create ScriptLangGraphAgent instance."""
        return ScriptLangGraphAgent(mock_service)

    def test_agent_has_monitoring_attributes(self, agent):
        """Agent should have monitoring attributes for metrics."""
        assert hasattr(agent, "_repair_monitor")
        assert hasattr(agent, "_failure_matcher")

    def test_repair_monitor_provides_metrics(self, agent):
        """RepairMonitor should provide structured metrics."""
        # Simulate some repair attempts
        agent._repair_monitor.record(
            failure_mode=FailureMode.CONTENT_CONSTRAINT,
            strategy="duration_retry",
            success=True,
            duration_ms=25.0,
            error_before="test error",
        )

        metrics = agent._repair_monitor.get_metrics()

        # Check metrics structure
        assert hasattr(metrics, "total_attempts")
        assert hasattr(metrics, "successful_repairs")
        assert hasattr(metrics, "success_rate")
        assert hasattr(metrics, "avg_duration_ms")

        # Check values
        assert metrics.total_attempts == 1
        assert metrics.success_rate == 1.0
        assert metrics.avg_duration_ms == 25.0

    def test_identify_problematic_patterns_works(self, agent):
        """identify_problematic_patterns should return list."""
        # Record many failures for one mode
        for _ in range(10):
            agent._repair_monitor.record(
                failure_mode=FailureMode.LOGIC_ERROR,
                strategy="simplify",
                success=False,
                duration_ms=10.0,
                error_before="repeated error",
            )

        problems = agent._repair_monitor.identify_problematic_patterns()
        assert isinstance(problems, list)
        # With 10 failures and 0 successes, this should be flagged
        assert len(problems) > 0
        assert problems[0]["name"] == "logic_error"


class TestFailurePatternMatcherIntegration:
    """Tests for FailurePatternMatcher integration."""

    @pytest.fixture
    def mock_service(self):
        """Create mock AIService."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """Create ScriptLangGraphAgent instance."""
        return ScriptLangGraphAgent(mock_service)

    def test_failure_matcher_matches_json_errors(self, agent):
        """FailurePatternMatcher should match JSON errors."""
        pattern = agent._failure_matcher.match_first("JSON parse error: expecting '}'")
        assert pattern is not None
        assert "json" in pattern.category.value.lower()

    def test_failure_matcher_provides_repair_hints(self, agent):
        """FailurePatternMatcher should provide repair hints."""
        hints = agent._failure_matcher.get_repair_hints("Missing required field")
        assert len(hints) > 0

    def test_classify_category_works(self, agent):
        """classify_category should return PatternCategory."""
        from app.services.agent_core.failure_patterns import PatternCategory

        # Use an error that matches the unclosed_json_brace pattern
        category = agent._failure_matcher.classify_category("Expecting '}' delimiter")
        assert category is not None
        assert isinstance(category, PatternCategory)
        assert category == PatternCategory.JSON_SYNTAX
