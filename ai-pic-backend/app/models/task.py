import enum

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDIT = "image_edit"
    IMAGE_ENHANCEMENT = "image_enhancement"
    STORYBOARD_IMAGE_GENERATION = "storyboard_image_generation"
    VIRTUAL_IP_IMAGE_GENERATION = "virtual_ip_image_generation"
    VIRTUAL_IP_IMAGE_VARIANT_GENERATION = "virtual_ip_image_variant_generation"
    ENVIRONMENT_IMAGE_GENERATION = "environment_image_generation"
    ENVIRONMENT_IMAGE_VARIANT_GENERATION = "environment_image_variant_generation"
    STORY_GENERATION = "story_generation"
    EPISODE_GENERATION = "episode_generation"
    SCRIPT_GENERATION = "script_generation"
    SCRIPT_REVIEW = "script_review"
    DIALOGUE_AUDIO_GENERATION = "dialogue_audio_generation"
    TIMELINE_GENERATION = "timeline_generation"
    TIMELINE_PIPELINE = "timeline_pipeline"
    STORYBOARD_GENERATION = "storyboard_generation"
    VIDEO_GENERATION = "video_generation"
    TEXT_GENERATION = "text_generation"


class Task(SoftDeleteBusinessMixin, Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    target_business_id = Column(
        String(32), nullable=True, index=True, comment="业务目标对象 business_id"
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    prompt = Column(Text, nullable=True)
    parameters = Column(
        Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True
    )  # JSON字符串
    result_file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="tasks")
