from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class StoryNovelExport(SoftDeleteBusinessMixin, Base):
    """Persisted long-form novel export generated from a Story (e.g. Zhihu-style)."""

    __tablename__ = "story_novel_exports"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    story_business_id = Column(
        String(32),
        nullable=True,
        index=True,
        comment="业务主键：故事 business_id",
    )
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    style = Column(String(32), nullable=False, default="zhihu", comment="输出风格")
    target_words = Column(Integer, nullable=False, comment="目标字数")
    chapter_count = Column(Integer, nullable=True, comment="章节数")
    total_words = Column(Integer, nullable=True, comment="实际字数")
    model = Column(String(128), nullable=True, comment="文本生成模型（原样）")
    temperature = Column(Float, nullable=True, comment="生成温度")

    file_relative_path = Column(String(512), nullable=True, comment="导出文件相对路径")
    content_text = Column(
        Text().with_variant(mysql.LONGTEXT(), "mysql"),
        nullable=False,
        comment="导出内容文本（可能较长）",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    story = relationship("Story", backref="novel_exports")
    task = relationship("Task")
    user = relationship("User")
