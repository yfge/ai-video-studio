from __future__ import annotations

import json
from dataclasses import dataclass

from app.schemas.production_canvas_content import ProductionCanvasProductionContext


@dataclass(frozen=True)
class CompiledCanvasScriptContext:
    requirements: str
    model: str | None
    style_preferences: list[str] | None
    target_chars: int


def compile_canvas_script_context(
    context: ProductionCanvasProductionContext,
    *,
    episode_number: int,
) -> CompiledCanvasScriptContext:
    brief = context.brief
    content = context.content_plan
    episode_plan = next(
        (item for item in content.episodes if item.episode_number == episode_number),
        content.episodes[0] if content.episodes else None,
    )
    duration = brief.video_spec.duration_seconds
    sections = [
        "## Production Context v1（最高优先级）",
        "- 原始用户目标必须作为创意事实保留，不能被通用样板替换。",
        "- 只能使用本上下文中的人物、产品、技术、场景和事件；"
        "禁止擅自加入原始目标不存在的角色、公司、业务事件或预设冲突模板。",
        "- 若通用质量规则与本上下文冲突，以本上下文和原始用户目标为准。",
        f"### 原始用户目标\n{brief.source_prompt}",
        "### 结构化创意意图\n"
        + json.dumps(brief.intent.model_dump(), ensure_ascii=False, indent=2),
        "### 内容主线\n"
        + json.dumps(
            {
                "title": content.title,
                "premise": content.premise,
                "synopsis": content.synopsis,
                "main_conflict": content.main_conflict,
                "characters": [item.model_dump() for item in content.characters],
                "environments": [item.model_dump() for item in content.environments],
                "season_arc": content.season_arc,
                "recurring_engine": content.recurring_engine,
                "continuity_rules": content.continuity_rules,
                "future_threads": content.future_threads,
            },
            ensure_ascii=False,
            indent=2,
        ),
    ]
    if episode_plan:
        sections.append(
            f"### 当前第 {episode_number} 集合同\n"
            + json.dumps(
                episode_plan.model_dump(),
                ensure_ascii=False,
                indent=2,
            )
        )
    sections.append(
        "### 生产规格\n"
        + json.dumps(
            brief.video_spec.model_dump(exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )
    )
    sections.append(
        "### 模型与资产关联\n"
        + json.dumps(
            {
                "models": brief.models.model_dump(),
                "asset_associations": [
                    item.model_dump() for item in context.asset_associations
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if duration:
        sections.extend(
            [
                "### 时长硬约束",
                f"- 本集/本条成片总时长必须是 {duration} 秒。",
                "- 标题、logline、场景时长、beats 和正文必须使用同一时长。",
                "- prompt 中出现的其他数字只有在明确属于剧情时才能作为戏内数字。",
            ]
        )
    if brief.intent.must_include:
        sections.append(
            "### 必须出现\n"
            + "\n".join(f"- {item}" for item in brief.intent.must_include)
        )
    if brief.intent.must_avoid:
        sections.append(
            "### 禁止出现\n"
            + "\n".join(f"- {item}" for item in brief.intent.must_avoid)
        )
    target_chars = max(600, min(2500, round((duration or 180) * 5)))
    styles = list(dict.fromkeys([*brief.intent.tone, *brief.video_spec.visual_style]))
    return CompiledCanvasScriptContext(
        requirements="\n\n".join(sections),
        model=brief.models.text.selected,
        style_preferences=styles or None,
        target_chars=target_chars,
    )
