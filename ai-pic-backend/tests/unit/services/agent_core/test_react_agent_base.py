"""Tests for ReAct Agent Base Class."""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from app.services.agent_core.react_agent_base import (
    AgentError,
    AgentErrorType,
    AgentResult,
    AgentState,
    ReactAgentBase,
    RepairStrategy,
)


class TestAgentErrorType:
    """Tests for AgentErrorType enum."""

    def test_all_error_types_defined(self):
        """Verify all expected error types exist."""
        expected = {"syntax", "semantic", "budget", "network", "validation", "unknown"}
        actual = {e.value for e in AgentErrorType}
        assert actual == expected

    def test_error_type_is_string(self):
        """Error types should be string-based."""
        assert AgentErrorType.SYNTAX == "syntax"
        assert AgentErrorType.BUDGET == "budget"


class TestRepairStrategy:
    """Tests for RepairStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies exist."""
        expected = {"retry", "refine", "simplify", "decompose", "fallback", "abort"}
        actual = {s.value for s in RepairStrategy}
        assert actual == expected


class TestAgentError:
    """Tests for AgentError dataclass."""

    def test_create_basic_error(self):
        """Create error with minimal fields."""
        error = AgentError(
            error_type=AgentErrorType.SYNTAX,
            message="Parse failed",
        )
        assert error.error_type == AgentErrorType.SYNTAX
        assert error.message == "Parse failed"
        assert error.recoverable is True
        assert error.suggested_strategy == RepairStrategy.RETRY

    def test_create_error_with_all_fields(self):
        """Create error with all fields specified."""
        error = AgentError(
            error_type=AgentErrorType.BUDGET,
            message="Token limit exceeded",
            details={"tokens": 5000, "limit": 4096},
            recoverable=True,
            suggested_strategy=RepairStrategy.SIMPLIFY,
        )
        assert error.details == {"tokens": 5000, "limit": 4096}
        assert error.suggested_strategy == RepairStrategy.SIMPLIFY

    def test_to_dict(self):
        """Error should serialize to dictionary."""
        error = AgentError(
            error_type=AgentErrorType.NETWORK,
            message="Connection refused",
            details={"host": "api.example.com"},
        )
        result = error.to_dict()
        assert result["error_type"] == "network"
        assert result["message"] == "Connection refused"
        assert result["recoverable"] is True
        assert "timestamp" in result

    def test_timestamp_auto_generated(self):
        """Timestamp should be auto-generated."""
        error = AgentError(
            error_type=AgentErrorType.UNKNOWN,
            message="Something went wrong",
        )
        assert error.timestamp is not None
        assert isinstance(error.timestamp, datetime)


class TestAgentState:
    """Tests for AgentState dataclass."""

    def test_initial_state(self):
        """State should initialize with defaults."""
        state = AgentState()
        assert state.attempt == 0
        assert state.max_attempts == 3
        assert state.errors == []
        assert state.intermediate_results == []
        assert state.context == {}
        assert state.completed_at is None

    def test_has_remaining_attempts_true(self):
        """Should return True when attempts remain."""
        state = AgentState(attempt=2, max_attempts=3)
        assert state.has_remaining_attempts is True

    def test_has_remaining_attempts_false(self):
        """Should return False when no attempts remain."""
        state = AgentState(attempt=3, max_attempts=3)
        assert state.has_remaining_attempts is False

    def test_add_error(self):
        """Should track errors."""
        state = AgentState()
        error = AgentError(
            error_type=AgentErrorType.SYNTAX,
            message="Parse error",
        )
        state.add_error(error)
        assert len(state.errors) == 1
        assert state.errors[0].message == "Parse error"

    def test_add_intermediate(self):
        """Should track intermediate results."""
        state = AgentState()
        state.add_intermediate({"step": 1, "output": "partial"})
        assert len(state.intermediate_results) == 1
        assert state.intermediate_results[0]["step"] == 1

    def test_complete_sets_timestamp(self):
        """Complete should set completed_at."""
        state = AgentState()
        assert state.completed_at is None
        state.complete()
        assert state.completed_at is not None

    def test_duration_seconds(self):
        """Duration should calculate elapsed time."""
        state = AgentState()
        state.complete()
        # Duration should be very small but positive
        assert state.duration_seconds >= 0


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_ok_creates_success(self):
        """ok() should create successful result."""
        result = AgentResult.ok({"output": "data"})
        assert result.success is True
        assert result.data == {"output": "data"}
        assert result.errors == []

    def test_ok_with_metadata(self):
        """ok() should accept metadata."""
        result = AgentResult.ok(
            {"output": "data"},
            metadata={"attempts": 2},
        )
        assert result.metadata == {"attempts": 2}

    def test_fail_creates_failure(self):
        """fail() should create failed result."""
        error = AgentError(
            error_type=AgentErrorType.SYNTAX,
            message="Parse failed",
        )
        result = AgentResult.fail([error])
        assert result.success is False
        assert result.data is None
        assert len(result.errors) == 1

    def test_to_dict(self):
        """Result should serialize to dictionary."""
        result = AgentResult.ok({"output": "test"})
        d = result.to_dict()
        assert d["success"] is True
        assert d["data"] == {"output": "test"}
        assert d["errors"] == []


class ConcreteTestAgent(ReactAgentBase[Dict[str, Any]]):
    """Concrete implementation for testing."""

    def __init__(
        self,
        generate_returns: Any = None,
        generate_raises: Exception = None,
        validation_errors: List[AgentError] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._generate_returns = generate_returns or {"result": "ok"}
        self._generate_raises = generate_raises
        self._validation_errors = validation_errors or []
        self.generate_call_count = 0

    async def _generate(
        self, input_data: Dict[str, Any], state: AgentState
    ) -> Any:
        self.generate_call_count += 1
        if self._generate_raises:
            raise self._generate_raises
        return self._generate_returns

    def _validate(
        self, result: Dict[str, Any], state: AgentState
    ) -> List[AgentError]:
        return self._validation_errors


class TestReactAgentBase:
    """Tests for ReactAgentBase."""

    @pytest.mark.asyncio
    async def test_successful_generation(self):
        """Agent should return success on valid generation."""
        agent = ConcreteTestAgent(generate_returns={"output": "test"})
        result = await agent.run({"input": "data"})
        assert result.success is True
        assert result.data == {"output": "test"}
        assert agent.generate_call_count == 1

    @pytest.mark.asyncio
    async def test_generation_with_retry_on_error(self):
        """Agent should retry on recoverable errors."""
        # First call raises, subsequent calls succeed
        call_count = 0

        class RetryAgent(ReactAgentBase[Dict[str, Any]]):
            async def _generate(self, input_data, state):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ValueError("First attempt failed")
                return {"output": "success"}

        agent = RetryAgent(max_attempts=3)
        result = await agent.run({"input": "data"})
        assert result.success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries_returns_failure(self):
        """Agent should fail after exhausting retries."""
        agent = ConcreteTestAgent(
            generate_raises=ValueError("Always fails"),
            max_attempts=2,
        )
        result = await agent.run({"input": "data"})
        assert result.success is False
        assert len(result.errors) == 2
        assert result.metadata["attempts"] == 2

    @pytest.mark.asyncio
    async def test_validation_errors_trigger_retry(self):
        """Validation errors should trigger repair and retry."""
        call_count = 0
        validation_error = AgentError(
            error_type=AgentErrorType.VALIDATION,
            message="Invalid output",
            recoverable=True,
        )

        class ValidationAgent(ReactAgentBase[Dict[str, Any]]):
            async def _generate(self, input_data, state):
                nonlocal call_count
                call_count += 1
                return {"output": "data"}

            def _validate(self, result, state):
                if call_count == 1:
                    return [validation_error]
                return []

        agent = ValidationAgent(max_attempts=3)
        result = await agent.run({"input": "data"})
        assert result.success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_custom_validator_called(self):
        """Custom validators should be called."""
        validator_called = False

        def custom_validator(result: Dict[str, Any]) -> List[AgentError]:
            nonlocal validator_called
            validator_called = True
            return []

        agent = ConcreteTestAgent()
        agent.add_validator(custom_validator)
        await agent.run({"input": "data"})
        assert validator_called is True

    @pytest.mark.asyncio
    async def test_parse_result_handles_dict(self):
        """Parser should pass through dicts."""
        agent = ConcreteTestAgent(generate_returns={"key": "value"})
        result = await agent.run({"input": "data"})
        assert result.data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_parse_result_handles_json_string(self):
        """Parser should extract JSON from string."""
        json_str = '```json\n{"parsed": true}\n```'
        agent = ConcreteTestAgent(generate_returns=json_str)
        result = await agent.run({"input": "data"})
        assert result.data == {"parsed": True}

    @pytest.mark.asyncio
    async def test_parse_failure_triggers_retry(self):
        """Parse failure should trigger retry."""
        call_count = 0

        class ParseFailAgent(ReactAgentBase[Dict[str, Any]]):
            async def _generate(self, input_data, state):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return "not valid json {"
                return {"valid": "json"}

        agent = ParseFailAgent(max_attempts=3)
        result = await agent.run({"input": "data"})
        assert result.success is True
        assert call_count == 2

    def test_default_repair_strategies(self):
        """Default strategies should be configured."""
        agent = ConcreteTestAgent()
        assert agent.repair_strategies[AgentErrorType.SYNTAX] == RepairStrategy.REFINE
        assert agent.repair_strategies[AgentErrorType.BUDGET] == RepairStrategy.SIMPLIFY
        assert agent.repair_strategies[AgentErrorType.NETWORK] == RepairStrategy.RETRY

    def test_custom_repair_strategies(self):
        """Custom strategies should override defaults."""
        custom = {AgentErrorType.SYNTAX: RepairStrategy.ABORT}
        agent = ConcreteTestAgent(repair_strategies=custom)
        assert agent.repair_strategies[AgentErrorType.SYNTAX] == RepairStrategy.ABORT


class TestErrorClassification:
    """Tests for error classification."""

    def test_classify_json_error(self):
        """JSON errors should be classified as SYNTAX."""
        agent = ConcreteTestAgent()
        error = agent._classify_error(ValueError("JSON decode error"))
        assert error.error_type == AgentErrorType.SYNTAX

    def test_classify_token_limit_error(self):
        """Token limit errors should be classified as BUDGET."""
        agent = ConcreteTestAgent()
        error = agent._classify_error(ValueError("Token limit exceeded"))
        assert error.error_type == AgentErrorType.BUDGET
        assert error.suggested_strategy == RepairStrategy.SIMPLIFY

    def test_classify_network_error(self):
        """Network errors should be classified as NETWORK."""
        agent = ConcreteTestAgent()
        error = agent._classify_error(ConnectionError("Connection refused"))
        assert error.error_type == AgentErrorType.NETWORK

    def test_classify_unknown_error(self):
        """Unknown errors should be classified as UNKNOWN."""
        agent = ConcreteTestAgent()
        error = agent._classify_error(RuntimeError("Something weird"))
        assert error.error_type == AgentErrorType.UNKNOWN


class TestRepairStrategies:
    """Tests for repair strategy application."""

    @pytest.mark.asyncio
    async def test_refine_adds_error_feedback(self):
        """Refine strategy should add error feedback to input."""
        agent = ConcreteTestAgent()
        error = AgentError(
            error_type=AgentErrorType.SYNTAX,
            message="Invalid JSON",
        )
        state = AgentState()
        refined = agent._refine_input({"original": "data"}, error, state)
        assert refined["_error_feedback"] == "Invalid JSON"
        assert refined["_error_type"] == "syntax"
        assert refined["original"] == "data"

    @pytest.mark.asyncio
    async def test_simplify_returns_input_by_default(self):
        """Default simplify should return input unchanged."""
        agent = ConcreteTestAgent()
        state = AgentState()
        result = agent._simplify_input({"data": "test"}, state)
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_decompose_returns_input_by_default(self):
        """Default decompose should return input unchanged."""
        agent = ConcreteTestAgent()
        state = AgentState()
        result = agent._decompose_input({"data": "test"}, state)
        assert result == {"data": "test"}
