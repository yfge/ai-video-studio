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


def request_for_canvas_node(
    run: ProductionCanvasRunResponse,
    node: ProductionCanvasSavedNode,
) -> ProductionCanvasSkillExecuteRequest:
    outputs = node.outputs or {}
    prompt = outputs.get("prompt")
    frame_indexes = outputs.get("frame_indexes")
    fps = _number(outputs, "fps")
    return ProductionCanvasSkillExecuteRequest(
        prompt=prompt if isinstance(prompt, str) and prompt else run.prompt,
        skill=node.skill or "",
        run_id=run.run_id,
        node_id=node.id,
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
        episode_id=_first_number(outputs, "episode_id", "episode_ids"),
        script_id=_first_number(outputs, "script_id", "script_ids"),
        task_id=_first_number(outputs, "task_id", "task_ids"),
        virtual_ip_id=_first_number(outputs, "virtual_ip_id", "virtual_ip_ids"),
        environment_id=_first_number(outputs, "environment_id", "environment_ids"),
    )
