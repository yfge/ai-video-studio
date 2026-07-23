"""Reusable screenplay template model."""

from datetime import datetime

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text


class ScriptTemplate(SoftDeleteBusinessMixin, Base):
    __tablename__ = "script_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="模板名称")
    category = Column(String(50), comment="模板分类")
    template_content = Column(Text, comment="模板内容")
    structure = Column(JSON, comment="结构定义")
    variables = Column(JSON, comment="变量定义")
    usage_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Float, comment="评分")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_public = Column(Boolean, default=False, comment="是否公开")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
