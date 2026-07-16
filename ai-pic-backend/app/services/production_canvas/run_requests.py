from __future__ import annotations

from app.schemas.production_canvas import (
    ProductionCanvasRunResponse,
    ProductionCanvasSavedNode,
    ProductionCanvasSkillExecuteRequest,
)


def _number(outputs: dict, key: str) -> int | float | None:
    value = outputs.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def _first_number(outputs: dict, singular: str, plural: str) -> int | None:
    value = _number(outputs, singular)
    if isinstance(value, int):
        return value
    values = outputs.get(plural)
    if isinstance(values, list) and values and isinstance(values[0], int):
        return values[0]
    return None


def _context_number(
    context: object,
    outputs: dict,
    singular: str,
    plural: str,
) -> int | None:
    value = _first_number(outputs, singular, plural)
    if value is not None:
        return value
    fallback = (
        context.get(singular)
        if isinstance(context, dict)
        else getattr(context, singular, None)
    )
    return (
        fallback
        if isinstance(fallback, int) and not isinstance(fallback, bool)
        else None
    )


def _context_string(
    context: object,
    outputs: dict,
    key: str,
) -> str | None:
    value = outputs.get(key)
    if isinstance(value, str) and value:
        return value
    fallback = (
        context.get(key) if isinstance(context, dict) else getattr(context, key, None)
    )
    return fallback if isinstance(fallback, str) and fallback else None


def request_for_canvas_node_context(
    base: ProductionCanvasSkillExecuteRequest,
    node: ProductionCanvasSavedNode,
    context: object,
) -> ProductionCanvasSkillExecuteRequest:
    outputs = node.outputs or {}
    prompt = outputs.get("prompt")
    planning_mode = outputs.get("planning_mode")
    frame_indexes = outputs.get("frame_indexes")
    fps = _number(outputs, "fps")
    return ProductionCanvasSkillExecuteRequest(
        prompt=prompt if isinstance(prompt, str) and prompt else base.prompt,
        planning_mode=(
            planning_mode
            if planning_mode in {"series", "single_video"}
            else base.planning_mode
        ),
        skill=node.skill or "",
        run_id=base.run_id,
        node_id=node.id,
        execution_scope="node",
        frame_indexes=(
            frame_indexes
            if isinstance(frame_indexes, list)
            and all(isinstance(item, int) for item in frame_indexes)
            else None
        ),
        model=outputs.get("model") if isinstance(outputs.get("model"), str) else None,
        aspect_ratio=(
            outputs.get("aspect_ratio")
            if isinstance(outputs.get("aspect_ratio"), str)
            else None
        ),
        require_reference_images=(
            outputs.get("require_reference_images")
            if isinstance(outputs.get("require_reference_images"), bool)
            else None
        ),
        duration=_number(outputs, "duration"),
        fps=int(fps) if fps is not None else None,
        resolution=(
            outputs.get("resolution")
            if isinstance(outputs.get("resolution"), str)
            else None
        ),
        ratio=outputs.get("ratio") if isinstance(outputs.get("ratio"), str) else None,
        camera_fixed=(
            outputs.get("camera_fixed")
            if isinstance(outputs.get("camera_fixed"), bool)
            else None
        ),
        start_frame_url=(
            outputs.get("start_frame_url")
            if isinstance(outputs.get("start_frame_url"), str)
            else None
        ),
        reference_artifacts=[
            item
            for item in outputs.get("reference_artifacts", [])
            if isinstance(item, str) and item
        ],
        virtual_ip_id=_context_number(
            context, outputs, "virtual_ip_id", "virtual_ip_ids"
        ),
        environment_id=_context_number(
            context, outputs, "environment_id", "environment_ids"
        ),
        story_id=_context_number(context, outputs, "story_id", "story_ids"),
        episode_id=_context_number(context, outputs, "episode_id", "episode_ids"),
        script_id=_context_number(context, outputs, "script_id", "script_ids"),
        timeline_id=_context_number(context, outputs, "timeline_id", "timeline_ids"),
        timeline_version=_context_number(
            context, outputs, "timeline_version", "timeline_versions"
        ),
        clip_id=_context_string(context, outputs, "clip_id"),
        task_id=_context_number(context, outputs, "task_id", "task_ids"),
    )


def request_for_canvas_node(
    run: ProductionCanvasRunResponse,
    node: ProductionCanvasSavedNode,
) -> ProductionCanvasSkillExecuteRequest:
    return request_for_canvas_node_context(
        ProductionCanvasSkillExecuteRequest(
            prompt=run.prompt,
            skill=node.skill or "",
            run_id=run.run_id,
        ),
        node,
        run.resolved_context,
    )
