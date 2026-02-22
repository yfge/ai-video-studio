"""Integration tests for Episode Character Management API.

Tests complete workflows including:
- CRUD operations
- Voice binding integration
- Script generation with auto-creation
- Resource resolution
- Error handling
"""

import pytest
from app.models.episode_character import EpisodeCharacter
from app.models.script import Episode, Story
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db: Session):
    """Create test user."""
    user = User(
        username="test_user_episode_chars",
        email="test_episode_chars@example.com",
        hashed_password="test_hash",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_story(db: Session, test_user: User):
    """Create test story."""
    story = Story(
        user_id=test_user.id,
        title="Test Story for Episode Characters",
        genre="drama",
        story_format="short_video",
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


@pytest.fixture
def test_episode(db: Session, test_story: Story):
    """Create test episode."""
    episode = Episode(
        story_id=test_story.id,
        episode_number=1,
        title="Test Episode",
        summary="Test episode for character integration",
        duration_minutes=5,
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode


@pytest.fixture
def test_virtual_ip(db: Session, test_user: User):
    """Create test VirtualIP."""
    vip = VirtualIP(
        user_id=test_user.id,
        name="Test VirtualIP",
        description="Test virtual IP for episode characters",
        biography="测试性格",
        background_story="测试背景",
        style_prompt="测试外观",
        voice_config={
            "provider": "minimax",
            "voice_id": "male-qn-jingying",
        },
    )
    db.add(vip)
    db.commit()
    db.refresh(vip)
    return vip


class TestEpisodeCharacterCRUD:
    """Test CRUD operations for Episode characters."""

    def test_create_episode_character(
        self,
        client: TestClient,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
        auth_headers: dict,
    ):
        """Test creating an Episode character."""
        response = client.post(
            f"/api/v1/episodes/{test_episode.id}/characters",
            headers=auth_headers,
            json={
                "virtual_ip_id": test_virtual_ip.id,
                "character_name": "快递员",
                "role_type": "temporary",
                "importance": 2,
                "personality": "热情、负责",
                "background": "快递公司员工",
                "appearance_override": "穿着快递制服",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["character_name"] == "快递员"
        assert data["importance"] == 2
        assert data["role_type"] == "temporary"
        assert "business_id" in data
        assert "id" in data

    def test_list_episode_characters(
        self,
        client: TestClient,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
        auth_headers: dict,
    ):
        """Test listing Episode characters with pagination."""
        # Create test characters
        for i in range(3):
            char = EpisodeCharacter(
                episode_id=test_episode.id,
                virtual_ip_id=test_virtual_ip.id,
                character_name=f"角色{i}",
                importance=i + 1,
            )
            db.add(char)
        db.commit()

        response = client.get(
            f"/api/v1/episodes/{test_episode.id}/characters?page=1&page_size=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["has_more"] is False

        # Verify sorted by importance descending
        importances = [item["importance"] for item in data["items"]]
        assert importances == [3, 2, 1]

    def test_get_episode_character(
        self,
        client: TestClient,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
        auth_headers: dict,
    ):
        """Test getting Episode character details."""
        char = EpisodeCharacter(
            episode_id=test_episode.id,
            virtual_ip_id=test_virtual_ip.id,
            character_name="医生",
            importance=3,
        )
        db.add(char)
        db.commit()
        db.refresh(char)

        response = client.get(
            f"/api/v1/episodes/{test_episode.id}/characters/{char.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["character_name"] == "医生"
        assert data["importance"] == 3

    def test_get_character_resources(
        self,
        client: TestClient,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
        auth_headers: dict,
    ):
        """Test getting resolved character resources."""
        char = EpisodeCharacter(
            episode_id=test_episode.id,
            virtual_ip_id=test_virtual_ip.id,
            character_name="护士",
            appearance_override="穿着护士服",
            voice_config_override={
                "provider": "minimax",
                "voice_id": "female-qn-qingse",
            },
        )
        db.add(char)
        db.commit()
        db.refresh(char)

        response = client.get(
            f"/api/v1/episodes/{test_episode.id}/characters/{char.id}/resources",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "护士"
        assert data["resolved_voice_config"]["voice_id"] == "female-qn-qingse"
        assert "穿着护士服" in data["resolved_appearance_prompt"]

    def test_update_episode_character(
        self,
        client: TestClient,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
        auth_headers: dict,
    ):
        """Test updating Episode character."""
        char = EpisodeCharacter(
            episode_id=test_episode.id,
            virtual_ip_id=test_virtual_ip.id,
            character_name="警察",
            importance=1,
        )
        db.add(char)
        db.commit()
        db.refresh(char)

        response = client.put(
            f"/api/v1/episodes/{test_episode.id}/characters/{char.id}",
            headers=auth_headers,
            json={
                "importance": 3,
                "personality": "严肃、正义",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["importance"] == 3
        assert data["personality"] == "严肃、正义"

    def test_delete_episode_character(
        self,
        client: TestClient,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
        auth_headers: dict,
    ):
        """Test soft deleting Episode character."""
        char = EpisodeCharacter(
            episode_id=test_episode.id,
            virtual_ip_id=test_virtual_ip.id,
            character_name="服务员",
        )
        db.add(char)
        db.commit()
        db.refresh(char)

        response = client.delete(
            f"/api/v1/episodes/{test_episode.id}/characters/{char.id}?reason=Test+deletion",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft delete in database
        db.refresh(char)
        assert char.is_deleted is True
        assert char.deleted_reason == "Test deletion"


class TestCharacterExtraction:
    """Test character extraction from script content."""

    def test_extract_from_dialogues(self):
        """Test extracting characters from dialogues."""
        from app.services.script.temporary_character_extractor import (
            extract_temporary_characters,
        )

        script_content = {
            "dialogues": [
                {"character": "快递员", "content": "您的快递到了", "scene_number": 3},
                {"character": "快递员", "content": "请签收", "scene_number": 3},
                {"character": "医生", "content": "病人情况如何？", "scene_number": 5},
            ],
            "stage_directions": [
                {"content": "快递员穿着快递制服走进来", "scene_number": 3},
            ],
        }

        results = extract_temporary_characters(
            script_content=script_content,
            unknown_names=["快递员", "医生"],
        )

        assert len(results) == 2
        assert results[0].character_name == "快递员"
        assert results[0].dialogue_count == 2
        assert results[0].first_appearance_scene == 3
        assert len(results[0].appearance_hints) > 0

    def test_extract_appearance_hints(self):
        """Test extracting appearance hints from stage directions."""
        from app.services.script.temporary_character_extractor import (
            _extract_appearance_hints,
        )

        stage_direction = "穿着快递制服，戴着口罩，背着快递包的年轻人"
        hints = _extract_appearance_hints(stage_direction, "快递员")

        assert "快递制服" in hints
        assert "口罩" in hints
        assert any("快递包" in hint for hint in hints)


class TestBackgroundGeneration:
    """Test AI background generation."""

    @pytest.mark.asyncio
    async def test_generate_with_heuristics(self):
        """Test background generation with heuristics."""
        from app.services.script.character_background_generator import (
            generate_character_background,
        )
        from app.services.script.temporary_character_extractor import (
            TemporaryCharacterInfo,
        )

        char_info = TemporaryCharacterInfo(
            character_name="快递员",
            dialogues=["您的快递到了", "请签收"],
            stage_directions=[],
            scene_appearances=[3],
            first_appearance_scene=3,
            last_appearance_scene=3,
            dialogue_count=2,
            appearance_hints=["快递制服"],
        )

        scene_context = {
            "setting_location": "城市住宅小区",
            "setting_time": "现代",
        }

        result = await generate_character_background(
            character_info=char_info,
            scene_context=scene_context,
            ai_service=None,  # Use heuristics
        )

        assert "personality" in result
        assert "background" in result
        assert "appearance_override" in result
        assert len(result["personality"]) > 0

    def test_heuristic_templates(self):
        """Test pre-defined heuristic templates."""
        from app.services.script.character_background_generator import (
            _generate_with_heuristics,
        )
        from app.services.script.temporary_character_extractor import (
            TemporaryCharacterInfo,
        )

        # Test known character types
        known_types = ["快递员", "医生", "护士", "警察", "服务员", "司机"]

        for char_name in known_types:
            char_info = TemporaryCharacterInfo(
                character_name=char_name,
                dialogues=[],
                stage_directions=[],
                scene_appearances=[1],
                first_appearance_scene=1,
                last_appearance_scene=1,
                dialogue_count=0,
                appearance_hints=[],
            )

            result = _generate_with_heuristics(char_info)

            assert (
                result["personality"] != "普通、友好、礼貌"
            )  # Should use specific template
            assert char_name in result["background"] or "工作" in result["background"]


class TestAutoCreation:
    """Test auto-creation workflow."""

    @pytest.mark.asyncio
    async def test_auto_create_workflow(
        self,
        db: Session,
        test_episode: Episode,
        test_user: User,
    ):
        """Test complete auto-creation workflow."""
        from app.services.script.auto_character_creator import (
            auto_create_episode_characters,
        )

        script_content = {
            "dialogues": [
                {"character": "快递员", "content": "您的快递到了", "scene_number": 3},
                {"character": "快递员", "content": "请签收", "scene_number": 3},
            ],
            "stage_directions": [
                {"content": "穿着快递制服的年轻人走进来", "scene_number": 3},
            ],
            "metadata": {
                "setting_location": "城市住宅小区",
                "setting_time": "现代",
            },
        }

        results = await auto_create_episode_characters(
            db=db,
            episode_id=test_episode.id,
            script_content=script_content,
            unknown_names=["快递员"],
            user_id=test_user.id,
            ai_service=None,  # Use heuristics
        )

        assert len(results) == 1
        assert results[0]["character_name"] == "快递员"
        assert results[0]["needs_customization"] is True
        assert "episode_character_id" in results[0]

        # Verify in database
        char = (
            db.query(EpisodeCharacter)
            .filter(EpisodeCharacter.id == results[0]["episode_character_id"])
            .first()
        )
        assert char is not None
        assert char.character_name == "快递员"

    @pytest.mark.asyncio
    async def test_auto_create_with_default_virtualip(
        self,
        db: Session,
        test_episode: Episode,
        test_user: User,
    ):
        """Test auto-creation creates default VirtualIP if needed."""
        from app.services.script.auto_character_creator import (
            auto_create_episode_characters,
        )

        # Ensure no default VirtualIP exists
        existing_default = (
            db.query(VirtualIP)
            .filter(
                VirtualIP.user_id == test_user.id,
                VirtualIP.name == "临时角色默认形象",
            )
            .first()
        )
        if existing_default:
            db.delete(existing_default)
            db.commit()

        script_content = {
            "dialogues": [
                {"character": "路人", "content": "你好", "scene_number": 1},
            ],
            "stage_directions": [],
            "metadata": {},
        }

        results = await auto_create_episode_characters(
            db=db,
            episode_id=test_episode.id,
            script_content=script_content,
            unknown_names=["路人"],
            user_id=test_user.id,
            ai_service=None,
        )

        assert len(results) == 1

        # Verify default VirtualIP was created
        default_vip = (
            db.query(VirtualIP)
            .filter(
                VirtualIP.user_id == test_user.id,
                VirtualIP.name == "临时角色默认形象",
            )
            .first()
        )
        assert default_vip is not None
        assert default_vip.voice_config["provider"] == "minimax"

    def test_importance_inference(self):
        """Test importance inference from dialogue count."""
        from app.services.script.auto_character_creator import _infer_importance

        assert _infer_importance(15) == 3  # >= 10
        assert _infer_importance(7) == 2  # >= 5
        assert _infer_importance(2) == 1  # < 5


class TestVoiceBinding:
    """Test voice binding integration with Episode characters."""

    def test_get_episode_character_map(
        self,
        db: Session,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
    ):
        """Test getting Episode character voice mapping."""
        from app.services.voice_binding_service import get_episode_character_map

        # Create Episode character with voice override
        char = EpisodeCharacter(
            episode_id=test_episode.id,
            virtual_ip_id=test_virtual_ip.id,
            character_name="播音员",
            voice_config_override={
                "provider": "minimax",
                "voice_id": "female-qn-qingse",
            },
        )
        db.add(char)
        db.commit()

        char_map = get_episode_character_map(db, test_episode.id)

        # Normalized name should be in map
        assert "播音员" in char_map or any("播音员" in key for key in char_map.keys())

    def test_get_combined_character_map(
        self,
        db: Session,
        test_story: Story,
        test_episode: Episode,
        test_virtual_ip: VirtualIP,
    ):
        """Test combined Story + Episode character mapping."""
        from app.services.voice_binding_service import get_combined_character_map

        # Create Episode character
        char = EpisodeCharacter(
            episode_id=test_episode.id,
            virtual_ip_id=test_virtual_ip.id,
            character_name="临时角色",
        )
        db.add(char)
        db.commit()

        combined_map = get_combined_character_map(db, test_story.id, test_episode.id)

        assert isinstance(combined_map, dict)
        # Should include Episode characters


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_auto_create_with_empty_unknown_names(
        self,
        db: Session,
        test_episode: Episode,
        test_user: User,
    ):
        """Test auto-creation with empty unknown_names."""
        from app.services.script.auto_character_creator import (
            auto_create_episode_characters,
        )

        results = await auto_create_episode_characters(
            db=db,
            episode_id=test_episode.id,
            script_content={},
            unknown_names=[],
            user_id=test_user.id,
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_auto_create_with_invalid_script(
        self,
        db: Session,
        test_episode: Episode,
        test_user: User,
    ):
        """Test auto-creation with invalid script content."""
        from app.services.script.auto_character_creator import (
            auto_create_episode_characters,
        )

        results = await auto_create_episode_characters(
            db=db,
            episode_id=test_episode.id,
            script_content=None,  # Invalid
            unknown_names=["测试角色"],
            user_id=test_user.id,
        )

        # Should handle gracefully and return empty
        assert results == []

    def test_character_not_found(
        self,
        client: TestClient,
        test_episode: Episode,
        auth_headers: dict,
    ):
        """Test getting non-existent character."""
        response = client.get(
            f"/api/v1/episodes/{test_episode.id}/characters/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404
