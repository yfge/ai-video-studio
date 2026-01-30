"""
Unit tests for TrafficSheetService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.schemas.generation import TrafficSheet, TrafficSheetAsset
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


class TestTrafficSheetAsset:
    """Tests for TrafficSheetAsset model."""

    def test_asset_required_fields(self):
        """Test asset with required fields only."""
        asset = TrafficSheetAsset(
            asset_id="test_001",
            duration_seconds=15,
            hook_type="reveal",
            source_episode=1,
            key_line="关键台词",
            visual_hook="关键画面",
            cliff_or_cta="立即观看",
        )

        assert asset.asset_id == "test_001"
        assert asset.duration_seconds == 15
        assert asset.shot_list == []
        assert asset.music_reference is None

    def test_asset_all_fields(self):
        """Test asset with all fields."""
        asset = TrafficSheetAsset(
            asset_id="test_002",
            duration_seconds=30,
            market_region="NA",
            micro_genre="Werewolf mate drama",
            hook_type="reunion",
            source_episode=5,
            source_timecode_start="00:02:30",
            source_timecode_end="00:03:00",
            key_line="我终于找到你了",
            visual_hook="狼人变身后相认",
            shot_list=["特写：眼泪", "中景：拥抱", "远景：月光"],
            cliff_or_cta="他们能在一起吗？",
            music_reference="深情BGM",
            compliance_flags=["no_violence"],
        )

        assert asset.duration_seconds == 30
        assert len(asset.shot_list) == 3
        assert asset.compliance_flags == ["no_violence"]


class TestTrafficSheet:
    """Tests for TrafficSheet model."""

    def test_empty_traffic_sheet(self):
        """Test empty traffic sheet."""
        sheet = TrafficSheet()

        assert sheet.episode_id is None
        assert sheet.script_id is None
        assert sheet.assets == []

    def test_traffic_sheet_with_assets(self):
        """Test traffic sheet with assets."""
        assets = [
            TrafficSheetAsset(
                asset_id="a1",
                duration_seconds=15,
                hook_type="betrayal",
                source_episode=1,
                key_line="Test",
                visual_hook="Test",
                cliff_or_cta="Test",
            ),
            TrafficSheetAsset(
                asset_id="a2",
                duration_seconds=30,
                hook_type="reveal",
                source_episode=1,
                key_line="Test 2",
                visual_hook="Test 2",
                cliff_or_cta="Test 2",
            ),
        ]

        sheet = TrafficSheet(
            episode_id=1,
            script_id=10,
            market_region="NA",
            assets=assets,
        )

        assert sheet.episode_id == 1
        assert len(sheet.assets) == 2
        assert sheet.generated_at is not None
