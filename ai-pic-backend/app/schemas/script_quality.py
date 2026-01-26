from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ScriptLintOptions(BaseModel):
    """剧本质检选项（可用于脚本 lint / 评分任务）。"""

    max_dialogue_chars: int = Field(
        15, ge=1, le=100, description="单句台词最大字符数（不含空格/标点）"
    )
    pass_threshold: float = Field(9.0, ge=0.0, le=10.0, description="合格阈值（0-10）")
    target_word_min: int | None = Field(
        None, ge=1, description="目标字数下限（估算；中文按字计）"
    )
    target_word_max: int | None = Field(
        None, ge=1, description="目标字数上限（估算；中文按字计）"
    )


class ScriptLintIssue(BaseModel):
    severity: Literal["error", "warn", "info"] = Field(..., description="问题严重级别")
    rule_id: str = Field(..., description="规则 ID")
    message: str = Field(..., description="问题描述")
    line: int | None = Field(None, description="行号（从 1 开始）")
    excerpt: str | None = Field(None, description="触发片段（可选）")
    suggestion: str | None = Field(None, description="修复建议（可选）")


class ScriptLintRuleResult(BaseModel):
    rule_id: str = Field(..., description="规则 ID")
    title: str = Field(..., description="规则名称")
    weight: float = Field(..., ge=0.0, description="权重")
    score: float = Field(..., ge=0.0, le=1.0, description="规则得分（0-1）")
    passed: bool = Field(..., description="规则是否通过")
    details: dict[str, Any] | None = Field(None, description="规则细节（可选）")


class ScriptLintMetrics(BaseModel):
    non_empty_lines: int = Field(..., ge=0, description="非空行数")
    dialogue_lines: int = Field(..., ge=0, description="对白行数")
    stage_lines: int = Field(..., ge=0, description="舞台指示/音效行数")
    estimated_words: int = Field(..., ge=0, description="估算字数（中文按字计）")
    estimated_dialogue_chars: int = Field(..., ge=0, description="对白估算字数（中文按字计）")


class ScriptLintResult(BaseModel):
    options: ScriptLintOptions = Field(..., description="本次质检使用的选项")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="综合评分（0-10）")
    passed: bool = Field(..., description="是否通过（overall_score >= pass_threshold）")
    rules: list[ScriptLintRuleResult] = Field(..., description="规则明细（可表格化展示）")
    issues: list[ScriptLintIssue] = Field(..., description="问题列表（含定位与建议）")
    metrics: ScriptLintMetrics = Field(..., description="统计指标")
    unimplemented_checks: list[str] = Field(
        default_factory=list, description="尚未自动检测的规则（需人工或 LLM 审核）"
    )

