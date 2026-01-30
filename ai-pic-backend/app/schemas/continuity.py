from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ContinuityTimelineItem(BaseModel):
    episode_number: int = Field(..., description="集数（从 1 开始）")
    time_anchor: Optional[str] = Field(
        None, description="时间锚点（同一天/第二天/一周后/具体日期等）"
    )
    location_anchor: Optional[str] = Field(
        None, description="地点锚点（城市/区域/关键主要地点）"
    )
    events: List[str] = Field(default_factory=list, description="关键事件（短句）")
    end_state: Optional[str] = Field(None, description="本集结尾的关键状态（短句）")
    reveals: List[str] = Field(
        default_factory=list, description="本集揭示的信息（短句）"
    )


class ContinuityInfoAcquisitionEvent(BaseModel):
    episode_number: Optional[int] = Field(None, description="集数（若适用）")
    scene_number: Optional[int] = Field(None, description="场景号（若适用）")
    who: str = Field(..., description="谁获得信息（角色名/旁白/观众）")
    what: str = Field(..., description="获得的信息（姓名/身份/事实/动机等）")
    how: str = Field(
        ..., description="获得方式（自报/他人介绍/工牌/手机备注/目击/推断等）"
    )
    evidence: Optional[str] = Field(None, description="证据片段/引用（可选）")


class ContinuityCharacterState(BaseModel):
    status: Optional[str] = Field(None, description="当前状态/处境（短句）")
    goal: Optional[str] = Field(None, description="当前目标（短句）")
    relationships: Dict[str, str] = Field(
        default_factory=dict, description="与他人的关系"
    )
    known_info: List[str] = Field(
        default_factory=list, description="角色已知信息（短句）"
    )
    unknown_info: List[str] = Field(
        default_factory=list, description="角色未知但重要的信息（短句，可为空）"
    )


class ContinuityLedger(BaseModel):
    version: int = Field(1, description="账本版本号")
    facts: List[str] = Field(default_factory=list, description="已确认事实（短句）")
    timeline: List[ContinuityTimelineItem] = Field(
        default_factory=list, description="时间线"
    )
    characters: Dict[str, ContinuityCharacterState] = Field(
        default_factory=dict, description="角色状态/关系/知识"
    )
    info_acquisition_events: List[ContinuityInfoAcquisitionEvent] = Field(
        default_factory=list, description="信息获得事件（用于知识门控）"
    )
    open_threads: List[str] = Field(
        default_factory=list, description="未解决线索/悬念（短句）"
    )
    resolved_threads: List[str] = Field(
        default_factory=list, description="已收束线索/悬念（短句）"
    )


class EpisodeContinuitySnapshot(BaseModel):
    episode_number: int
    time_anchor: Optional[str] = None
    location_anchor: Optional[str] = None
    end_state: Optional[str] = None
    reveals: List[str] = Field(default_factory=list)
    info_acquisition_events: List[ContinuityInfoAcquisitionEvent] = Field(
        default_factory=list
    )


class EpisodeContinuityUpdatePayload(BaseModel):
    ledger: ContinuityLedger
    episode_snapshot: EpisodeContinuitySnapshot


class ContinuityAuditIssue(BaseModel):
    issue_type: str = Field(
        ...,
        description="问题类型：causality/timeline/knowledge/relationship/location/plausibility 等",
    )
    severity: str = Field(..., description="严重度：low/medium/high")
    description: str = Field(..., description="问题描述（短句）")
    evidence: Optional[str] = Field(None, description="触发问题的片段/定位（可选）")
    fix_guidance: Optional[str] = Field(None, description="修复指导（可选）")


class ContinuityAuditResult(BaseModel):
    verdict: str = Field(..., description="pass/fail")
    issues: List[ContinuityAuditIssue] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="一句话总结（可选）")
