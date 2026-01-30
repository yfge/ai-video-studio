from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON


class VirtualIP(SoftDeleteBusinessMixin, Base):
    __tablename__ = "virtual_ips"

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
