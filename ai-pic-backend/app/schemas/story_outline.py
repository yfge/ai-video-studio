"""Legacy outline fields plus the Story Seed production envelope."""

from typing import Any, Dict, List, Optional

from app.schemas.story_seed import StorySeedModel
from pydantic import BaseModel, Field, model_validator


class CharacterInfo(BaseModel):
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述或定位")
    role: Optional[str] = Field(None, description="角色类型/职责")


class PlotStructure(BaseModel):
    act1: Optional[str] = None
    act2: Optional[str] = None
    act3: Optional[str] = None


class HookBeat(BaseModel):
    beat_type: Optional[str] = Field(
        None, description="钩子类型：hook/reversal/payoff 等"
    )
    description: str = Field(..., description="钩子/反转描述")
    timing: Optional[str] = Field(None, description="出现时机：开场/中段/结尾等")
    intensity: Optional[str] = Field(None, description="强度：low/medium/high")


class HookPlan(BaseModel):
    opening_hook: Optional[str] = Field(None, description="开场钩子设计")
    escalation_plan: Optional[str] = Field(None, description="情绪积压/升级节奏")
    payoff_plan: Optional[str] = Field(None, description="释放/回收节点规划")
    key_reversals: Optional[List[HookBeat]] = Field(None, description="关键反转列表")


class AdSnippet(BaseModel):
    duration_seconds: Optional[int] = Field(None, description="素材时长（秒）")
    hook: str = Field(..., description="素材核心钩子")
    visual_summary: Optional[str] = Field(None, description="素材画面摘要")
    call_to_action: Optional[str] = Field(None, description="引导文案/CTA")


class StoryOutlineModel(BaseModel):
    premise: Optional[str] = Field(None, description="兼容字段：故事前提/核心概念")
    synopsis: Optional[str] = Field(None, description="兼容字段：详细故事概要")
    main_conflict: Optional[str] = Field(None, description="主要冲突")
    resolution: Optional[str] = Field(None, description="解决方案/结局")
    character_relationships: Optional[Dict[str, Any]] = Field(
        None, description="角色关系网"
    )
    main_characters: Optional[List[CharacterInfo]] = Field(None, description="主要角色")
    plot_structure: Optional[PlotStructure] = Field(None, description="三幕式结构")
    core_values: Optional[str] = Field(None, description="核心价值")
    visual_style: Optional[str] = Field(None, description="视觉风格建议")
    selling_points: Optional[List[str]] = Field(None, description="营销卖点")
    market_region: Optional[str] = Field(None, description="目标市场/地区")
    micro_genre: Optional[str] = Field(None, description="微类型/细分题材")
    hook_plan: Optional[HookPlan] = Field(None, description="爽点/钩子节奏规划")
    twist_density: Optional[str] = Field(None, description="反转密度目标")
    cliffhanger_plan: Optional[List[str]] = Field(None, description="悬念/卡点规划")
    ad_snippets: Optional[List[AdSnippet]] = Field(None, description="投流素材建议")
    structured_story_contract: Optional[Dict[str, Any]] = Field(
        None, description="历史生产故事合同，只读兼容"
    )
    story_seed: Optional[StorySeedModel] = Field(
        None, description="轻量故事种子；新 production 生成唯一必需合同"
    )

    @model_validator(mode="after")
    def require_seed_or_legacy_outline(self):
        if self.story_seed is None and not (self.premise and self.synopsis):
            raise ValueError("story_seed or legacy premise/synopsis is required")
        return self
