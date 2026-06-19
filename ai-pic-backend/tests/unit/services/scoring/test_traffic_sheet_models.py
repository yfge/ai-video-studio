"""
Unit tests for traffic sheet schema models.
"""

from app.schemas.generation import TrafficSheet, TrafficSheetAsset


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
