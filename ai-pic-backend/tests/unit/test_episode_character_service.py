"""Unit tests for episode character service."""

import pytest
from unittest.mock import MagicMock
from app.models.episode_character import EpisodeCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.services.episode_character_service import (
    resolve_character_resources,
    get_character_display_name,
)


class TestResolveCharacterResources:
    """Test resource resolution logic."""

    def test_resolve_with_no_overrides(self):
        """Test resource resolution with no overrides uses VirtualIP defaults."""
        # Mock VirtualIP
        virtual_ip = MagicMock(spec=VirtualIP)
        virtual_ip.id = 1
        virtual_ip.name = "快递员模板"
        virtual_ip.style_prompt = "穿着制服"
        virtual_ip.voice_config = {"provider": "minimax", "voice_id": "male_01"}
        virtual_ip.images = []

        # Mock EpisodeCharacter
        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.virtual_ip_id = 1
        character.virtual_ip = virtual_ip
        character.character_name = "快递员"
        character.voice_config_override = None
        character.appearance_override = None

        # Mock DB
        db = MagicMock()

        # Execute
        result = resolve_character_resources(character, db)

        # Assert
        assert result["voice_config"] == {"provider": "minimax", "voice_id": "male_01"}
        assert result["appearance_prompt"] == "穿着制服"
        assert result["display_name"] == "快递员"
        assert result["images"] == []

    def test_resolve_with_voice_override(self):
        """Test voice_config_override replaces VirtualIP default."""
        virtual_ip = MagicMock(spec=VirtualIP)
        virtual_ip.voice_config = {"provider": "minimax", "voice_id": "male_01"}
        virtual_ip.name = "模板"
        virtual_ip.style_prompt = None
        virtual_ip.images = []

        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.virtual_ip_id = 1
        character.virtual_ip = virtual_ip
        character.character_name = "快递员"
        character.voice_config_override = {"provider": "openai", "voice_id": "alloy"}
        character.appearance_override = None

        db = MagicMock()
        result = resolve_character_resources(character, db)

        # Voice override should win
        assert result["voice_config"] == {"provider": "openai", "voice_id": "alloy"}

    def test_resolve_with_appearance_override(self):
        """Test appearance_override merges with VirtualIP.style_prompt."""
        virtual_ip = MagicMock(spec=VirtualIP)
        virtual_ip.style_prompt = "年轻男性"
        virtual_ip.voice_config = None
        virtual_ip.name = "模板"
        virtual_ip.images = []

        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.virtual_ip_id = 1
        character.virtual_ip = virtual_ip
        character.character_name = "快递员"
        character.voice_config_override = None
        character.appearance_override = "穿着快递制服,背着包裹"

        db = MagicMock()
        result = resolve_character_resources(character, db)

        # Should merge both parts
        assert result["appearance_prompt"] == "年轻男性 穿着快递制服,背着包裹"

    def test_resolve_with_images(self):
        """Test image sorting (is_default first, then created_at)."""
        img1 = MagicMock(spec=VirtualIPImage)
        img1.id = 1
        img1.business_id = "img1"
        img1.filename = "default.jpg"
        img1.oss_url = "http://oss.com/default.jpg"
        img1.category = "avatar"
        img1.subcategory = None
        img1.is_default = True
        img1.is_deleted = False
        img1.tags = []
        img1.created_at = "2024-01-02"

        img2 = MagicMock(spec=VirtualIPImage)
        img2.id = 2
        img2.business_id = "img2"
        img2.filename = "alt.jpg"
        img2.oss_url = "http://oss.com/alt.jpg"
        img2.category = "expression"
        img2.subcategory = "happy"
        img2.is_default = False
        img2.is_deleted = False
        img2.tags = ["smile"]
        img2.created_at = "2024-01-01"

        virtual_ip = MagicMock(spec=VirtualIP)
        virtual_ip.images = [img2, img1]  # Intentionally unsorted
        virtual_ip.name = "模板"
        virtual_ip.style_prompt = None
        virtual_ip.voice_config = None

        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.virtual_ip_id = 1
        character.virtual_ip = virtual_ip
        character.character_name = "快递员"
        character.voice_config_override = None
        character.appearance_override = None

        db = MagicMock()
        result = resolve_character_resources(character, db)

        # Default image should be first
        assert len(result["images"]) == 2
        assert result["images"][0]["id"] == 1
        assert result["images"][0]["is_default"] is True
        assert result["images"][1]["id"] == 2

    def test_resolve_with_missing_virtual_ip(self):
        """Test fallback when VirtualIP is missing."""
        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.virtual_ip_id = 999
        character.virtual_ip = None
        character.character_name = "未知角色"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = resolve_character_resources(character, db)

        # Should return fallback values
        assert result["voice_config"] is None
        assert result["images"] == []
        assert result["appearance_prompt"] is None
        assert result["display_name"] == "未知角色"


class TestGetCharacterDisplayName:
    """Test display name resolution."""

    def test_display_name_from_character_name(self):
        """Test display name uses character_name first."""
        virtual_ip = MagicMock(spec=VirtualIP)
        virtual_ip.name = "模板名"

        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.character_name = "快递员"
        character.virtual_ip = virtual_ip

        db = MagicMock()
        result = get_character_display_name(character, db)

        assert result == "快递员"

    def test_display_name_from_virtual_ip(self):
        """Test display name uses VirtualIP.name when character_name is None."""
        virtual_ip = MagicMock(spec=VirtualIP)
        virtual_ip.name = "通用角色"

        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.character_name = None
        character.virtual_ip = virtual_ip

        db = MagicMock()
        result = get_character_display_name(character, db)

        assert result == "通用角色"

    def test_display_name_fallback(self):
        """Test display name fallback when both names are missing."""
        character = MagicMock(spec=EpisodeCharacter)
        character.id = 10
        character.character_name = None
        character.virtual_ip = None
        character.virtual_ip_id = 999

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_character_display_name(character, db)

        assert result == "临时角色10"
