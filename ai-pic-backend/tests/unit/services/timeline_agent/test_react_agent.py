"""Tests for Timeline ReactAgent implementation."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.agent_core import AgentError, AgentErrorType, AgentState
from app.services.timeline_agent.react_agent import TimelineReactAgent
from app.services.timeline_agent.schemas import TimingDecision, TimingPlan


class TestTimelineReactAgent:
    """Tests for TimelineReactAgent."""

    @pytest.fixture
    def mock_service(self):
        """Create mock AI service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        service.ai_manager.generate_text = AsyncMock()
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """Create agent with mock service."""
        return TimelineReactAgent(mock_service)

    @pytest.fixture
    def sample_dialogues(self):
        """Sample dialogue data."""
        return [
            {"character": "张三", "content": "你好", "emotion": "happy"},
            {"character": "李四", "content": "你好啊", "emotion": "calm"},
            {"character": "张三", "content": "最近怎么样？", "emotion": "curious"},
        ]

    @pytest.fixture
    def sample_scene_context(self):
        """Sample scene context."""
        return {
            "scene_id": 1,
            "scene_number": 1,
            "location": "咖啡店",
            "time_of_day": "下午",
        }

    def test_init(self, mock_service):
        """Agent should initialize with service."""
        agent = TimelineReactAgent(mock_service)
        assert agent.service == mock_service
        assert agent.max_attempts == 3  # MAX_REPAIR_ATTEMPTS + 1

    @pytest.mark.asyncio
    async def test_compute_timing_fallback_no_manager(self, mock_service):
        """Should fallback when AI manager unavailable."""
        mock_service.ai_manager = None
        agent = TimelineReactAgent(mock_service)

        result = await agent.compute_timing(
            dialogues=[{"character": "A", "content": "Hello"}],
            stage_directions=[],
            scene_context={"scene_id": 1, "scene_number": 1},
        )

        assert result is not None
        assert result.fallback_used is True

    @pytest.mark.asyncio
    async def test_compute_timing_success(
        self, agent, sample_dialogues, sample_scene_context
    ):
        """Should return timing plan on successful LLM call."""
        # Mock LLM response
        agent.service.ai_manager.generate_text.return_value = MagicMock(
            data='{"timing_decisions": [{"segment_index": 0, "gap_type": "post_dialogue", "duration_ms": 300, "reasoning": "test"}, {"segment_index": 1, "gap_type": "post_dialogue", "duration_ms": 400, "reasoning": "test"}, {"segment_index": 2, "gap_type": "post_dialogue", "duration_ms": 350, "reasoning": "test"}], "overall_rhythm_note": "good rhythm"}',
            provider="openai",
            model="gpt-4",
        )

        result = await agent.compute_timing(
            dialogues=sample_dialogues,
            stage_directions=[],
            scene_context=sample_scene_context,
        )

        assert result is not None
        assert len(result.decisions) == 3
        assert result.fallback_used is False

    @pytest.mark.asyncio
    async def test_compute_timing_uses_fallback_on_parse_error(
        self, agent, sample_dialogues, sample_scene_context
    ):
        """Should fallback on LLM parse error."""
        agent.service.ai_manager.generate_text.return_value = MagicMock(
            data="not valid json {",
            provider="openai",
            model="gpt-4",
        )

        result = await agent.compute_timing(
            dialogues=sample_dialogues,
            stage_directions=[],
            scene_context=sample_scene_context,
        )

        assert result is not None
        assert result.fallback_used is True


class TestParseResult:
    """Tests for result parsing."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return TimelineReactAgent(service)

    def test_parse_valid_json(self, agent):
        """Should parse valid JSON response."""
        raw = '{"timing_decisions": [{"segment_index": 0, "gap_type": "post_dialogue", "duration_ms": 300}]}'
        result = agent._parse_result(raw)
        assert result is not None
        assert len(result.decisions) == 1
        assert result.decisions[0].adjusted_duration_ms == 300

    def test_parse_json_with_markdown(self, agent):
        """Should parse JSON with markdown code block."""
        raw = '```json\n{"timing_decisions": [{"segment_index": 0, "gap_type": "post_dialogue", "duration_ms": 500}]}\n```'
        result = agent._parse_result(raw)
        assert result is not None
        assert result.decisions[0].adjusted_duration_ms == 500

    def test_parse_empty_response(self, agent):
        """Should return None for empty response."""
        assert agent._parse_result("") is None
        assert agent._parse_result(None) is None

    def test_parse_invalid_json(self, agent):
        """Should return None for invalid JSON."""
        assert agent._parse_result("not json") is None
        assert agent._parse_result("{invalid}") is None

    def test_parse_no_decisions(self, agent):
        """Should return None for response without decisions."""
        result = agent._parse_result('{"other_field": "value"}')
        assert result is None


class TestValidation:
    """Tests for timing validation."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return TimelineReactAgent(service)

    @pytest.fixture
    def state(self):
        """Create agent state."""
        return AgentState(context={})

    def test_validate_valid_plan(self, agent, state):
        """Should pass valid timing plan."""
        plan = TimingPlan(
            scene_id=1,
            decisions=[
                TimingDecision(segment_index=0, adjusted_duration_ms=300),
                TimingDecision(segment_index=1, adjusted_duration_ms=400),
                TimingDecision(segment_index=2, adjusted_duration_ms=350),
            ],
            total_gap_ms=1050,
            avg_gap_ms=350,
            rhythm_score=0.7,
        )
        errors = agent._validate(plan, state)
        assert errors == []

    def test_validate_gap_too_short(self, agent, state):
        """Should reject gap below minimum."""
        plan = TimingPlan(
            scene_id=1,
            decisions=[
                TimingDecision(segment_index=0, adjusted_duration_ms=50),  # Too short
            ],
            total_gap_ms=50,
            avg_gap_ms=50,
        )
        errors = agent._validate(plan, state)
        assert len(errors) >= 1
        assert any("too_short" in e.message for e in errors)

    def test_validate_gap_too_long(self, agent, state):
        """Should reject gap above maximum."""
        plan = TimingPlan(
            scene_id=1,
            decisions=[
                TimingDecision(segment_index=0, adjusted_duration_ms=6000),  # Too long
            ],
            total_gap_ms=6000,
            avg_gap_ms=6000,
        )
        errors = agent._validate(plan, state)
        assert len(errors) >= 1
        assert any("too_long" in e.message for e in errors)

    def test_validate_monotonous_rhythm(self, agent, state):
        """Should reject monotonous rhythm."""
        plan = TimingPlan(
            scene_id=1,
            decisions=[
                TimingDecision(segment_index=i, adjusted_duration_ms=300)
                for i in range(5)  # All same duration
            ],
            total_gap_ms=1500,
            avg_gap_ms=300,
        )
        errors = agent._validate(plan, state)
        assert any("monotonous" in e.message for e in errors)

    def test_validate_avg_gap_too_short(self, agent, state):
        """Should reject average gap below minimum."""
        plan = TimingPlan(
            scene_id=1,
            decisions=[
                TimingDecision(segment_index=0, adjusted_duration_ms=100),
                TimingDecision(segment_index=1, adjusted_duration_ms=150),
            ],
            total_gap_ms=250,
            avg_gap_ms=125,  # Below MIN_AVG_GAP_MS (200)
        )
        errors = agent._validate(plan, state)
        assert any("avg_gap_too_short" in e.message for e in errors)


class TestRefineInput:
    """Tests for input refinement."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return TimelineReactAgent(service)

    def test_refine_adds_error_feedback(self, agent):
        """Should add error feedback to input."""
        state = AgentState(
            errors=[
                AgentError(
                    error_type=AgentErrorType.VALIDATION,
                    message="gap_0_too_short",
                )
            ]
        )
        error = state.errors[0]

        refined = agent._refine_input(
            {"dialogues": []},
            error,
            state,
        )

        assert refined["_error_feedback"] == "gap_0_too_short"
        assert refined["_error_type"] == "validation"
        assert "_validation_errors" in refined


class TestFallback:
    """Tests for fallback timing calculation."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return TimelineReactAgent(service)

    def test_fallback_returns_valid_plan(self, agent):
        """Fallback should return valid timing plan."""
        dialogues = [
            {"character": "A", "content": "Hello", "emotion": "happy"},
            {"character": "B", "content": "Hi there", "emotion": "calm"},
        ]
        scene_context = {"scene_id": 1, "scene_number": 1}

        result = agent._compute_fallback(dialogues, scene_context)

        assert result is not None
        assert result.fallback_used is True
        assert len(result.decisions) == 2
        # All gaps should be within valid range
        for d in result.decisions:
            assert 100 <= d.adjusted_duration_ms <= 5000

    def test_fallback_considers_emotions(self, agent):
        """Fallback should vary timing by emotion transitions."""
        dialogues = [
            {"character": "A", "content": "我很生气！", "emotion": "angry"},
            {"character": "A", "content": "算了...", "emotion": "calm"},  # Big shift
        ]
        scene_context = {"scene_id": 1, "scene_number": 1}

        result = agent._compute_fallback(dialogues, scene_context)

        # Angry->Calm transition should have longer pause
        # (This tests the emotion weight is being applied)
        assert result.decisions[1].emotion_factor > 1.0
