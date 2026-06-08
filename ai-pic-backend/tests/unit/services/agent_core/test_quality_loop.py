"""Tests for Quality Closed Loop System."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.agent_core.quality_loop import (
    DeterministicValidator,
    FailureMode,
    RepairAttempt,
    RepairMetrics,
    RepairMonitor,
    SemanticValidator,
    TwoLayerValidator,
    ValidationLayer,
    ValidationResult,
)


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_create_passing_result(self):
        """Create a passing validation result."""
        result = ValidationResult(
            passed=True,
            layer=ValidationLayer.DETERMINISTIC,
        )
        assert result.passed is True
        assert result.errors == []

    def test_create_failing_result(self):
        """Create a failing validation result."""
        result = ValidationResult(
            passed=False,
            layer=ValidationLayer.DETERMINISTIC,
            errors=["Error 1", "Error 2"],
            failure_mode=FailureMode.JSON_PARSE,
        )
        assert result.passed is False
        assert len(result.errors) == 2
        assert result.failure_mode == FailureMode.JSON_PARSE

    def test_to_dict(self):
        """Result should serialize to dictionary."""
        result = ValidationResult(
            passed=False,
            layer=ValidationLayer.SEMANTIC,
            errors=["Error"],
            failure_mode=FailureMode.LOGIC_ERROR,
            duration_ms=15.5,
        )
        d = result.to_dict()
        assert d["passed"] is False
        assert d["layer"] == "semantic"
        assert d["failure_mode"] == "logic_error"
        assert d["duration_ms"] == 15.5


class TestDeterministicValidator:
    """Tests for DeterministicValidator."""

    def test_no_rules_passes(self):
        """No rules should pass any data."""
        validator = DeterministicValidator()
        result = validator.validate({"any": "data"})
        assert result.passed is True
        assert result.layer == ValidationLayer.DETERMINISTIC

    def test_single_rule_pass(self):
        """Single passing rule."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: [])  # No errors
        result = validator.validate("data")
        assert result.passed is True

    def test_single_rule_fail(self):
        """Single failing rule."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: ["Missing required field"])
        result = validator.validate({})
        assert result.passed is False
        assert "Missing required field" in result.errors

    def test_multiple_rules(self):
        """Multiple rules accumulate errors."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: ["Error 1"])
        validator.add_rule(lambda x: ["Error 2", "Error 3"])
        result = validator.validate({})
        assert result.passed is False
        assert len(result.errors) == 3

    def test_rule_exception_handled(self):
        """Exceptions in rules are handled."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: (_ for _ in ()).throw(ValueError("Boom")))
        result = validator.validate({})
        assert result.passed is False
        assert any("Rule execution error" in e for e in result.errors)

    def test_failure_mode_classification_json(self):
        """Should classify JSON errors."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: ["JSON parse error: unexpected token"])
        result = validator.validate({})
        assert result.failure_mode == FailureMode.JSON_PARSE

    def test_failure_mode_classification_schema(self):
        """Should classify schema errors."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: ["Required field 'name' missing"])
        result = validator.validate({})
        assert result.failure_mode == FailureMode.SCHEMA_VIOLATION

    def test_failure_mode_classification_character(self):
        """Should classify character errors."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: ["角色不一致: 张三性别矛盾"])
        result = validator.validate({})
        assert result.failure_mode == FailureMode.CHARACTER_INCONSISTENCY

    def test_duration_tracked(self):
        """Should track validation duration."""
        validator = DeterministicValidator()
        validator.add_rule(lambda x: [])
        result = validator.validate({})
        assert result.duration_ms >= 0


class TestSemanticValidator:
    """Tests for SemanticValidator."""

    def test_no_checks_passes(self):
        """No checks should pass any data."""
        validator = SemanticValidator()
        result = validator.validate({"data": "test"})
        assert result.passed is True
        assert result.layer == ValidationLayer.SEMANTIC

    def test_single_check_pass(self):
        """Single passing check."""
        validator = SemanticValidator()
        validator.add_check(lambda x: [])
        result = validator.validate("data")
        assert result.passed is True

    def test_single_check_fail(self):
        """Single failing check."""
        validator = SemanticValidator()
        validator.add_check(lambda x: ["Narrative inconsistency detected"])
        result = validator.validate({})
        assert result.passed is False
        assert result.failure_mode == FailureMode.LOGIC_ERROR

    def test_check_exception_as_warning(self):
        """Exceptions in checks become warnings."""
        validator = SemanticValidator()
        validator.add_check(lambda x: (_ for _ in ()).throw(ValueError("Boom")))
        result = validator.validate({})
        # Exception becomes warning, not error
        assert result.passed is True  # No actual errors
        assert any("Semantic check error" in w for w in result.warnings)


class TestTwoLayerValidator:
    """Tests for TwoLayerValidator."""

    def test_both_layers_pass(self):
        """Both layers passing."""
        det = DeterministicValidator()
        sem = SemanticValidator()
        validator = TwoLayerValidator(det, sem)

        results = validator.validate({"data": "test"})
        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_deterministic_fails_skips_semantic(self):
        """Deterministic failure skips semantic by default."""
        det = DeterministicValidator()
        det.add_rule(lambda x: ["Deterministic error"])
        sem = SemanticValidator()
        validator = TwoLayerValidator(det, sem, skip_semantic_on_fast_fail=True)

        results = validator.validate({})
        assert len(results) == 1
        assert results[0].layer == ValidationLayer.DETERMINISTIC

    def test_deterministic_fails_runs_semantic_if_configured(self):
        """Can run semantic even when deterministic fails."""
        det = DeterministicValidator()
        det.add_rule(lambda x: ["Deterministic error"])
        sem = SemanticValidator()
        validator = TwoLayerValidator(det, sem, skip_semantic_on_fast_fail=False)

        results = validator.validate({})
        assert len(results) == 2

    def test_is_valid_convenience(self):
        """is_valid() returns True only if all pass."""
        det = DeterministicValidator()
        sem = SemanticValidator()
        validator = TwoLayerValidator(det, sem)

        assert validator.is_valid({"data": "test"}) is True

        det.add_rule(lambda x: ["Error"])
        assert validator.is_valid({}) is False

    def test_semantic_optional(self):
        """Semantic layer is optional."""
        det = DeterministicValidator()
        validator = TwoLayerValidator(det, semantic=None)

        results = validator.validate({})
        assert len(results) == 1


class TestRepairAttempt:
    """Tests for RepairAttempt."""

    def test_create_attempt(self):
        """Create a repair attempt record."""
        attempt = RepairAttempt(
            timestamp=datetime.now(timezone.utc),
            failure_mode=FailureMode.JSON_PARSE,
            repair_strategy="refine",
            success=True,
            duration_ms=50.0,
            error_before="JSON parse error",
        )
        assert attempt.success is True
        assert attempt.failure_mode == FailureMode.JSON_PARSE


class TestRepairMetrics:
    """Tests for RepairMetrics."""

    def test_empty_metrics(self):
        """Empty metrics should have zero rate."""
        metrics = RepairMetrics()
        assert metrics.success_rate == 0.0

    def test_success_rate_calculation(self):
        """Success rate should calculate correctly."""
        metrics = RepairMetrics(total_attempts=10, successful_repairs=7)
        assert metrics.success_rate == 0.7

    def test_to_dict(self):
        """Metrics should serialize."""
        metrics = RepairMetrics(total_attempts=10, successful_repairs=8)
        d = metrics.to_dict()
        assert d["total_attempts"] == 10
        assert d["success_rate"] == 0.8


class TestRepairMonitor:
    """Tests for RepairMonitor."""

    def test_record_attempt(self):
        """Should record repair attempts."""
        monitor = RepairMonitor()
        monitor.record(
            failure_mode=FailureMode.JSON_PARSE,
            strategy="refine",
            success=True,
            duration_ms=50.0,
            error_before="Parse error",
        )
        metrics = monitor.get_metrics()
        assert metrics.total_attempts == 1
        assert metrics.successful_repairs == 1

    def test_success_rate_calculation(self):
        """Should calculate success rate."""
        monitor = RepairMonitor()
        for _ in range(7):
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=True,
                duration_ms=10.0,
                error_before="Error",
            )
        for _ in range(3):
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=False,
                duration_ms=10.0,
                error_before="Error",
                error_after="Still error",
            )
        assert monitor.get_success_rate() == 0.7

    def test_success_rate_by_failure_mode(self):
        """Should filter by failure mode."""
        monitor = RepairMonitor()
        # JSON errors: 2/3 success
        for success in [True, True, False]:
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=success,
                duration_ms=10.0,
                error_before="Error",
            )
        # Schema errors: 1/2 success
        for success in [True, False]:
            monitor.record(
                failure_mode=FailureMode.SCHEMA_VIOLATION,
                strategy="refine",
                success=success,
                duration_ms=10.0,
                error_before="Error",
            )

        json_rate = monitor.get_success_rate(failure_mode=FailureMode.JSON_PARSE)
        schema_rate = monitor.get_success_rate(
            failure_mode=FailureMode.SCHEMA_VIOLATION
        )

        assert abs(json_rate - 2 / 3) < 0.01
        assert schema_rate == 0.5

    def test_slo_alert_triggered(self):
        """Should trigger alert when SLO breached."""
        alert_callback = MagicMock()
        monitor = RepairMonitor(
            slo_threshold=0.7,
            alert_callback=alert_callback,
        )

        # Record mostly failures
        for _ in range(10):
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=False,
                duration_ms=10.0,
                error_before="Error",
            )

        assert alert_callback.called
        call_args = alert_callback.call_args
        assert call_args[0][0] == "SLO_BREACH"
        assert call_args[0][1]["failure_mode"] == "json_parse"

    def test_alert_cooldown(self):
        """Should not spam alerts during cooldown."""
        alert_callback = MagicMock()
        monitor = RepairMonitor(
            slo_threshold=0.7,
            alert_callback=alert_callback,
        )

        # Record failures multiple times
        for _ in range(5):
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=False,
                duration_ms=10.0,
                error_before="Error",
            )

        # Should only alert once due to cooldown
        assert alert_callback.call_count == 1

    def test_identify_problematic_patterns(self):
        """Should identify patterns with low success."""
        monitor = RepairMonitor(slo_threshold=0.7)

        # Create a problematic failure mode
        for _ in range(10):
            monitor.record(
                failure_mode=FailureMode.LOGIC_ERROR,
                strategy="simplify",
                success=False,
                duration_ms=10.0,
                error_before="Error",
            )

        # Create a healthy failure mode
        for _ in range(10):
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=True,
                duration_ms=10.0,
                error_before="Error",
            )

        problems = monitor.identify_problematic_patterns()
        assert len(problems) > 0
        assert problems[0]["name"] == "logic_error"

    def test_metrics_by_strategy(self):
        """Should track metrics by strategy."""
        monitor = RepairMonitor()

        # Refine strategy: 3/4 success
        for success in [True, True, True, False]:
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=success,
                duration_ms=10.0,
                error_before="Error",
            )

        # Simplify strategy: 1/4 success
        for success in [True, False, False, False]:
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="simplify",
                success=success,
                duration_ms=10.0,
                error_before="Error",
            )

        metrics = monitor.get_metrics()
        assert metrics.by_strategy["refine"]["success"] == 3
        assert metrics.by_strategy["simplify"]["success"] == 1

    def test_window_size_limit(self):
        """Should limit to window size."""
        monitor = RepairMonitor(window_size=10)

        # Add more than window size
        for i in range(25):
            monitor.record(
                failure_mode=FailureMode.JSON_PARSE,
                strategy="refine",
                success=i >= 15,  # Last 10 are successes
                duration_ms=10.0,
                error_before="Error",
            )

        # Window should only see recent attempts
        rate = monitor.get_success_rate()
        assert rate == 1.0  # Last 10 all succeeded


class TestFailureModeEnum:
    """Tests for FailureMode enum."""

    def test_all_modes_defined(self):
        """Verify all expected modes exist."""
        expected = {
            "json_parse",
            "schema_violation",
            "content_constraint",
            "logic_error",
            "character_inconsistency",
            "timeline_error",
            "api_error",
            "unknown",
        }
        actual = {m.value for m in FailureMode}
        assert actual == expected


class TestIntegration:
    """Integration tests for quality loop components."""

    def test_full_validation_pipeline(self):
        """Test complete validation pipeline."""
        # Setup deterministic rules
        det = DeterministicValidator()
        det.add_rule(lambda x: [] if "name" in x else ["Missing name"])
        det.add_rule(lambda x: [] if len(x.get("name", "")) > 0 else ["Name is empty"])

        # Setup semantic checks
        sem = SemanticValidator()
        sem.add_check(lambda x: [] if x.get("valid", True) else ["Semantic error"])

        # Create two-layer validator
        validator = TwoLayerValidator(det, sem)

        # Test passing data
        assert validator.is_valid({"name": "Test", "valid": True})

        # Test failing deterministic
        results = validator.validate({})
        assert not results[0].passed
        assert len(results) == 1  # Semantic skipped

        # Test passing deterministic, failing semantic
        results = validator.validate({"name": "Test", "valid": False})
        assert results[0].passed  # Deterministic passed
        assert not results[1].passed  # Semantic failed

    def test_validation_with_repair_monitoring(self):
        """Test validation integrated with repair monitoring."""
        monitor = RepairMonitor(slo_threshold=0.8)

        det = DeterministicValidator()
        det.add_rule(lambda x: [] if isinstance(x, dict) else ["Not a dict"])

        validator = TwoLayerValidator(det)

        # Simulate validation + repair loop
        test_cases = [
            ({"valid": True}, True),
            ("invalid", False),
            ({"valid": True}, True),
            (123, False),
        ]

        for data, expected_success in test_cases:
            results = validator.validate(data)
            success = all(r.passed for r in results)

            monitor.record(
                failure_mode=(
                    FailureMode.SCHEMA_VIOLATION if not success else FailureMode.UNKNOWN
                ),
                strategy="refine",
                success=success,
                duration_ms=10.0,
                error_before=str(results[0].errors) if not success else "",
            )

        metrics = monitor.get_metrics()
        assert metrics.total_attempts == 4
        assert metrics.success_rate == 0.5
