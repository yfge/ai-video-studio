"""
简单的模型测试
"""

import pytest
from app.models.script import Episode, Script, Story
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from sqlalchemy.orm import Session


@pytest.mark.unit
def test_create_user(test_db_session: Session):
    """测试创建用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
    )

    test_db_session.add(user)
    test_db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is False


@pytest.mark.unit
def test_create_virtual_ip(test_db_session: Session):
    """测试创建虚拟IP"""
    vip = VirtualIP(
        name="Test IP",
        description="A test virtual IP",
        tags=["test", "virtual", "ip"],
        is_active=True,
    )

    test_db_session.add(vip)
    test_db_session.commit()

    assert vip.id is not None
    assert vip.name == "Test IP"
    assert vip.description == "A test virtual IP"
    assert vip.tags == ["test", "virtual", "ip"]
    assert vip.is_active is True


@pytest.mark.unit
def test_create_virtual_ip_image(test_db_session: Session):
    """测试创建虚拟IP图像"""
    # 先创建虚拟IP
    vip = VirtualIP(name="Test IP", description="A test virtual IP", is_active=True)
    test_db_session.add(vip)
    test_db_session.commit()

    # 创建图像
    image = VirtualIPImage(
        virtual_ip_id=vip.id,
        filename="test.jpg",
        original_filename="test.jpg",
        file_path="/uploads/test.jpg",
        file_size=1024,
        mime_type="image/jpeg",
        category="avatar",
    )

    test_db_session.add(image)
    test_db_session.commit()

    assert image.id is not None
    assert image.virtual_ip_id == vip.id
    assert image.filename == "test.jpg"
    assert image.category == "avatar"

    # 测试关系
    assert image.virtual_ip == vip
    assert image in vip.images


@pytest.mark.unit
def test_create_story(test_db_session: Session):
    """测试创建故事"""
    story = Story(
        title="Test Story",
        genre="Romance",
        premise="A test story premise",
        synopsis="A test story synopsis",
        main_characters=[{"name": "Character1", "role": "protagonist"}],
        character_relationships={"Character1": {"Character2": "friend"}},
        generation_params={"temperature": 0.7},
    )

    test_db_session.add(story)
    test_db_session.commit()

    assert story.id is not None
    assert story.title == "Test Story"
    assert story.genre == "Romance"
    assert story.main_characters == [{"name": "Character1", "role": "protagonist"}]


@pytest.mark.unit
def test_create_episode(test_db_session: Session):
    """测试创建剧集"""
    # 先创建故事
    story = Story(
        title="Test Story",
        genre="Romance",
        premise="A test story premise",
        synopsis="A test story synopsis",
        main_characters=[],
        character_relationships={},
        generation_params={},
    )
    test_db_session.add(story)
    test_db_session.commit()

    # 创建剧集
    episode = Episode(
        story_id=story.id,
        episode_number=1,
        title="Episode 1",
        summary="First episode",
        duration_minutes=15,
        plot_points=[{"point": 1, "description": "Opening scene"}],
        character_arcs={"Character1": "Development arc"},
        conflicts=["Conflict1", "Conflict2"],
        generation_params={"temperature": 0.7},
    )

    test_db_session.add(episode)
    test_db_session.commit()

    assert episode.id is not None
    assert episode.story_id == story.id
    assert episode.episode_number == 1
    assert episode.title == "Episode 1"

    # 测试关系
    assert episode.story == story
    assert episode in story.episodes


@pytest.mark.unit
def test_create_script(test_db_session: Session):
    """测试创建剧本"""
    # 先创建故事和剧集
    story = Story(
        title="Test Story",
        genre="Romance",
        premise="A test story premise",
        synopsis="A test story synopsis",
        main_characters=[],
        character_relationships={},
        generation_params={},
    )
    test_db_session.add(story)
    test_db_session.commit()

    episode = Episode(
        story_id=story.id,
        episode_number=1,
        title="Episode 1",
        summary="First episode",
        duration_minutes=15,
        plot_points=[],
        character_arcs={},
        conflicts=[],
        generation_params={},
    )
    test_db_session.add(episode)
    test_db_session.commit()

    # 创建剧本
    script = Script(
        episode_id=episode.id,
        title="Script 1",
        content="Test script content",
        format_type="screenplay",
        scenes=[{"scene_number": 1, "slug_line": "INT. ROOM - DAY", "summary": "Test"}],
        dialogues=[
            {"scene_number": 1, "character": "Character1", "content": "Hello!"}
        ],
        stage_directions=[{"scene_number": 1, "direction": "Camera pans."}],
        word_count=500,
        character_count=2500,
        generation_params={"temperature": 0.7},
    )

    test_db_session.add(script)
    test_db_session.commit()

    assert script.id is not None
    assert script.episode_id == episode.id
    assert script.title == "Script 1"
    assert script.content == "Test script content"

    # 测试关系
    assert script.episode == episode
    assert script in episode.scripts
