from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

BIGINT_PK = BigInteger().with_variant(Integer, "sqlite")


class VirtualIP(SoftDeleteBusinessMixin, Base):
    __tablename__ = "virtual_ips"
    __table_args__ = (
        Index(
            "ux_virtual_ips_user_name_is_deleted",
            "user_id",
            "name",
            "is_deleted",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # 存储标签列表
    background_story = Column(Text, nullable=True)
    biography = Column(Text, nullable=True)  # 人物小传

    # 风格设定
    style_prompt = Column(Text, nullable=True)  # 风格描述，用于AI生成
    style_reference_images = Column(JSON, nullable=True)  # 风格参考图片URL列表
    voice_config = Column(JSON, nullable=True)  # 语音绑定（provider/model/voice_id等）

    # 默认头像
    default_avatar_url = Column(String(256), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # 是否公开

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    images = relationship(
        "VirtualIPImage", back_populates="virtual_ip", cascade="all, delete-orphan"
    )
    environment_links = relationship(
        "VirtualIPEnvironment", back_populates="virtual_ip", cascade="all, delete-orphan"
    )


class VirtualIPImage(SoftDeleteBusinessMixin, Base):
    __tablename__ = "virtual_ip_images"

    id = Column(Integer, primary_key=True, index=True)
    virtual_ip_id = Column(Integer, ForeignKey("virtual_ips.id"), nullable=False)
    virtual_ip_business_id = Column(String(32), index=True, nullable=True)

    # 图像信息
    filename = Column(String(128), nullable=False)
    original_filename = Column(String(128), nullable=False)
    file_path = Column(String(256), nullable=False)
    oss_url = Column(String(512), nullable=True)  # OSS存储URL
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(64), nullable=False)

    # 分类和标签
    category = Column(
        String(32), nullable=False
    )  # avatar, expression, costume, scene, prop等
    subcategory = Column(
        String(64), nullable=True
    )  # 子分类，如表情：happy, sad, angry等
    tags = Column(JSON, nullable=True)  # 图像标签

    # 生成信息
    prompt = Column(Text, nullable=True)  # 生成时的prompt
    ai_model = Column(String(64), nullable=True)  # 使用的AI模型
    generation_params = Column(JSON, nullable=True)  # 生成参数

    # 状态
    is_default = Column(Boolean, default=False)  # 是否为默认图像
    is_public = Column(Boolean, default=True)  # 是否公开

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    virtual_ip = relationship("VirtualIP", back_populates="images")


class VirtualIPEnvironment(SoftDeleteBusinessMixin, Base):
    """Reusable environment asset linked into an IP production pool."""

    __tablename__ = "virtual_ip_environments"
    __table_args__ = (
        Index(
            "ux_virtual_ip_environments_pair_deleted",
            "virtual_ip_id",
            "environment_id",
            "is_deleted",
            unique=True,
        ),
        Index("ix_virtual_ip_environments_user_id", "user_id"),
        Index("ix_virtual_ip_environments_virtual_ip_id", "virtual_ip_id"),
        Index("ix_virtual_ip_environments_environment_id", "environment_id"),
    )

    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    virtual_ip_id = Column(Integer, ForeignKey("virtual_ips.id"), nullable=False)
    virtual_ip_business_id = Column(String(32), index=True, nullable=True)
    environment_id = Column(
        BIGINT_PK, ForeignKey("environments.id"), nullable=False
    )
    environment_business_id = Column(String(32), index=True, nullable=True)
    usage_type = Column(String(32), nullable=False, default="scene_pool")
    usage_note = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    virtual_ip = relationship("VirtualIP", back_populates="environment_links")
    environment = relationship("Environment", back_populates="virtual_ip_links")
