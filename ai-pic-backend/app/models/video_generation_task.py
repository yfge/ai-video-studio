import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin


class VideoGenerationTaskStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"


class VideoGenerationTask(SoftDeleteBusinessMixin, Base):
    __tablename__ = "video_generation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True, index=True)
    frame_index = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    provider = Column(String(64), nullable=False)
    provider_task_id = Column(String(512), nullable=False, index=True)
    model = Column(String(128), nullable=True)
    model_type = Column(String(32), nullable=False)
    prompt = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    generation_metadata = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    status = Column(
        Enum(
            VideoGenerationTaskStatus,
            name="video_generation_task_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=VideoGenerationTaskStatus.PENDING,
        nullable=False,
    )

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_polled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    task = relationship("Task", backref="video_generation_tasks")
    user = relationship("User", backref="video_generation_tasks")
    script = relationship("Script", backref="video_generation_tasks")
