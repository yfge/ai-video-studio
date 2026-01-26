from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, enum.Enum):
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDIT = "image_edit"
    IMAGE_ENHANCEMENT = "image_enhancement"
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
    target_business_id = Column(String(32), nullable=True, index=True, comment="业务目标对象 business_id")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    prompt = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON字符串
    result_file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="tasks") 
