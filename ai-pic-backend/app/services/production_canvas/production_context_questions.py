from __future__ import annotations

from app.models.user import User
from app.repositories.production_canvas_context_repository import (
    ProductionCanvasContextRepository,
)
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import (
    ProductionCanvasClarification,
    ProductionCanvasClarificationOption,
)
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from app.services.production_canvas.asset_selection import CanvasAssetSelection
from sqlalchemy.orm import Session


def add_asset_questions(
    planning: ProductionCanvasPlanningDraft,
    selection: CanvasAssetSelection,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanningDraft:
    questions = list(planning.brief.clarifications)
    asset_policy = planning.brief.assets.asset_policy
    if (
        request.virtual_ip_id is None
        and not selection.selected.virtual_ips
        and len(selection.candidate_virtual_ips) > 1
    ):
        questions.append(
            _asset_question(
                "context.virtual_ip_id",
                "匹配到多个 IP，请选择本次要关联的角色。",
                selection.candidate_virtual_ips,
            )
        )
    if (
        request.environment_id is None
        and not selection.selected.environments
        and len(selection.candidate_environments) > 1
    ):
        questions.append(
            _asset_question(
                "context.environment_id",
                "匹配到多个场景资产，请选择本次要复用的环境。",
                selection.candidate_environments,
            )
        )
    if asset_policy in {"reuse_only", "ask_if_ambiguous"}:
        if (
            planning.brief.assets.virtual_ip_name
            and not selection.selected.virtual_ips
            and not selection.candidate_virtual_ips
        ):
            questions.append(
                _missing_asset_question(
                    "virtual_ip",
                    planning.brief.assets.virtual_ip_name,
                )
            )
        for name in planning.brief.assets.environment_names:
            if (
                not selection.selected.environments
                and not selection.candidate_environments
            ):
                questions.append(_missing_asset_question("environment", name))
    questions = list({item.id: item for item in questions}.values())
    ready = planning.brief.ready_for_execution and not any(
        item.required and not item.answer for item in questions
    )
    return planning.model_copy(
        update={
            "brief": planning.brief.model_copy(
                update={
                    "clarifications": questions,
                    "ready_for_execution": ready,
                }
            )
        }
    )


def add_story_question(
    db: Session,
    user: User,
    planning: ProductionCanvasPlanningDraft,
    requested: ProductionCanvasPlanRequest,
    resolved: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanningDraft:
    if requested.story_id is not None or resolved.story_id is not None:
        return planning
    if resolved.virtual_ip_id is None:
        return planning
    candidates = ProductionCanvasContextRepository(db).list_stories(
        user,
        virtual_ip_id=int(resolved.virtual_ip_id),
        episode_number=planning.brief.video_spec.focus_episode_number,
    )
    if len(candidates) <= 1:
        return planning
    question = ProductionCanvasClarification(
        id="context.story_id",
        field="context.story_id",
        question="匹配到多个可继续制作的故事，请选择本次所属故事。",
        reason="多个故事都包含目标 IP 和集数，系统不会擅自新建或猜测。",
        options=[
            ProductionCanvasClarificationOption(
                label=f"{story.title} (#{story.id})",
                value=str(story.id),
            )
            for story in candidates[:20]
        ],
    )
    brief = planning.brief.model_copy(
        update={
            "clarifications": [*planning.brief.clarifications, question],
            "ready_for_execution": False,
        }
    )
    return planning.model_copy(update={"brief": brief})


def add_missing_protagonist_question(
    planning: ProductionCanvasPlanningDraft,
    requested: ProductionCanvasPlanRequest,
    resolved: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanningDraft:
    has_existing_context = any(
        (
            requested.virtual_ip_id,
            requested.story_id,
            requested.episode_id,
            requested.script_id,
            requested.timeline_id,
        )
    )
    if (
        requested.planning_mode != "series"
        or has_existing_context
        or resolved.virtual_ip_id is not None
        or planning.brief.assets.virtual_ip_name
    ):
        return planning
    question = ProductionCanvasClarification(
        id="assets.virtual_ip_name",
        field="assets.virtual_ip_name",
        question="系列内容的核心主角 IP 是谁？可以填写已有 IP 名或新角色名。",
        reason="持续剧集需要稳定的角色身份和跨集连续性锚点。",
    )
    questions = {item.id: item for item in [*planning.brief.clarifications, question]}
    brief = planning.brief.model_copy(
        update={
            "clarifications": list(questions.values()),
            "ready_for_execution": False,
        }
    )
    return planning.model_copy(update={"brief": brief})


def _asset_question(field: str, question: str, candidates):
    return ProductionCanvasClarification(
        id=field,
        field=field,
        question=question,
        reason="候选资产匹配度相同，系统不会猜测或错误关联。",
        options=[
            ProductionCanvasClarificationOption(
                label=f"{item.name} (#{item.id})",
                value=str(item.id),
            )
            for item in candidates[:20]
        ],
    )


def _missing_asset_question(
    kind: str,
    name: str,
) -> ProductionCanvasClarification:
    label = "IP" if kind == "virtual_ip" else "场景"
    return ProductionCanvasClarification(
        id="assets.asset_policy",
        field="assets.asset_policy",
        question=f"没有找到名为“{name}”的现有{label}资产，是否创建新资产？",
        reason="当前资产策略不允许系统在未确认时自动新建。",
        options=[
            ProductionCanvasClarificationOption(
                label="创建新资产",
                value="create_if_missing",
            ),
            ProductionCanvasClarificationOption(
                label="保持仅复用",
                value="reuse_only",
            ),
        ],
    )
