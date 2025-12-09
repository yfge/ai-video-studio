"""
测试数据工厂
"""
import factory
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.models.script import Story, Episode, Script, StoryCharacter, ScriptTemplate
from tests.unit.test_database import test_db


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    """基础工厂类"""
    
    class Meta:
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    @classmethod
    def _setup_next_sequence(cls):
        """设置序列"""
        return 1


class UserFactory(BaseFactory):
    """用户工厂"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    hashed_password = factory.LazyFunction(lambda: "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW")  # "secret"
    full_name = factory.LazyAttribute(lambda obj: f"{obj.username.title()} User")
    is_active = True
    is_superuser = False
    created_at = factory.LazyFunction(datetime.utcnow)


class VirtualIPFactory(BaseFactory):
    """虚拟IP工厂"""
    
    class Meta:
        model = VirtualIP
    
    name = factory.Sequence(lambda n: f"VirtualIP{n}")
    description = factory.Faker("text", max_nb_chars=200)
    tags = factory.LazyFunction(lambda: ["tag1", "tag2"])
    background_story = factory.Faker("text", max_nb_chars=500)
    style_prompt = factory.Faker("sentence")
    style_reference_images = factory.LazyFunction(lambda: ["http://example.com/image1.jpg"])
    default_avatar_url = factory.Faker("image_url")
    is_active = True
    is_public = False
    created_at = factory.LazyFunction(datetime.utcnow)


class VirtualIPImageFactory(BaseFactory):
    """虚拟IP图像工厂"""
    
    class Meta:
        model = VirtualIPImage
    
    virtual_ip = factory.SubFactory(VirtualIPFactory)
    filename = factory.Sequence(lambda n: f"image_{n}.jpg")
    original_filename = factory.LazyAttribute(lambda obj: obj.filename)
    file_path = factory.LazyAttribute(lambda obj: f"/uploads/{obj.filename}")
    file_size = factory.Faker("random_int", min=1000, max=1000000)
    mime_type = "image/jpeg"
    category = factory.Faker("random_element", elements=["avatar", "expression", "costume", "scene"])
    subcategory = factory.Faker("word")
    tags = factory.LazyFunction(lambda: ["test", "image"])
    is_default = False
    is_ai_generated = False
    created_at = factory.LazyFunction(datetime.utcnow)


class StoryFactory(BaseFactory):
    """故事工厂"""
    
    class Meta:
        model = Story
    
    title = factory.Faker("sentence", nb_words=4)
    genre = factory.Faker("random_element", elements=["Romance", "Action", "Comedy", "Drama"])
    theme = factory.Faker("sentence", nb_words=6)
    target_audience = factory.Faker("random_element", elements=["Young Adult", "Adult", "Teen"])
    duration_minutes = factory.Faker("random_int", min=60, max=180)
    premise = factory.Faker("text", max_nb_chars=300)
    synopsis = factory.Faker("text", max_nb_chars=500)
    main_conflict = factory.Faker("text", max_nb_chars=200)
    resolution = factory.Faker("text", max_nb_chars=200)
    main_characters = factory.LazyFunction(lambda: [{"name": "Character1", "role": "protagonist"}])
    character_relationships = factory.LazyFunction(lambda: {"Character1": {"Character2": "friend"}})
    setting_time = factory.Faker("random_element", elements=["Modern", "Medieval", "Future"])
    setting_location = factory.Faker("city")
    world_building = factory.Faker("text", max_nb_chars=300)
    generation_prompt = factory.Faker("text", max_nb_chars=200)
    ai_model = "gpt-4"
    generation_params = factory.LazyFunction(lambda: {"temperature": 0.7})
    status = "draft"
    is_public = False
    tags = factory.LazyFunction(lambda: ["test", "story"])
    extra_metadata = factory.LazyFunction(lambda: {"version": "1.0"})
    created_at = factory.LazyFunction(datetime.utcnow)


class EpisodeFactory(BaseFactory):
    """剧集工厂"""
    
    class Meta:
        model = Episode
    
    story = factory.SubFactory(StoryFactory)
    episode_number = factory.Sequence(lambda n: n)
    title = factory.Faker("sentence", nb_words=3)
    summary = factory.Faker("text", max_nb_chars=300)
    plot_points = factory.LazyFunction(
        lambda: [{"order": 1, "description": "Opening scene"}]
    )
    character_arcs = factory.LazyFunction(lambda: {"Character1": "Development arc"})
    conflicts = factory.LazyFunction(lambda: ["Conflict A", "Conflict B"])
    duration_minutes = factory.Faker("random_int", min=5, max=30)
    scene_count = factory.Faker("random_int", min=3, max=10)
    generation_prompt = factory.Faker("text", max_nb_chars=200)
    ai_model = "gpt-4"
    generation_params = factory.LazyFunction(lambda: {"temperature": 0.7})
    status = "draft"
    tags = factory.LazyFunction(lambda: ["test", "episode"])
    extra_metadata = factory.LazyFunction(lambda: {"version": "1.0"})
    created_at = factory.LazyFunction(datetime.utcnow)


class ScriptFactory(BaseFactory):
    """剧本工厂"""
    
    class Meta:
        model = Script
    
    episode = factory.SubFactory(EpisodeFactory)
    title = factory.Faker("sentence", nb_words=3)
    content = factory.Faker("text", max_nb_chars=1000)
    scenes = factory.LazyFunction(
        lambda: [
            {
                "scene_number": 1,
                "slug_line": "INT. ROOM - DAY",
                "summary": "Opening conversation",
            }
        ]
    )
    dialogues = factory.LazyFunction(
        lambda: [
            {"scene_number": 1, "character": "Character1", "content": "Hello!"}
        ]
    )
    stage_directions = factory.LazyFunction(
        lambda: [{"scene_number": 1, "direction": "Camera pans across the room."}]
    )
    format_type = "screenplay"
    language = "zh-CN"
    page_count = factory.Faker("random_int", min=1, max=10)
    word_count = factory.Faker("random_int", min=500, max=2000)
    character_count = factory.Faker("random_int", min=2000, max=10000)
    generation_prompt = factory.Faker("text", max_nb_chars=200)
    ai_model = "gpt-4"
    generation_params = factory.LazyFunction(lambda: {"temperature": 0.7})
    status = "draft"
    version = "1.0"
    tags = factory.LazyFunction(lambda: ["test", "script"])
    extra_metadata = factory.LazyFunction(lambda: {"version": "1.0"})
    created_at = factory.LazyFunction(datetime.utcnow)


class StoryCharacterFactory(BaseFactory):
    """故事角色工厂"""
    
    class Meta:
        model = StoryCharacter
    
    story = factory.SubFactory(StoryFactory)
    virtual_ip = factory.SubFactory(VirtualIPFactory)
    character_name = factory.Faker("first_name")
    role_type = factory.Faker(
        "random_element", elements=["protagonist", "antagonist", "supporting"]
    )
    importance = factory.Faker("random_int", min=1, max=5)
    personality = factory.Faker("text", max_nb_chars=200)
    background = factory.Faker("text", max_nb_chars=200)
    motivation = factory.Faker("text", max_nb_chars=200)
    character_arc = factory.Faker("text", max_nb_chars=200)
    relationships = factory.LazyFunction(lambda: {"Character2": "ally"})
    created_at = factory.LazyFunction(datetime.utcnow)


class ScriptTemplateFactory(BaseFactory):
    """剧本模板工厂"""
    
    class Meta:
        model = ScriptTemplate
    
    name = factory.Sequence(lambda n: f"Template{n}")
    category = factory.Faker("random_element", elements=["Romance", "Action", "Comedy"])
    template_content = factory.Faker("text", max_nb_chars=500)
    structure = factory.LazyFunction(lambda: {"acts": 3, "scenes_per_act": 3})
    variables = factory.LazyFunction(lambda: {"character_name": "string", "location": "string"})
    usage_count = 0
    is_public = True
    created_at = factory.LazyFunction(datetime.utcnow)


def setup_factories(session: Session):
    """设置工厂会话"""
    UserFactory._meta.sqlalchemy_session = session
    VirtualIPFactory._meta.sqlalchemy_session = session
    VirtualIPImageFactory._meta.sqlalchemy_session = session
    StoryFactory._meta.sqlalchemy_session = session
    EpisodeFactory._meta.sqlalchemy_session = session
    ScriptFactory._meta.sqlalchemy_session = session
    StoryCharacterFactory._meta.sqlalchemy_session = session
    ScriptTemplateFactory._meta.sqlalchemy_session = session


def create_test_data(session: Session):
    """创建测试数据"""
    setup_factories(session)
    
    # 创建用户
    user = UserFactory()
    
    # 创建虚拟IP
    virtual_ip = VirtualIPFactory()
    
    # 创建虚拟IP图像
    image = VirtualIPImageFactory(virtual_ip=virtual_ip)
    
    # 创建故事
    story = StoryFactory()
    
    # 创建故事角色
    character = StoryCharacterFactory(story=story, virtual_ip=virtual_ip)
    
    # 创建剧集
    episode = EpisodeFactory(story=story)
    
    # 创建剧本
    script = ScriptFactory(episode=episode)
    
    # 创建剧本模板
    template = ScriptTemplateFactory()
    
    session.commit()
    
    return {
        'user': user,
        'virtual_ip': virtual_ip,
        'image': image,
        'story': story,
        'character': character,
        'episode': episode,
        'script': script,
        'template': template
    } 
