from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
)
from app.services.production_canvas.asset_generation import (
    execute_environment_image_generation,
    execute_virtual_ip_image_generation,
)
from app.services.production_canvas.execution_common import blocked_result
from app.services.production_canvas.graph_runtime import (
    CanvasGraphResolution,
    apply_canvas_node_execution,
    resolve_canvas_graph_request,
)
from app.services.production_canvas.immediate_execution import (
    execute_asset_selection,
    execute_brief_compose,
)
from app.services.production_canvas.media_execution import (
    execute_storyboard_images,
    execute_storyboard_video_candidates,
)
from app.services.production_canvas.pipeline_execution import (
    execute_script_generation,
    execute_storyboard_generation,
    execute_timeline_pipeline,
)
from app.services.production_canvas.render_execution import (
    execute_timeline_export,
    execute_timeline_render,
)
from app.services.production_canvas.report_execution import execute_report_summary
from app.services.production_canvas.run_persistence import load_canvas_saved_state
from app.services.production_canvas.stale_runtime import canvas_node_input_fingerprint
from sqlalchemy.orm import Session


def _dispatch_canvas_skill(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    if request.skill == "brief.compose":
        return execute_brief_compose(request)
    if request.skill == "asset.select":
        return execute_asset_selection(db, user, request)
    if request.skill == "virtual_ip.image":
        return execute_virtual_ip_image_generation(db, user, request)
    if request.skill == "environment.image":
        return execute_environment_image_generation(db, user, request)
    if request.skill == "script.generate":
        return execute_script_generation(db, user, request)
    if request.skill == "storyboard.plan":
        return execute_storyboard_generation(db, user, request)
    if request.skill == "image.candidates":
        return execute_storyboard_images(db, user, request)
    if request.skill == "video.candidates":
        return execute_storyboard_video_candidates(db, user, request)
    if request.skill == "timeline.assemble":
        return execute_timeline_pipeline(db, user, request)
    if request.skill == "timeline.render":
        return execute_timeline_render(db, user, request)
    if request.skill == "timeline.export":
        return execute_timeline_export(db, user, request)
    if request.skill == "report.summarize":
        return execute_report_summary(db, user, request)

    return blocked_result(
        request,
        title=f"{request.skill} 暂未接入自动执行",
        detail="当前 Skill 已登记后台复用目标，但还没有接入明确的任务派发器。",
        required_inputs=["dispatcher"],
    )


def execute_canvas_resolution(
    db: Session,
    user: User,
    resolution: CanvasGraphResolution,
    state: ProductionCanvasSavedState,
) -> ProductionCanvasSkillExecuteResponse:
    if resolution.missing_inputs:
        response = blocked_result(
            resolution.request,
            title="画布节点等待类型化输入",
            detail="必填端口尚未从已连接的上游输出解析完成。",
            required_inputs=resolution.missing_inputs,
        )
    else:
        response = _dispatch_canvas_skill(db, user, resolution.request)
    return response.model_copy(
        update={
            "node_id": resolution.node_id,
            "resolved_inputs": resolution.resolved_inputs,
            "execution_order": resolution.execution_order,
            "input_fingerprint": canvas_node_input_fingerprint(
                state, resolution.node_id
            ),
        }
    )


def _node_execution(
    response: ProductionCanvasSkillExecuteResponse,
) -> ProductionCanvasNodeExecution:
    return ProductionCanvasNodeExecution(
        skill_result=response.skill_result,
        task_id=response.task_id,
        task_status=response.task_status,
        node_id=response.node_id,
        resolved_inputs=response.resolved_inputs,
        input_fingerprint=response.input_fingerprint,
    )


def _execute_downstream(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
    state: ProductionCanvasSavedState,
    first_resolution: CanvasGraphResolution,
) -> ProductionCanvasSkillExecuteResponse:
    executions: list[ProductionCanvasNodeExecution] = []
    working_state = state
    node_by_id = {node.id: node for node in state.nodes}
    for node_id in first_resolution.execution_order:
        node = node_by_id[node_id]
        node_request = request.model_copy(
            update={
                "node_id": node_id,
                "skill": node.skill or "",
                "execution_scope": "node",
            }
        )
        resolution = resolve_canvas_graph_request(working_state, node_request)
        if resolution is None:
            break
        response = execute_canvas_resolution(db, user, resolution, working_state)
        execution = _node_execution(response)
        executions.append(execution)
        working_state = apply_canvas_node_execution(working_state, execution)
        if response.skill_result.status in {"blocked", "failed", "cancelled"}:
            break

    first = executions[0]
    return ProductionCanvasSkillExecuteResponse(
        **first.model_dump(),
        execution_order=first_resolution.execution_order,
        executions=executions,
    )


def execute_canvas_skill(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    state = (
        load_canvas_saved_state(db, user, request.run_id) if request.run_id else None
    )
    resolution = resolve_canvas_graph_request(state, request) if state else None
    if state and state.graph_version == 2 and resolution is None:
        return blocked_result(
            request,
            title="画布节点不属于当前类型图",
            detail="node_id 与当前 Run 的 graph v2 定义不一致，执行已拒绝。",
            required_inputs=["graph_node"],
        )
    if resolution is None:
        return _dispatch_canvas_skill(db, user, request)
    if request.execution_scope == "downstream":
        return _execute_downstream(db, user, request, state, resolution)
    return execute_canvas_resolution(db, user, resolution, state)
