from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declared_attr


class StoryNovelWorkflowMixin:
    @declared_attr
    def workflow_mode(cls):
        return Column(
            String(32), nullable=False, default="direct", server_default="direct"
        )

    @declared_attr
    def canonical_novel_export_id(cls):
        return Column(
            Integer,
            ForeignKey("story_novel_exports.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )


class EpisodeNovelSourceMixin:
    @declared_attr
    def source_novel_export_id(cls):
        return Column(
            Integer,
            ForeignKey("story_novel_exports.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )

    @declared_attr
    def source_novel_export_business_id(cls):
        return Column(String(32), nullable=True, index=True)

    @declared_attr
    def source_chapter_refs(cls):
        return Column(JSON, nullable=True, comment="审批时固定的章节引用及 hash")
