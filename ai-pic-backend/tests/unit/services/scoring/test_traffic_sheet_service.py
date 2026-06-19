"""
Unit tests for TrafficSheetService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.scoring.traffic_sheet_service import TrafficSheetService


class TestTrafficSheetService:
    """Tests for TrafficSheetService."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        service = MagicMock()
        service.ai_manager = MagicMock()
        service.ai_manager.generate_text = AsyncMock()
        return service

    @pytest.fixture
    def traffic_service(self, mock_ai_service):
        """Create a TrafficSheetService instance."""
        return TrafficSheetService(mock_ai_service)

    def test_parse_traffic_sheet_response_valid(self, traffic_service):
        """Test parsing a valid traffic sheet response."""
        response = """
        ```json
        {
            "episode_id": 1,
            "script_id": 10,
            "market_region": "NA",
            "micro_genre": "Mafia romance revenge",
            "assets": [
                {
                    "asset_id": "ep1_asset01_15s",
                    "duration_seconds": 15,
                    "market_region": "NA",
                    "micro_genre": "Mafia romance revenge",
                    "hook_type": "betrayal",
                    "source_episode": 1,
                    "source_timecode_start": "00:00:05",
                    "source_timecode_end": "00:00:20",
                    "key_line": "你以为我不知道？",
                    "visual_hook": "女主摔门",
                    "shot_list": ["特写：愤怒眼神", "中景：惊慌"],
                    "cliff_or_cta": "点击观看",
                    "music_reference": "紧张BGM"
                },
                {
                    "asset_id": "ep1_asset02_30s",
                    "duration_seconds": 30,
                    "hook_type": "reveal",
                    "source_episode": 1,
                    "key_line": "真相大白",
                    "visual_hook": "揭露证据",
                    "shot_list": ["近景：证据"],
                    "cliff_or_cta": "继续看"
                }
            ]
        }
        ```
        """
        result = traffic_service._parse_traffic_sheet_response(response)

        assert result.episode_id == 1
        assert result.script_id == 10
        assert result.market_region == "NA"
        assert len(result.assets) == 2
        assert result.assets[0].duration_seconds == 15
        assert result.assets[0].hook_type == "betrayal"
        assert result.assets[1].duration_seconds == 30

    def test_parse_traffic_sheet_response_empty_assets(self, traffic_service):
        """Test parsing response with empty assets."""
        response = """
        ```json
        {
            "assets": []
        }
        ```
        """
        result = traffic_service._parse_traffic_sheet_response(response)
        assert len(result.assets) == 0

    def test_parse_traffic_sheet_response_coerces_numeric_strings(
        self, traffic_service
    ):
        """Test parsing numeric IDs and durations returned as strings."""
        response = """
        ```json
        {
            "episode_id": "174",
            "script_id": "6112",
            "assets": [
                {
                    "asset_id": "ep1_asset01_15s",
                    "duration_seconds": "15",
                    "hook_type": "reveal",
                    "source_episode": "1",
                    "key_line": "看时间戳。",
                    "visual_hook": "AP指向修改日志",
                    "shot_list": ["近景：日志时间戳"],
                    "cliff_or_cta": "继续看谁删了文件"
                }
            ]
        }
        ```
        """

        result = traffic_service._parse_traffic_sheet_response(response)

        assert result.episode_id == 174
        assert result.script_id == 6112
        assert len(result.assets) == 1
        assert result.assets[0].duration_seconds == 15
        assert result.assets[0].source_episode == 1

    def test_parse_traffic_sheet_response_invalid_json(self, traffic_service):
        """Test parsing invalid JSON returns empty traffic sheet."""
        response = "Invalid JSON here"
        result = traffic_service._parse_traffic_sheet_response(
            response,
            episode_id=5,
            script_id=50,
            story={"market_region": "SEA", "micro_genre": "CEO drama"},
        )

        assert result.episode_id == 5
        assert result.script_id == 50
        assert result.market_region == "SEA"
        assert result.micro_genre == "CEO drama"
        assert len(result.assets) == 0

    def test_parse_traffic_sheet_response_with_fallback(self, traffic_service):
        """Test fallback values from story context."""
        response = """
        ```json
        {
            "assets": [
                {
                    "asset_id": "ep1_asset01_15s",
                    "duration_seconds": 15,
                    "hook_type": "revenge",
                    "source_episode": 1,
                    "key_line": "Test line",
                    "visual_hook": "Test visual",
                    "cliff_or_cta": "Test CTA"
                }
            ]
        }
        ```
        """
        result = traffic_service._parse_traffic_sheet_response(
            response,
            story={"market_region": "LATAM", "micro_genre": "Revenge drama"},
        )

        assert result.market_region == "LATAM"
        assert result.micro_genre == "Revenge drama"

    @pytest.mark.asyncio
    async def test_generate_traffic_sheet_success(
        self, traffic_service, mock_ai_service
    ):
        """Test successful traffic sheet generation."""
        mock_ai_service.ai_manager.generate_text.return_value = AIResponse(
            success=True,
            data="""
        ```json
        {
            "assets": [
                {
                    "asset_id": "ep1_asset01_15s",
                    "duration_seconds": 15,
                    "hook_type": "betrayal",
                    "source_episode": 1,
                    "key_line": "你骗了我！",
                    "visual_hook": "摔杯子",
                    "shot_list": ["特写：碎杯"],
                    "cliff_or_cta": "观看完整版"
                }
            ]
        }
        ```
        """,
            provider="mock",
            model="mock",
            task_type=AITaskType.SCRIPT_WRITING,
            model_type=AIModelType.TEXT_GENERATION,
        )

        result = await traffic_service.generate_traffic_sheet(
            script_content="Test script",
            episode_number=1,
            story={"title": "Test", "market_region": "NA"},
        )

        assert len(result.assets) == 1
        assert result.assets[0].duration_seconds == 15
        assert result.assets[0].hook_type == "betrayal"
        mock_ai_service.ai_manager.generate_text.assert_called_once()
