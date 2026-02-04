from datetime import datetime

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class Story(SoftDeleteBusinessMixin, Base):
    """故事概要模型"""

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="所属用户ID"
    )
    title = Column(String(255), nullable=False, comment="故事标题")
    story_format = Column(
        String(32),
        nullable=False,
        default="short_drama",
        comment="故事形态：short_drama/tv_series/film",
    )
    genre = Column(String(50), nullable=False, comment="故事类型")
    theme = Column(String(255), comment="故事主题")
    target_audience = Column(String(100), comment="目标受众")
    duration_minutes = Column(Integer, comment="预计总时长（分钟）")
    default_aspect_ratio = Column(
        String(8),
        nullable=False,
        default="9:16",
        comment="默认画幅：9:16/16:9",
    )

    # 故事内容
    premise = Column(Text, comment="故事前提")
    synopsis = Column(Text, comment="故事概要")
    main_conflict = Column(Text, comment="主要冲突")
    resolution = Column(Text, comment="解决方案")

    # 角色信息
    main_characters = Column(JSON, comment="主要角色列表")
    character_relationships = Column(JSON, comment="角色关系")

    # 设定信息
    setting_time = Column(String(100), comment="时间设定")
    setting_location = Column(String(255), comment="地点设定")
    world_building = Column(Text, comment="世界观设定")

    # AI生成相关
    generation_prompt = Column(Text, comment="生成提示词")
    ai_model = Column(String(50), comment="使用的AI模型")
    generation_params = Column(JSON, comment="生成参数")

    # 状态和元数据
    status = Column(
        String(20), default="draft", comment="状态：draft, approved, published"
    )
    is_public = Column(Boolean, default=False, comment="是否公开")
    tags = Column(JSON, comment="标签列表")
    extra_metadata = Column(JSON, comment="额外元数据")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    episodes = relationship(
        "Episode", back_populates="story", cascade="all, delete-orphan"
    )
    story_characters = relationship(
        "StoryCharacter", back_populates="story", cascade="all, delete-orphan"
    )


class Episode(SoftDeleteBusinessMixin, Base):
    """剧集模型"""

    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=False, comment="故事ID"
    )
    story_business_id = Column(
        String(32), index=True, nullable=True, comment="业务主键：故事 business_id"
    )
    episode_number = Column(Integer, nullable=False, comment="集数")
    title = Column(String(255), nullable=False, comment="剧集标题")

    # 剧集内容
    summary = Column(Text, comment="剧集概要")
    plot_points = Column(JSON, comment="情节要点")
    character_arcs = Column(JSON, comment="角色发展")
    conflicts = Column(JSON, comment="冲突点")

    # 技术信息
    duration_minutes = Column(Integer, comment="预计时长（分钟）")
    scene_count = Column(Integer, comment="场景数量")
    aspect_ratio = Column(
        String(8),
        nullable=True,
        comment="可选画幅覆盖：9:16/16:9（为空则继承 Story.default_aspect_ratio）",
    )

    # AI生成相关
    generation_prompt = Column(Text, comment="生成提示词")
    ai_model = Column(String(50), comment="使用的AI模型")
    generation_params = Column(JSON, comment="生成参数")

    # 状态和元数据
    status = Column(
        String(20), default="draft", comment="状态：draft, approved, published"
    )
    tags = Column(JSON, comment="标签列表")
    extra_metadata = Column(JSON, comment="额外元数据")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    story = relationship("Story", back_populates="episodes")
    scripts = relationship(
        "Script", back_populates="episode", cascade="all, delete-orphan"
    )
    episode_characters = relationship(
        "EpisodeCharacter", back_populates="episode", cascade="all, delete-orphan"
    )


class Script(SoftDeleteBusinessMixin, Base):
    """剧本模型"""

    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(
        Integer, ForeignKey("episodes.id"), nullable=False, comment="剧集ID"
    )
    episode_business_id = Column(
        String(32), index=True, nullable=True, comment="业务主键：剧集 business_id"
    )
    title = Column(String(255), nullable=False, comment="剧本标题")

    # 剧本内容
    content = Column(Text, comment="剧本内容")
    scenes = Column(JSON, comment="场景列表")
    dialogues = Column(JSON, comment="对话列表")
    stage_directions = Column(JSON, comment="舞台指示")

    # 格式信息
    format_type = Column(String(50), default="screenplay", comment="剧本格式类型")
    language = Column(String(10), default="zh-CN", comment="语言")

    # 技术信息
    page_count = Column(Integer, comment="页数")
    word_count = Column(Integer, comment="字数")
    character_count = Column(Integer, comment="字符数")

    # AI生成相关
    generation_prompt = Column(Text, comment="生成提示词")
    ai_model = Column(String(50), comment="使用的AI模型")
    generation_params = Column(JSON, comment="生成参数")

    # 状态和元数据
    status = Column(
        String(20), default="draft", comment="状态：draft, approved, published"
    )
    version = Column(String(20), default="1.0", comment="版本号")
    tags = Column(JSON, comment="标签列表")
    extra_metadata = Column(JSON, comment="额外元数据")
    storyboard_plan = Column(JSON, comment="最新分镜规划")
    storyboard_version = Column(Integer, default=1, comment="分镜版本号")
    storyboard_updated_at = Column(DateTime, comment="分镜最近更新时间")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    episode = relationship("Episode", back_populates="scripts")


class StoryCharacter(SoftDeleteBusinessMixin, Base):
    """故事角色关联模型"""

    __tablename__ = "story_characters"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=False, comment="故事ID"
    )
    story_business_id = Column(
        String(32), index=True, nullable=True, comment="业务主键：故事 business_id"
    )
    virtual_ip_id = Column(
        Integer, ForeignKey("virtual_ips.id"), nullable=False, comment="虚拟IP ID"
    )
    virtual_ip_business_id = Column(
        String(32), index=True, nullable=True, comment="业务主键：虚拟IP business_id"
    )

    # 角色信息
    character_name = Column(String(100), comment="角色名称")
    role_type = Column(
        String(50), comment="角色类型：protagonist, antagonist, supporting"
    )
    importance = Column(Integer, default=1, comment="重要度：1-5")

    # 角色设定
    personality = Column(Text, comment="性格特点")
    background = Column(Text, comment="背景故事")
    motivation = Column(Text, comment="动机")
    character_arc = Column(Text, comment="角色发展弧线")

    # 关系设定
    relationships = Column(JSON, comment="与其他角色的关系")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )

    # 关系
    story = relationship("Story", back_populates="story_characters")
    virtual_ip = relationship("VirtualIP")


class ScriptTemplate(SoftDeleteBusinessMixin, Base):
    """剧本模板模型"""

    __tablename__ = "script_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="模板名称")
    category = Column(String(50), comment="模板分类")

    # 模板内容
    template_content = Column(Text, comment="模板内容")
    structure = Column(JSON, comment="结构定义")
    variables = Column(JSON, comment="变量定义")

    # 使用信息
    usage_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Float, comment="评分")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_public = Column(Boolean, default=False, comment="是否公开")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
