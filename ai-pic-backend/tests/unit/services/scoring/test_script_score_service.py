"""
Unit tests for ScriptScoreService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.schemas.generation import ScriptScoreDimensions
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.scoring.script_score_service import (
    PASS_DIMENSION_THRESHOLD,
    PASS_OVERALL_THRESHOLD,
    REVIEW_DIMENSION_MIN,
    REVIEW_OVERALL_MIN,
    ScriptScoreService,
)


class TestScriptScoreService:
    """Tests for ScriptScoreService."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        service.ai_manager.generate_text = AsyncMock()
        return service

    @pytest.fixture
    def score_service(self, mock_ai_service):
        """Create a ScriptScoreService instance."""
        return ScriptScoreService(mock_ai_service)

    def test_compute_verdict_pass(self, score_service):
        """Test verdict computation for passing scripts."""
        dimensions = ScriptScoreDimensions(
            conflict_intensity=4.5,
            character_recognizability=4.3,
            cultural_fit=4.5,
            clip_ability=4.3,
            logic_coherence=4.4,
        )
        verdict = score_service._compute_verdict(4.5, dimensions)
        assert verdict == "pass"

    def test_compute_verdict_review_overall(self, score_service):
        """Test verdict for borderline overall score."""
        dimensions = ScriptScoreDimensions(
            conflict_intensity=4.3,
            character_recognizability=4.3,
            cultural_fit=4.3,
            clip_ability=4.3,
            logic_coherence=4.3,
        )
        verdict = score_service._compute_verdict(4.3, dimensions)
        assert verdict == "review"

    def test_compute_verdict_review_dimension(self, score_service):
        """Test verdict when one dimension is borderline."""
        dimensions = ScriptScoreDimensions(
            conflict_intensity=4.5,
            character_recognizability=4.0,  # Borderline
            cultural_fit=4.5,
            clip_ability=4.5,
            logic_coherence=4.5,
        )
        verdict = score_service._compute_verdict(4.4, dimensions)
        assert verdict == "review"

    def test_compute_verdict_rewrite_overall(self, score_service):
        """Test verdict for low overall score."""
        dimensions = ScriptScoreDimensions(
            conflict_intensity=3.0,
            character_recognizability=3.0,
            cultural_fit=3.0,
            clip_ability=3.0,
            logic_coherence=3.0,
        )
        verdict = score_service._compute_verdict(3.0, dimensions)
        assert verdict == "rewrite"

    def test_compute_verdict_rewrite_dimension(self, score_service):
        """Test verdict when one dimension is too low."""
        dimensions = ScriptScoreDimensions(
            conflict_intensity=4.5,
            character_recognizability=2.5,  # Too low
            cultural_fit=4.5,
            clip_ability=4.5,
            logic_coherence=4.5,
        )
        verdict = score_service._compute_verdict(4.1, dimensions)
        assert verdict == "rewrite"

    def test_parse_score_response_valid(self, score_service):
        """Test parsing a valid score response."""
        response = """
        Here is the score:
        ```json
        {
            "overall_score": 4.6,
            "dimension_scores": {
                "conflict_intensity": 4.5,
                "character_recognizability": 4.3,
                "cultural_fit": 4.5,
                "clip_ability": 4.4,
                "logic_coherence": 4.3
            },
            "verdict": "pass",
            "strengths": ["Strong opening hook", "Clear character arcs"],
            "risks": ["Second scene is slow"],
            "rewrite_guidance": [],
            "suggested_ad_hooks": ["15s: Opening betrayal scene"]
        }
        ```
        """
        result = score_service._parse_score_response(response)

        assert result.overall_score == 4.6
        assert result.verdict == "pass"
        assert result.dimension_scores.conflict_intensity == 4.5
        assert len(result.strengths) == 2
        assert len(result.risks) == 1
        assert len(result.suggested_ad_hooks) == 1

    def test_parse_score_response_missing_overall(self, score_service):
        """Test parsing when overall_score is missing (computed)."""
        response = """
        ```json
        {
            "dimension_scores": {
                "conflict_intensity": 4.0,
                "character_recognizability": 4.0,
                "cultural_fit": 4.0,
                "clip_ability": 4.0,
                "logic_coherence": 4.0
            },
            "strengths": [],
            "risks": [],
            "rewrite_guidance": [],
            "suggested_ad_hooks": []
        }
        ```
        """
        result = score_service._parse_score_response(response)

        # Should compute average: 4.0
        assert result.overall_score == 4.0
        assert result.verdict == "review"

    def test_parse_score_response_invalid_json(self, score_service):
        """Test parsing invalid JSON returns default result."""
        response = "This is not valid JSON"
        result = score_service._parse_score_response(response)

        assert result.overall_score == 3.0
        assert result.verdict == "review"
        assert "评分解析失败" in result.risks[0]

    def test_default_score_result(self, score_service):
        """Test default score result structure."""
        result = score_service._default_score_result()

        assert result.overall_score == 3.0
        assert result.verdict == "review"
        assert result.dimension_scores.conflict_intensity == 3.0
        assert len(result.risks) > 0

    @pytest.mark.asyncio
    async def test_score_script_success(self, score_service, mock_ai_service):
        """Test successful script scoring."""
        mock_ai_service.ai_manager.generate_text.return_value = AIResponse(
            success=True,
            data="""
        ```json
        {
            "overall_score": 4.5,
            "dimension_scores": {
                "conflict_intensity": 4.5,
                "character_recognizability": 4.5,
                "cultural_fit": 4.5,
                "clip_ability": 4.5,
                "logic_coherence": 4.5
            },
            "verdict": "pass",
            "strengths": ["Excellent pacing"],
            "risks": [],
            "rewrite_guidance": [],
            "suggested_ad_hooks": ["15s: Opening scene"]
        }
        ```
        """,
            provider="mock",
            model="mock",
            task_type=AITaskType.SCRIPT_WRITING,
            model_type=AIModelType.TEXT_GENERATION,
        )

        result = await score_service.score_script(
            script_content="Test script content",
            story={"title": "Test Story", "genre": "Drama"},
            episode={"episode_number": 1, "title": "Pilot"},
        )

        assert result.overall_score == 4.5
        assert result.verdict == "pass"
        mock_ai_service.ai_manager.generate_text.assert_called_once()
        prompt = mock_ai_service.ai_manager.generate_text.call_args.kwargs["prompt"]
        assert "总分 >= 4.5" in prompt
        assert "所有维度 >= 4.2" in prompt
        assert "精品线校准锚点" in prompt
        assert "客户撤单倒计时" in prompt
        assert "不要再用“男二动机需补充”" in prompt


class TestScoreThresholds:
    """Tests for score threshold constants."""

    def test_pass_thresholds(self):
        """Test pass threshold values."""
        assert PASS_OVERALL_THRESHOLD == 4.5
        assert PASS_DIMENSION_THRESHOLD == 4.2

    def test_review_thresholds(self):
        """Test review threshold values."""
        assert REVIEW_OVERALL_MIN == 3.5
        assert REVIEW_DIMENSION_MIN == 3.0
