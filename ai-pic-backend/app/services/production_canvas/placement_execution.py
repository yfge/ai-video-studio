from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasResolvedContext,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.schemas.production_canvas_review import (
    ProductionCanvasTimelinePlacementRequest,
)
from app.services.production_canvas.execution_common import (
    blocked_result,
    skill_definition,
)
from app.services.production_canvas.timeline_placement import (
    place_canvas_video_in_timeline,
)
from sqlalchemy.orm import Session


def _source_video_node_id(
    state: ProductionCanvasSavedState,
    placement_node_id: str,
) -> str | None:
    nodes = {node.id: node for node in state.nodes}
    for edge in state.edges:
        source = nodes.get(edge.from_node)
        if (
            edge.to_node == placement_node_id
            and edge.to_port == "approved_video"
            and source is not None
            and source.skill == "video.candidates"
        ):
            return source.id
    return None


def execute_timeline_placement(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
    state: ProductionCanvasSavedState,
    node_id: str,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("timeline.place")
    source_node_id = _source_video_node_id(state, node_id)
    missing = []
    if request.run_id is None:
        missing.append("run_id")
    if request.timeline_version is None:
        missing.append("timeline_version")
    if source_node_id is None:
        missing.append("approved_video")
    if missing:
        return blocked_result(
            request,
            title="Timeline Placement 等待选用视频",
            detail="需要已选用视频、当前 Timeline version 与 stable clip_id。",
            required_inputs=missing,
        )
    run = place_canvas_video_in_timeline(
        db,
        user,
        str(request.run_id),
        str(source_node_id),
        ProductionCanvasTimelinePlacementRequest(
            expected_version=int(request.timeline_version)
        ),
    )
    context = run.resolved_context
    source = next(
        (
            item
            for item in (run.saved_state.nodes if run.saved_state else [])
            if item.id == source_node_id
        ),
        None,
    )
    outputs = source.outputs if source else {}
    return ProductionCanvasSkillExecuteResponse(
        resolved_context=ProductionCanvasResolvedContext.model_validate(context),
        skill_result=ProductionCanvasSkillResult(
            skill="timeline.place",
            label=skill.label if skill else "Timeline Placement",
            status="ready",
            title=f"已回填 Timeline v{context.timeline_version}",
            detail="审核通过的视频已写入 stable clip_id；后续渲染只消费新版本。",
            outputs={
                "placed_timeline": context.timeline_id,
                "timeline_id": context.timeline_id,
                "timeline_version": context.timeline_version,
                "clip_id": context.clip_id,
                "placed_media_asset_id": outputs.get("placed_media_asset_id"),
                "placed_timeline_clip_id": outputs.get("placed_timeline_clip_id"),
                "source_video_node_id": source_node_id,
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
            reuse_targets=skill.reuse_targets if skill else [],
        ),
    )
