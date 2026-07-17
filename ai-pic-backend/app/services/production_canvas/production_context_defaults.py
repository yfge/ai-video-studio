from __future__ import annotations

from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import (
    ProductionCanvasAssetIntent,
    ProductionCanvasCreativeIntent,
    ProductionCanvasInterpretationStatus,
    ProductionCanvasModelChoice,
    ProductionCanvasModelPlan,
    ProductionCanvasProductionBrief,
    ProductionCanvasVideoSpec,
)
from app.schemas.production_canvas_content import (
    ProductionCanvasContentPlan,
    ProductionCanvasEpisodePlan,
    ProductionCanvasPlanningDraft,
)


def deterministic_planning_draft(
    request: ProductionCanvasPlanRequest,
    *,
    interpretation_status: ProductionCanvasInterpretationStatus = (
        "deterministic_compatibility"
    ),
    interpretation_warnings: list[str] | None = None,
) -> ProductionCanvasPlanningDraft:
    prompt = request.prompt.strip()
    title = request.brief_overrides.title or _fallback_title(prompt)
    overrides = request.brief_overrides
    spec = ProductionCanvasVideoSpec(
        duration_seconds=overrides.duration_seconds,
        episode_count=overrides.episode_count,
        aspect_ratio=overrides.aspect_ratio,
        resolution=overrides.resolution,
        fps=overrides.fps,
        visual_style=([overrides.visual_style] if overrides.visual_style else []),
    )
    models = ProductionCanvasModelPlan(
        text=ProductionCanvasModelChoice(requested=overrides.text_model),
        image=ProductionCanvasModelChoice(requested=overrides.image_model),
        video=ProductionCanvasModelChoice(requested=overrides.video_model),
    )
    brief = ProductionCanvasProductionBrief(
        source_prompt=prompt,
        interpretation_status=interpretation_status,
        interpretation_warnings=interpretation_warnings or [],
        intent=ProductionCanvasCreativeIntent(
            kind=(
                "single_video"
                if request.planning_mode == "single_video"
                else "story_series"
            ),
            objective=prompt,
            narrative_seed=prompt,
        ),
        video_spec=spec,
        models=models,
        assets=ProductionCanvasAssetIntent(),
    )
    return ProductionCanvasPlanningDraft(
        brief=brief,
        content_plan=_fallback_content_plan(brief, title=title),
    )


def _fallback_content_plan(
    brief: ProductionCanvasProductionBrief,
    *,
    title: str,
) -> ProductionCanvasContentPlan:
    seed = brief.intent.narrative_seed
    count = brief.video_spec.episode_count
    numbers = (
        [1]
        if brief.intent.kind == "single_video"
        else list(range(1, min(count or 0, 24) + 1))
    )
    episodes = [
        ProductionCanvasEpisodePlan(
            episode_number=number,
            title=title if number == 1 else f"{title} · {number}",
            logline=seed,
            beats=[
                "用原始目标建立开场。",
                "围绕原始目标推进主要事件。",
                "以可见结果结束本集内容。",
            ],
            payoff="完成原始目标要求的核心表达。",
            cliffhanger="如需延续，由下一轮内容规划补充。",
        )
        for number in numbers
    ]
    return ProductionCanvasContentPlan(
        title=title,
        premise=seed,
        synopsis=seed,
        main_conflict="由结构化上下文模型补充。",
        season_arc="由结构化上下文模型补充。",
        recurring_engine="由结构化上下文模型补充。",
        episodes=episodes,
    )


def _fallback_title(prompt: str) -> str:
    compact = " ".join(prompt.split())
    return compact[:24] or "未命名内容计划"
