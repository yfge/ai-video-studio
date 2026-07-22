from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class StoryNovelExport(SoftDeleteBusinessMixin, Base):
    """Persisted novel revision; legacy exports remain readable and downloadable."""

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

    revision_number = Column(
        Integer, nullable=False, default=0, server_default="0", comment="版本号"
    )
    lifecycle_status = Column(
        String(32),
        nullable=False,
        default="legacy",
        server_default="legacy",
        comment="版本生命周期",
    )
    continuity_status = Column(
        String(32),
        nullable=False,
        default="unchecked",
        server_default="unchecked",
        comment="连续性检查状态",
    )
    adaptation_plan_status = Column(
        String(32),
        nullable=False,
        default="empty",
        server_default="empty",
        comment="分集改编计划状态",
    )
    content_hash = Column(String(64), nullable=True, comment="小说内容 SHA-256")
    story_snapshot = Column(JSON, nullable=True, comment="创建版本时的 Story 快照")
    generation_plan = Column(JSON, nullable=True, comment="章节生成计划")
    continuity_ledger = Column(JSON, nullable=True, comment="跨章节连续性账本")
    continuity_report = Column(JSON, nullable=True, comment="连续性检查报告")
    adaptation_plan = Column(JSON, nullable=True, comment="可编辑分集改编计划")
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    file_relative_path = Column(String(512), nullable=True, comment="导出文件相对路径")
    content_text = Column(
        Text().with_variant(mysql.LONGTEXT(), "mysql"),
        nullable=False,
        comment="导出内容文本（可能较长）",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    story = relationship("Story", foreign_keys=[story_id], backref="novel_exports")
    task = relationship("Task")
    user = relationship("User", foreign_keys=[user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    chapters = relationship(
        "StoryNovelChapter",
        back_populates="novel_export",
        cascade="all, delete-orphan",
        order_by="StoryNovelChapter.position",
    )


class StoryNovelChapter(SoftDeleteBusinessMixin, Base):
    """Ordered, editable checkpoint inside a draft novel revision."""

    __tablename__ = "story_novel_chapters"

    id = Column(Integer, primary_key=True, index=True)
    novel_export_id = Column(
        Integer,
        ForeignKey("story_novel_exports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    novel_export_business_id = Column(String(32), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content_text = Column(
        Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=False, default=""
    )
    summary = Column(Text, nullable=True)
    cliffhanger = Column(Text, nullable=True)
    review_status = Column(
        String(32), nullable=False, default="ready", server_default="ready"
    )
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    novel_export = relationship("StoryNovelExport", back_populates="chapters")
