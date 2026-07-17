from __future__ import annotations

from app.schemas.production_canvas import CanvasNodeStatus, ProductionCanvasPlanRequest
from app.schemas.production_canvas_content import ProductionCanvasProductionContext
from app.services.production_canvas.asset_selection import CanvasAssetSelection


def asset_title(
    selection: CanvasAssetSelection,
    context: ProductionCanvasProductionContext,
) -> str:
    decisions = [
        f"{'IP' if item.kind == 'virtual_ip' else '场景'}："
        f"{'复用' if item.decision == 'reused' else '新建' if item.decision == 'created' else '待确认'}"
        f"{f' {item.asset_name}' if item.asset_name else ''}"
        for item in context.asset_associations
        if item.decision != "not_required"
    ]
    if decisions:
        return "；".join(decisions)
    ip_names = _asset_names(selection.selected.virtual_ips)
    env_names = _asset_names(selection.selected.environments)
    created = bool(
        selection.created_virtual_ip_ids or selection.created_environment_ids
    )
    if ip_names and env_names:
        return f"已{'创建' if created else '选择'} {ip_names} 和 {env_names}"
    if ip_names:
        return f"已{'创建' if created else '选择'} IP：{ip_names}；环境待确认"
    if env_names:
        return f"IP 待确认；已{'创建' if created else '选择'}环境：{env_names}"
    return "待确认 IP 和环境资产"


def asset_detail(
    selection: CanvasAssetSelection,
    context: ProductionCanvasProductionContext,
) -> str:
    if context.asset_associations:
        return "；".join(item.reason for item in context.asset_associations)
    ip_names = _asset_names(selection.selected.virtual_ips) or "待选择 IP"
    env_names = _asset_names(selection.selected.environments) or "待选择环境"
    if selection.created_virtual_ip_ids or selection.created_environment_ids:
        return f"根据 prompt 选择或创建 IP：{ip_names}；环境：{env_names}"
    return f"复用现有 IP：{ip_names}；环境：{env_names}"


def asset_status(
    selection: CanvasAssetSelection,
    context: ProductionCanvasProductionContext,
) -> CanvasNodeStatus:
    if not context.brief.ready_for_execution:
        return "blocked"
    if (
        selection.selected.virtual_ips
        or selection.selected.environments
        or all(item.decision == "not_required" for item in context.asset_associations)
    ):
        return "review"
    return "blocked"


def downstream_status(
    request: ProductionCanvasPlanRequest,
    selection: CanvasAssetSelection,
    skill_id: str,
    context: ProductionCanvasProductionContext,
) -> CanvasNodeStatus:
    if not context.brief.ready_for_execution:
        return "blocked"
    if skill_id == "virtual_ip.image" and selection.selected.virtual_ips:
        return "ready"
    if skill_id == "environment.image" and selection.selected.environments:
        return "ready"
    if skill_id == "script.generate":
        if request.script_id:
            return "review"
        if request.episode_id:
            return "ready"
    if skill_id in {"timeline.assemble", "image.candidates"} and request.script_id:
        return "review"
    if skill_id == "video.candidates" and request.script_id:
        return "blocked"
    if skill_id == "storyboard.plan" and request.script_id:
        return "ready"
    if skill_id in {"timeline.render", "timeline.export"} and request.script_id:
        return "review"
    if skill_id == "report.summarize" and request.task_id:
        return "ready"
    return "blocked"


def downstream_outputs(
    request: ProductionCanvasPlanRequest,
    selection: CanvasAssetSelection,
    context: ProductionCanvasProductionContext,
    skill_id: str,
) -> dict:
    outputs = dict(selection.outputs())
    outputs.update(request.model_dump(exclude={"prompt"}, exclude_none=True))
    outputs["production_context"] = context.model_dump()
    outputs["target_duration_seconds"] = context.brief.video_spec.duration_seconds
    outputs["aspect_ratio"] = context.brief.video_spec.aspect_ratio
    outputs["resolution"] = context.brief.video_spec.resolution
    outputs["fps"] = context.brief.video_spec.fps
    outputs["ratio"] = context.brief.video_spec.aspect_ratio
    model = None
    if skill_id in {
        "virtual_ip.image",
        "environment.image",
        "image.candidates",
    }:
        model = context.brief.models.image.selected
    elif skill_id == "video.candidates":
        model = context.brief.models.video.selected
    elif skill_id == "script.generate":
        model = context.brief.models.text.selected
    if model:
        outputs["model"] = model
    return outputs


def required_inputs(
    request: ProductionCanvasPlanRequest,
    selection: CanvasAssetSelection,
    skill_id: str,
    context: ProductionCanvasProductionContext,
) -> list[str]:
    if not context.brief.ready_for_execution:
        return ["production_context"]
    if skill_id == "virtual_ip.image" and not selection.selected.virtual_ips:
        return ["virtual_ip_id"]
    if skill_id == "environment.image" and not selection.selected.environments:
        return ["environment_id"]
    if skill_id == "script.generate" and request.episode_id is None:
        return ["episode_id"]
    if (
        skill_id
        in {
            "storyboard.plan",
            "image.candidates",
            "video.candidates",
            "timeline.assemble",
            "timeline.render",
            "timeline.export",
        }
        and request.script_id is None
    ):
        return ["script_id"]
    if skill_id == "report.summarize" and request.task_id is None:
        return ["task_id"]
    return []


def downstream_detail(
    request: ProductionCanvasPlanRequest,
    selection: CanvasAssetSelection,
    skill_id: str,
    context: ProductionCanvasProductionContext,
) -> str:
    if not context.brief.ready_for_execution:
        questions = [
            item.question
            for item in context.brief.clarifications
            if item.required and not item.answer
        ]
        return "等待用户补充：" + "；".join(questions)
    if skill_id == "script.generate" and request.script_id:
        return "已绑定现有剧本；仅在显式要求重生成时调用剧本 worker。"
    if skill_id == "timeline.assemble" and request.script_id:
        return "优先复用当前剧本的 Timeline；缺失时由操作员显式创建。"
    if skill_id == "image.candidates" and request.script_id:
        return "等待操作员从当前剧本分镜显式生成图片候选。"
    if skill_id == "video.candidates" and request.script_id:
        return "等待图片候选通过人工选用后生成视频候选。"
    missing = required_inputs(request, selection, skill_id, context)
    if skill_id in {"timeline.render", "timeline.export"} and not missing:
        return "人工触发后复用当前 Timeline 版本，保留 RenderJob 和成片资产证据。"
    if not missing:
        return "执行时消费同一份 production_context，并复用现有生产服务。"
    return "需要先补齐执行上下文，之后才会调用现有生成 API、service 或 worker。"


def _asset_names(assets) -> str:
    return "、".join(asset.name for asset in assets)
