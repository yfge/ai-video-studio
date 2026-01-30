from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StoryNovelExportSummary(BaseModel):
    """Lightweight novel export record used for history listing."""

    id: int
    business_id: str
    task_id: Optional[int] = None

    style: str = Field(..., description="输出风格，如 zhihu")
    target_words: int = Field(..., description="目标字数")
    chapter_count: Optional[int] = Field(None, description="章节数")
    total_words: Optional[int] = Field(None, description="实际字数")
    model: Optional[str] = Field(None, description="生成模型（原样）")
    temperature: Optional[float] = Field(None, description="生成温度")

    file_relative_path: Optional[str] = Field(None, description="导出文件相对路径")
    created_at: datetime

    class Config:
        from_attributes = True


class StoryNovelExportListResponse(BaseModel):
    items: List[StoryNovelExportSummary]
