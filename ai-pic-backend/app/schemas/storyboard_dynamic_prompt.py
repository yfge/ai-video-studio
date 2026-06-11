"""Schemas for LLM-generated dynamic storyboard image prompts."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class FramePromptItem(BaseModel):
    """One frame's dynamically generated prompt bundle."""

    frame_index: int = Field(..., description="帧在分镜列表中的索引")
    image_prompt: str = Field(..., description="单帧分镜图生图提示词")
    start_keyframe_prompt: str = Field(..., description="首帧关键帧提示词")
    end_keyframe_prompt: str = Field(..., description="尾帧关键帧提示词")


class DynamicPromptBatch(BaseModel):
    """LLM batch output: prompts for all frames of one scene chunk."""

    frames: List[FramePromptItem]
