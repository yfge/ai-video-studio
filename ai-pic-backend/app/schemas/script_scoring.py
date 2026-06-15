from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScriptScoreDimensions(BaseModel):
    """评分维度，每项 0-5 分"""

    conflict_intensity: float = Field(
        ..., ge=0, le=5, description="冲突强度：冲突是否明确、激烈、持续升级"
    )
    character_recognizability: float = Field(
        ..., ge=0, le=5, description="角色辨识度：角色是否有清晰标签、动机、行为一致性"
    )
    cultural_fit: float = Field(
        ..., ge=0, le=5, description="文化适配：是否符合目标市场的审美与禁忌"
    )
    clip_ability: float = Field(
        ..., ge=0, le=5, description="素材可剪性：每 60 秒内可拆出的投流钩子数"
    )
    logic_coherence: float = Field(
        ..., ge=0, le=5, description="逻辑一致性：情节连贯、无明显漏洞"
    )


class ScriptScoreResult(BaseModel):
    """剧本评分结果"""

    overall_score: float = Field(..., ge=0, le=5, description="总体评分（加权平均）")
    dimension_scores: ScriptScoreDimensions = Field(..., description="各维度评分")
    verdict: str = Field(..., description="判定结果：pass/review/rewrite")
    strengths: List[str] = Field(default_factory=list, description="剧本优势点")
    risks: List[str] = Field(default_factory=list, description="风险点/问题")
    rewrite_guidance: List[str] = Field(
        default_factory=list, description="修订建议（仅当 verdict != pass 时）"
    )
    suggested_ad_hooks: List[str] = Field(
        default_factory=list, description="可提炼的投流钩子建议"
    )


class TrafficSheetAsset(BaseModel):
    """投流表单条素材"""

    asset_id: str = Field(..., description="素材唯一标识")
    duration_seconds: int = Field(..., description="素材时长：15/30/60")
    market_region: Optional[str] = Field(None, description="目标市场")
    micro_genre: Optional[str] = Field(None, description="微类型")
    hook_type: str = Field(
        ...,
        description="钩子类型：betrayal/reveal/revenge/reunion/threat/taboo/power-shift",
    )
    source_episode: int = Field(..., description="来源剧集编号")
    source_timecode_start: Optional[str] = Field(None, description="起始时间码")
    source_timecode_end: Optional[str] = Field(None, description="结束时间码")
    key_line: str = Field(..., description="字幕锚点/核心台词")
    visual_hook: str = Field(..., description="首帧动作/视觉钩子")
    shot_list: List[str] = Field(
        default_factory=list, description="关键镜头列表（1-5 个）"
    )
    cliff_or_cta: str = Field(..., description="卡点/CTA 文案")
    music_reference: Optional[str] = Field(None, description="音乐参考")
    compliance_flags: Optional[List[str]] = Field(None, description="合规标记")


class TrafficSheet(BaseModel):
    """投流表（Traffic Sheet）"""

    episode_id: Optional[int] = Field(None, description="关联剧集 ID")
    script_id: Optional[int] = Field(None, description="关联剧本 ID")
    market_region: Optional[str] = Field(None, description="目标市场")
    micro_genre: Optional[str] = Field(None, description="微类型")
    assets: List[TrafficSheetAsset] = Field(
        default_factory=list, description="素材列表"
    )
    generated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="生成时间"
    )
