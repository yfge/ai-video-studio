from __future__ import annotations

import asyncio
import re
from typing import Any

from app.schemas.production_canvas_brief import (
    ProductionCanvasClarification,
    ProductionCanvasClarificationOption,
    ProductionCanvasModelChoice,
    ProductionCanvasModelPlan,
)
from app.services.providers.base import AIModelType
from app.utils.model_utils import (
    canonicalize_openai_image_model,
    parse_model_and_provider,
)


async def select_production_models(
    plan: ProductionCanvasModelPlan,
    ai_manager: Any,
) -> tuple[ProductionCanvasModelPlan, list[ProductionCanvasClarification]]:
    if ai_manager is None or not hasattr(ai_manager, "list_models"):
        return _without_catalog(plan)
    try:
        text_models, image_models, image_video_models, text_video_models = (
            await asyncio.gather(
                ai_manager.list_models(
                    model_type=AIModelType.TEXT_GENERATION,
                    source="static",
                ),
                ai_manager.list_models(
                    model_type=AIModelType.TEXT_TO_IMAGE,
                    source="static",
                ),
                ai_manager.list_models(
                    model_type=AIModelType.IMAGE_TO_VIDEO,
                    source="static",
                ),
                ai_manager.list_models(
                    model_type=AIModelType.TEXT_TO_VIDEO,
                    source="static",
                ),
            )
        )
    except Exception:
        return _without_catalog(plan)

    video_models = _dedupe_models([*image_video_models, *text_video_models])
    selected: dict[str, ProductionCanvasModelChoice] = {}
    questions: list[ProductionCanvasClarification] = []
    for field, choice, catalog in (
        ("text", plan.text, text_models),
        ("image", plan.image, image_models),
        ("video", plan.video, video_models),
    ):
        resolved, question = _resolve_choice(field, choice, catalog)
        selected[field] = resolved
        if question:
            questions.append(question)
    return ProductionCanvasModelPlan(**selected), questions


def _resolve_choice(
    field: str,
    choice: ProductionCanvasModelChoice,
    catalog: list[dict],
) -> tuple[ProductionCanvasModelChoice, ProductionCanvasClarification | None]:
    requested = (choice.requested or "").strip()
    if requested:
        match = _match_model(requested, catalog)
        if match:
            return (
                ProductionCanvasModelChoice(
                    requested=requested,
                    selected=_qualified_id(match),
                    provider=match.get("provider"),
                    status="requested",
                    reason="用户明确指定，且已通过当前模型目录能力校验。",
                ),
                None,
            )
        return (
            ProductionCanvasModelChoice(
                requested=requested,
                status="unavailable",
                reason="用户指定的模型未出现在当前可用能力目录中。",
            ),
            ProductionCanvasClarification(
                id=f"models.{field}",
                field=f"models.{field}.requested",
                question=f"“{requested}”当前不可用，{_field_label(field)}改用哪个模型？",
                reason="模型必须与当前已启用 provider 和任务类型兼容。",
                options=[
                    ProductionCanvasClarificationOption(
                        label=str(item.get("name") or item.get("id")),
                        value=_qualified_id(item),
                    )
                    for item in catalog[:12]
                ],
            ),
        )
    if catalog:
        preferred = catalog[0]
        return (
            ProductionCanvasModelChoice(
                selected=_qualified_id(preferred),
                provider=preferred.get("provider"),
                status="auto_selected",
                reason=f"按当前可用能力目录自动选择{_field_label(field)}。",
            ),
            None,
        )
    return (
        ProductionCanvasModelChoice(
            status="pipeline_default",
            reason=f"当前目录未返回{_field_label(field)}，执行时沿用现有链路默认。",
        ),
        None,
    )


def _without_catalog(
    plan: ProductionCanvasModelPlan,
) -> tuple[ProductionCanvasModelPlan, list[ProductionCanvasClarification]]:
    values = {}
    for field, choice in (
        ("text", plan.text),
        ("image", plan.image),
        ("video", plan.video),
    ):
        requested = choice.requested
        values[field] = ProductionCanvasModelChoice(
            requested=requested,
            selected=requested,
            status="requested" if requested else "pipeline_default",
            reason=(
                "模型目录暂不可用，保留用户指定模型并由执行链最终校验。"
                if requested
                else "模型目录暂不可用，沿用现有生产链默认模型。"
            ),
        )
    return ProductionCanvasModelPlan(**values), []


def _match_model(requested: str, catalog: list[dict]) -> dict | None:
    model_id, provider_hint = parse_model_and_provider(requested)
    needle = _normalize_model(model_id or requested)
    candidates = (
        [
            item
            for item in catalog
            if str(item.get("provider") or "").casefold() == provider_hint.casefold()
        ]
        if provider_hint
        else catalog
    )
    canonical_id = (model_id or "").strip().casefold()
    canonical_exact = [
        item
        for item in candidates
        if canonical_id and str(item.get("id") or "").strip().casefold() == canonical_id
    ]
    if len(canonical_exact) == 1:
        return canonical_exact[0]
    exact = [
        item
        for item in candidates
        if needle
        in {
            _normalize_model(str(item.get("id") or "")),
            _normalize_model(str(item.get("name") or "")),
        }
    ]
    if len(exact) == 1:
        return exact[0]
    contains = [
        item
        for item in candidates
        if needle
        and (
            needle in _normalize_model(str(item.get("id") or ""))
            or needle in _normalize_model(str(item.get("name") or ""))
            or _normalize_model(str(item.get("id") or "")) in needle
        )
    ]
    if len(contains) == 1:
        return contains[0]
    return _preferred_family_match(contains)


def _preferred_family_match(candidates: list[dict]) -> dict | None:
    preferred = [
        item
        for item in candidates
        if "推荐" in str(item.get("name") or "")
        and "fast" not in str(item.get("id") or "").casefold()
        and {"text_to_video", "image_to_video"}.issubset(
            {str(value).casefold() for value in item.get("capabilities") or []}
        )
    ]
    return preferred[0] if len(preferred) == 1 else None


def _normalize_model(value: str) -> str:
    canonical = canonicalize_openai_image_model(value) or value
    return re.sub(r"[^a-z0-9]+", "", canonical.casefold())


def _qualified_id(model: dict) -> str:
    model_id = str(model.get("id") or "")
    provider = str(model.get("provider") or "")
    return f"{provider}:{model_id}" if provider and ":" not in model_id else model_id


def _dedupe_models(models: list[dict]) -> list[dict]:
    unique: dict[str, dict] = {}
    for model in models:
        unique.setdefault(_qualified_id(model), model)
    return list(unique.values())


def _field_label(field: str) -> str:
    return {"text": "文本模型", "image": "图像模型", "video": "视频模型"}[field]
