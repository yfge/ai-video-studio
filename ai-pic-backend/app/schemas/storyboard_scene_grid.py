"""Schemas for scene-level grid storyboard sheets and continuous videos."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SceneGridCell(BaseModel):
    """One panel's metadata inside the grid sheet."""

    panel_index: int = Field(..., description="宫格序号，从1开始")
    title: str = Field(..., description="镜头名称（说明栏标题）")
    caption: str = Field("", description="说明栏文字")


class SceneGridPromptModel(BaseModel):
    """LLM output schema for the grid sheet prompt."""

    sheet_prompt: str = Field(..., description="宫格分镜大图生图提示词")
    cells: List[SceneGridCell]


class SceneGridVideoPromptModel(BaseModel):
    """LLM output schema for the grid-to-video prompt."""

    video_prompt: str = Field(..., description="宫格图转连续成片的视频提示词")


class SceneGridCharacterRef(BaseModel):
    """User-selected character reference for grid generation."""

    virtual_ip_id: Optional[int] = None
    url: Optional[str] = None
    name: Optional[str] = None


class SceneGridSheetRequest(BaseModel):
    """Request schema for generating a scene grid storyboard sheet."""

    scene_number: int = Field(..., description="场景编号")
    grid_size: int = Field(12, description="宫格数量（4/6/9/12/16）")
    model: Optional[str] = Field(None, description="生图模型")
    generation_profile: Optional[str] = None
    style: Optional[str] = Field(None, description="风格")
    aspect_ratio: str = Field("16:9", description="画幅比例")
    character_refs: Optional[List[SceneGridCharacterRef]] = Field(
        None, description="用户选择的人物参考图"
    )
    environment_refs: Optional[List[str]] = Field(
        None, description="用户选择的环境参考图 URL 列表"
    )


class SceneGridVideoRequest(BaseModel):
    """Request schema for generating a continuous video from the grid sheet."""

    scene_number: int = Field(..., description="场景编号")
    model: Optional[str] = Field("seedance-2.0", description="视频模型")
    duration: Optional[int] = Field(
        None, description="目标时长（秒，4-15；不传则按帧时长合计并截断）"
    )
    resolution: Optional[str] = Field("720p", description="分辨率")
    ratio: Optional[str] = Field(None, description="画幅比例")
    generate_audio: Optional[bool] = Field(None, description="是否生成音频")
    prompt: Optional[str] = Field(None, description="自定义视频提示词覆盖")


class SceneGridInfo(BaseModel):
    """Persisted scene grid payload returned to clients."""

    scene_number: int
    status: str = "ready"
    sheet_prompt: Optional[str] = None
    prompt_source: Optional[str] = None
    cells: Optional[List[Dict[str, Any]]] = None
    image_url: Optional[str] = None
    refs_used: Optional[List[Dict[str, Any]]] = None
    video_prompt: Optional[str] = None
    video_url: Optional[str] = None
    video_thumbnail_url: Optional[str] = None
    model: Optional[str] = None
    video_model: Optional[str] = None
    generated_at: Optional[str] = None
    video_generated_at: Optional[str] = None
