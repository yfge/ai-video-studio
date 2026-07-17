from __future__ import annotations

from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import (
    ProductionCanvasAssetIntent,
    ProductionCanvasClarification,
    ProductionCanvasCreativeIntent,
    ProductionCanvasModelPlan,
    ProductionCanvasVideoSpec,
)
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft


def apply_answers(
    draft: ProductionCanvasPlanningDraft,
    answers: dict[str, str],
) -> ProductionCanvasPlanningDraft:
    if not answers:
        return draft
    brief = draft.brief.model_copy(deep=True)
    intent = brief.intent.model_copy(deep=True)
    spec = brief.video_spec.model_copy(deep=True)
    assets = brief.assets.model_copy(deep=True)
    models = brief.models.model_copy(deep=True)
    if value := answers.get("intent.narrative_seed"):
        intent.narrative_seed = value
        intent.objective = f"{brief.source_prompt}\n用户补充：{value}"
    if value := answers.get("assets.virtual_ip_name"):
        assets.virtual_ip_name = value
    if value := answers.get("assets.environment_names"):
        assets.environment_names = [
            item.strip() for item in value.replace("，", ",").split(",") if item.strip()
        ]
    if value := answers.get("assets.asset_policy"):
        assets.asset_policy = value
    for field in ("duration_seconds", "episode_count", "fps"):
        value = answers.get(f"video_spec.{field}")
        if value and value.isdigit():
            setattr(spec, field, int(value))
    for field in ("aspect_ratio", "resolution"):
        value = answers.get(f"video_spec.{field}")
        if value:
            setattr(spec, field, value)
    for field in ("text", "image", "video"):
        value = answers.get(f"models.{field}") or answers.get(
            f"models.{field}.requested"
        )
        if value:
            getattr(models, field).requested = value
    spec = ProductionCanvasVideoSpec.model_validate(spec.model_dump())
    assets = ProductionCanvasAssetIntent.model_validate(assets.model_dump())
    return draft.model_copy(
        update={
            "brief": brief.model_copy(
                update={
                    "intent": intent,
                    "video_spec": spec,
                    "assets": assets,
                    "models": models,
                }
            )
        }
    )


def apply_explicit_content_overrides(
    draft: ProductionCanvasPlanningDraft,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanningDraft:
    overrides = request.brief_overrides
    brief = draft.brief.model_copy(deep=True)
    spec = brief.video_spec.model_copy(deep=True)
    models = brief.models.model_copy(deep=True)
    for field in (
        "duration_seconds",
        "episode_count",
        "aspect_ratio",
        "resolution",
        "fps",
    ):
        value = getattr(overrides, field)
        if value is not None:
            setattr(spec, field, value)
    if overrides.visual_style:
        spec.visual_style = [overrides.visual_style]
    for field in ("text", "image", "video"):
        value = getattr(overrides, f"{field}_model")
        if value:
            getattr(models, field).requested = value
    content = (
        draft.content_plan.model_copy(update={"title": overrides.title})
        if overrides.title
        else draft.content_plan
    )
    return draft.model_copy(
        update={
            "brief": brief.model_copy(
                update={
                    "video_spec": ProductionCanvasVideoSpec.model_validate(
                        spec.model_dump()
                    ),
                    "models": ProductionCanvasModelPlan.model_validate(
                        models.model_dump()
                    ),
                }
            ),
            "content_plan": content,
        }
    )


def finalize_questions(
    draft: ProductionCanvasPlanningDraft,
    request: ProductionCanvasPlanRequest,
    extra_questions: list[ProductionCanvasClarification],
) -> ProductionCanvasPlanningDraft:
    brief = draft.brief
    questions = [*brief.clarifications, *extra_questions]
    if _needs_seed_question(brief.intent):
        questions.append(
            ProductionCanvasClarification(
                id="intent.narrative_seed",
                field="intent.narrative_seed",
                question="这条内容最核心的人物、事件或要表达的观点是什么？",
                reason="当前目标过于宽泛，直接生成会造成题材和内容方向漂移。",
            )
        )
    questions = _dedupe_questions(questions, request.clarification_answers)
    ready = brief.interpretation_status != "failed" and not any(
        item.required and not item.answer for item in questions
    )
    return draft.model_copy(
        update={
            "brief": brief.model_copy(
                update={
                    "clarifications": questions,
                    "ready_for_execution": ready,
                }
            )
        }
    )


def _dedupe_questions(
    questions: list[ProductionCanvasClarification],
    answers: dict[str, str],
) -> list[ProductionCanvasClarification]:
    deduped: dict[str, ProductionCanvasClarification] = {}
    for question in questions:
        answer = answers.get(question.id) or answers.get(question.field)
        deduped[question.id] = question.model_copy(
            update={"answer": answer or question.answer}
        )
    return list(deduped.values())[:10]


def _needs_seed_question(intent: ProductionCanvasCreativeIntent) -> bool:
    value = intent.narrative_seed.strip(" ，,。")
    generic = {
        "做个视频",
        "制作视频",
        "生成视频",
        "做一个故事",
        "生成一个故事",
        "整体创建",
    }
    return len(value) < 6 or value in generic
