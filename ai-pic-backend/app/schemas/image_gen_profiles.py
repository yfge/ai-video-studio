from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ImageGenProfileDefaultsResponse(BaseModel):
    steps: int | None = Field(None, description="采样步数（可选）")
    cfg_scale: float | None = Field(None, description="CFG scale（可选）")
    negative_prompt: str | None = Field(None, description="反向提示词（可选）")
    strength: float | None = Field(None, description="图生图强度（可选）")
    image_reference: str | None = Field(None, description="图生图图片参考类型（可选）")
    image_fidelity: float | None = Field(
        None, description="图生图参考强度（可选，0~1）"
    )
    human_fidelity: float | None = Field(
        None, description="图生图面部参考强度（可选，0~1）"
    )


class ImageGenProfileResponse(BaseModel):
    id: str = Field(..., description="profile 标识（用于 generation_profile）")
    label: str = Field(..., description="显示名称")
    description: str | None = Field(None, description="说明")
    defaults: ImageGenProfileDefaultsResponse = Field(..., description="默认参数")


class ImageGenProfilesResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str | None = Field(None, description="推断出的 provider（若可用）")
    model_id: str | None = Field(
        None, description="去掉 provider 前缀后的 model_id（若可用）"
    )
    mode: Literal["text_to_image", "image_to_image"] = Field(
        ..., description="生成模式"
    )
    default_profile_id: str | None = Field(
        None, description="默认 profile id（profiles 为空时为 null）"
    )
    profiles: list[ImageGenProfileResponse] = Field(default_factory=list)
