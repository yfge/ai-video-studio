"""
模型单元测试
"""

import pytest
from app.models.script import Episode, Script, Story, StoryCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tests.factories import (
    EpisodeFactory,
    ScriptFactory,
    ScriptTemplateFactory,
    StoryCharacterFactory,
    StoryFactory,
    UserFactory,
    VirtualIPFactory,
    VirtualIPImageFactory,
    setup_factories,
)


@pytest.mark.unit
class TestUserModel:
    """用户模型测试"""

    def test_create_user(self, db_session: Session):
        """测试创建用户"""
        setup_factories(db_session)

        user = UserFactory()

        assert user.id is not None
        assert user.username is not None
        assert user.email is not None
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_username(self, db_session: Session):
        """测试用户名唯一性"""
        setup_factories(db_session)

        user1 = UserFactory(username="testuser")

        with pytest.raises(IntegrityError):
            UserFactory(username="testuser")

    def test_user_unique_email(self, db_session: Session):
        """测试邮箱唯一性"""
        setup_factories(db_session)

        user1 = UserFactory(email="test@example.com")

        with pytest.raises(IntegrityError):
            UserFactory(email="test@example.com")

    def test_user_string_representation(self, db_session: Session):
        """测试用户字符串表示"""
        setup_factories(db_session)

        user = UserFactory(username="testuser")
        assert str(user) == "testuser"


@pytest.mark.unit
class TestVirtualIPModel:
    """虚拟IP模型测试"""

    def test_create_virtual_ip(self, db_session: Session):
        """测试创建虚拟IP"""
        setup_factories(db_session)

        vip = VirtualIPFactory()

        assert vip.id is not None
        assert vip.name is not None
        assert vip.is_active is True
        assert vip.created_at is not None

    def test_virtual_ip_unique_name(self, db_session: Session):
        """测试虚拟IP名称唯一性"""
        setup_factories(db_session)

        vip1 = VirtualIPFactory(name="TestIP")

        with pytest.raises(IntegrityError):
            VirtualIPFactory(name="TestIP")

    def test_virtual_ip_images_relationship(self, db_session: Session):
        """测试虚拟IP图像关系"""
        setup_factories(db_session)

        vip = VirtualIPFactory()
        image1 = VirtualIPImageFactory(virtual_ip=vip)
        image2 = VirtualIPImageFactory(virtual_ip=vip)

        assert len(vip.images) == 2
        assert image1 in vip.images
        assert image2 in vip.images
        assert image1.virtual_ip == vip
        assert image2.virtual_ip == vip

    def test_virtual_ip_json_fields(self, db_session: Session):
        """测试虚拟IP JSON字段"""
        setup_factories(db_session)

        tags = ["tag1", "tag2", "tag3"]
        reference_images = [
            "http://example.com/image1.jpg",
            "http://example.com/image2.jpg",
        ]

        vip = VirtualIPFactory(tags=tags, style_reference_images=reference_images)

        assert vip.tags == tags
        assert vip.style_reference_images == reference_images

    def test_virtual_ip_cascade_delete(self, db_session: Session):
        """测试虚拟IP级联删除"""
        setup_factories(db_session)

        vip = VirtualIPFactory()
        image = VirtualIPImageFactory(virtual_ip=vip)

        vip_id = vip.id
        image_id = image.id

        # 删除虚拟IP
        db_session.delete(vip)
        db_session.commit()

        # 检查图像也被删除
        assert (
            db_session.query(VirtualIP).filter(VirtualIP.id == vip_id).first() is None
        )
        assert (
            db_session.query(VirtualIPImage)
            .filter(VirtualIPImage.id == image_id)
            .first()
            is None
        )


@pytest.mark.unit
class TestVirtualIPImageModel:
    """虚拟IP图像模型测试"""

    def test_create_virtual_ip_image(self, db_session: Session):
        """测试创建虚拟IP图像"""
        setup_factories(db_session)

        image = VirtualIPImageFactory()

        assert image.id is not None
        assert image.filename is not None
        assert image.virtual_ip_id is not None
        assert image.created_at is not None

    def test_virtual_ip_image_categories(self, db_session: Session):
        """测试虚拟IP图像分类"""
        setup_factories(db_session)

        categories = ["avatar", "expression", "costume", "scene", "prop"]

        for category in categories:
            image = VirtualIPImageFactory(category=category)
            assert image.category == category

    def test_virtual_ip_image_json_tags(self, db_session: Session):
        """测试虚拟IP图像JSON标签"""
        setup_factories(db_session)

        tags = ["happy", "portrait", "high-quality"]
        image = VirtualIPImageFactory(tags=tags)

        assert image.tags == tags


@pytest.mark.unit
class TestStoryModel:
    """故事模型测试"""

    def test_create_story(self, db_session: Session):
        """测试创建故事"""
        setup_factories(db_session)

        story = StoryFactory()

        assert story.id is not None
        assert story.title is not None
        assert story.genre is not None
        assert story.created_at is not None

    def test_story_json_fields(self, db_session: Session):
        """测试故事JSON字段"""
        setup_factories(db_session)

        main_characters = [
            {"name": "Character1", "role": "protagonist"},
            {"name": "Character2", "role": "antagonist"},
        ]
        character_relationships = {"Character1": {"Character2": "enemy"}}
        generation_params = {"temperature": 0.7}

        story = StoryFactory(
            main_characters=main_characters,
            character_relationships=character_relationships,
            generation_params=generation_params,
        )

        assert story.main_characters == main_characters
        assert story.character_relationships == character_relationships
        assert story.generation_params == generation_params

    def test_story_episodes_relationship(self, db_session: Session):
        """测试故事剧集关系"""
        setup_factories(db_session)

        story = StoryFactory()
        episode1 = EpisodeFactory(story=story)
        episode2 = EpisodeFactory(story=story)

        assert len(story.episodes) == 2
        assert episode1 in story.episodes
        assert episode2 in story.episodes
        assert episode1.story == story
        assert episode2.story == story

    def test_story_characters_relationship(self, db_session: Session):
        """测试故事角色关系"""
        setup_factories(db_session)

        story = StoryFactory()
        character1 = StoryCharacterFactory(story=story)
        character2 = StoryCharacterFactory(story=story)

        assert len(story.story_characters) == 2
        assert character1 in story.story_characters
        assert character2 in story.story_characters


@pytest.mark.unit
class TestEpisodeModel:
    """剧集模型测试"""

    def test_create_episode(self, db_session: Session):
        """测试创建剧集"""
        setup_factories(db_session)

        episode = EpisodeFactory()

        assert episode.id is not None
        assert episode.title is not None
        assert episode.story_id is not None
        assert episode.episode_number is not None
        assert episode.created_at is not None

    def test_episode_json_fields(self, db_session: Session):
        """测试剧集JSON字段"""
        setup_factories(db_session)

        scene_descriptions = [
            {"scene": 1, "description": "Opening scene"},
            {"scene": 2, "description": "Conflict scene"},
        ]
        character_arcs = {
            "Character1": "Character growth arc",
            "Character2": "Redemption arc",
        }
        key_events = ["Event1", "Event2", "Event3"]
        emotional_beats = ["Happy", "Sad", "Exciting", "Tension"]

        episode = EpisodeFactory(
            scene_descriptions=scene_descriptions,
            character_arcs=character_arcs,
            key_events=key_events,
            emotional_beats=emotional_beats,
        )

        assert episode.scene_descriptions == scene_descriptions
        assert episode.character_arcs == character_arcs
        assert episode.key_events == key_events
        assert episode.emotional_beats == emotional_beats

    def test_episode_scripts_relationship(self, db_session: Session):
        """测试剧集剧本关系"""
        setup_factories(db_session)

        episode = EpisodeFactory()
        script1 = ScriptFactory(episode=episode)
        script2 = ScriptFactory(episode=episode)

        assert len(episode.scripts) == 2
        assert script1 in episode.scripts
        assert script2 in episode.scripts
        assert script1.episode == episode
        assert script2.episode == episode


@pytest.mark.unit
class TestScriptModel:
    """剧本模型测试"""

    def test_create_script(self, db_session: Session):
        """测试创建剧本"""
        setup_factories(db_session)

        script = ScriptFactory()

        assert script.id is not None
        assert script.title is not None
        assert script.episode_id is not None
        assert script.content is not None
        assert script.created_at is not None

    def test_script_json_fields(self, db_session: Session):
        """测试剧本JSON字段"""
        setup_factories(db_session)

        scene_headings = ["INT. ROOM - DAY", "EXT. STREET - NIGHT"]
        character_list = ["Character1", "Character2", "Character3"]
        generation_params = {"temperature": 0.8}

        script = ScriptFactory(
            scene_headings=scene_headings,
            character_list=character_list,
            generation_params=generation_params,
        )

        assert script.scene_headings == scene_headings
        assert script.character_list == character_list
        assert script.generation_params == generation_params

    def test_script_counts(self, db_session: Session):
        """测试剧本计数字段"""
        setup_factories(db_session)

        script = ScriptFactory(
            dialogue_count=25, action_count=15, word_count=1500, character_count=7500
        )

        assert script.dialogue_count == 25
        assert script.action_count == 15
        assert script.word_count == 1500
        assert script.character_count == 7500


@pytest.mark.unit
class TestStoryCharacterModel:
    """故事角色模型测试"""

    def test_create_story_character(self, db_session: Session):
        """测试创建故事角色"""
        setup_factories(db_session)

        character = StoryCharacterFactory()

        assert character.id is not None
        assert character.story_id is not None
        assert character.virtual_ip_id is not None
        assert character.character_name is not None
        assert character.created_at is not None

    def test_story_character_json_fields(self, db_session: Session):
        """测试故事角色JSON字段"""
        setup_factories(db_session)

        personality_traits = ["brave", "kind", "intelligent", "stubborn"]
        relationships = {"Character2": "friend", "Character3": "rival"}

        character = StoryCharacterFactory(
            personality_traits=personality_traits, relationships=relationships
        )

        assert character.personality_traits == personality_traits
        assert character.relationships == relationships

    def test_story_character_relationships(self, db_session: Session):
        """测试故事角色关系"""
        setup_factories(db_session)

        story = StoryFactory()
        virtual_ip = VirtualIPFactory()
        character = StoryCharacterFactory(story=story, virtual_ip=virtual_ip)

        assert character.story == story
        assert character.virtual_ip == virtual_ip
        assert character in story.story_characters


@pytest.mark.unit
class TestScriptTemplateModel:
    """剧本模板模型测试"""

    def test_create_script_template(self, db_session: Session):
        """测试创建剧本模板"""
        setup_factories(db_session)

        template = ScriptTemplateFactory()

        assert template.id is not None
        assert template.name is not None
        assert template.created_at is not None

    def test_script_template_json_fields(self, db_session: Session):
        """测试剧本模板JSON字段"""
        setup_factories(db_session)

        structure = {"acts": 3, "scenes_per_act": 3, "total_scenes": 9}
        variables = {
            "character_name": "string",
            "location": "string",
            "time_period": "string",
        }

        template = ScriptTemplateFactory(structure=structure, variables=variables)

        assert template.structure == structure
        assert template.variables == variables

    def test_script_template_usage_count(self, db_session: Session):
        """测试剧本模板使用计数"""
        setup_factories(db_session)

        template = ScriptTemplateFactory(usage_count=0)

        assert template.usage_count == 0

        # 模拟使用模板
        template.usage_count += 1
        db_session.commit()

        assert template.usage_count == 1


@pytest.mark.unit
class TestModelRelationships:
    """模型关系测试"""

    def test_complete_story_workflow(self, db_session: Session):
        """测试完整的故事工作流"""
        setup_factories(db_session)

        # 创建虚拟IP
        virtual_ip = VirtualIPFactory()

        # 创建故事
        story = StoryFactory()

        # 创建故事角色
        character = StoryCharacterFactory(story=story, virtual_ip=virtual_ip)

        # 创建剧集
        episode = EpisodeFactory(story=story)

        # 创建剧本
        script = ScriptFactory(episode=episode)

        # 验证所有关系
        assert character.story == story
        assert character.virtual_ip == virtual_ip
        assert episode.story == story
        assert script.episode == episode
        assert script.episode.story == story

        # 验证反向关系
        assert character in story.story_characters
        assert episode in story.episodes
        assert script in episode.scripts

    def test_cascade_delete_story(self, db_session: Session):
        """测试故事级联删除"""
        setup_factories(db_session)

        story = StoryFactory()
        character = StoryCharacterFactory(story=story)
        episode = EpisodeFactory(story=story)
        script = ScriptFactory(episode=episode)

        story_id = story.id
        character_id = character.id
        episode_id = episode.id
        script_id = script.id

        # 删除故事
        db_session.delete(story)
        db_session.commit()

        # 检查级联删除
        assert db_session.query(Story).filter(Story.id == story_id).first() is None
        assert (
            db_session.query(StoryCharacter)
            .filter(StoryCharacter.id == character_id)
            .first()
            is None
        )
        assert (
            db_session.query(Episode).filter(Episode.id == episode_id).first() is None
        )
        assert db_session.query(Script).filter(Script.id == script_id).first() is None

    def test_virtual_ip_multiple_stories(self, db_session: Session):
        """测试虚拟IP在多个故事中的使用"""
        setup_factories(db_session)

        virtual_ip = VirtualIPFactory()
        story1 = StoryFactory()
        story2 = StoryFactory()

        character1 = StoryCharacterFactory(story=story1, virtual_ip=virtual_ip)
        character2 = StoryCharacterFactory(story=story2, virtual_ip=virtual_ip)

        # 验证虚拟IP可以在多个故事中使用
        assert character1.virtual_ip == virtual_ip
        assert character2.virtual_ip == virtual_ip
        assert character1.story != character2.story
