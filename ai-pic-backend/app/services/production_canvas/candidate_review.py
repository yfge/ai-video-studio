from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.user import User
from app.repositories.storyboard_media_repository import load_storyboard_frames
from app.schemas.production_canvas import (
    ProductionCanvasRunResponse,
    ProductionCanvasSavedNode,
)
from app.schemas.production_canvas_review import ProductionCanvasMediaCandidateList
from app.services.production_canvas.execution_common import load_script
from app.services.production_canvas.stale_runtime import (
    canvas_node_input_fingerprint,
    canvas_stale_impact_nodes,
)
from sqlalchemy.orm import Session

from .access_control import canvas_run_owner, require_canvas_access
from .candidate_history import (
    load_canvas_candidate_history,
    materialize_canvas_candidate,
    remember_canvas_candidate_history,
)
from .candidate_review_state import set_canvas_candidate_review
from .run_persistence import load_canvas_saved_state, save_canvas_state
from .timeline_candidates import list_timeline_video_candidates

_MEDIA_SKILLS = {
    "image.candidates": ("image", "approved_image"),
    "video.candidates": ("video", "approved_video"),
}


def _review_node(state, node_id: str) -> ProductionCanvasSavedNode:
    node = next((item for item in state.nodes if item.id == node_id), None)
    if node is None:
        raise ValueError("canvas_node_not_found")
    if node.skill not in _MEDIA_SKILLS:
        raise ValueError("canvas_node_not_reviewable")
    return node


def _string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _clip_id(frame: dict[str, Any]) -> str | None:
    source = frame.get("source")
    return _string(frame.get("timeline_clip_id")) or _string(
        source.get("clip_id") if isinstance(source, dict) else None
    )


def _candidate_urls(frame: dict[str, Any], media_type: str) -> list[str]:
    if media_type == "image":
        keys = ("start_image_urls", "image_url", "start_image_url")
    else:
        keys = ("video_urls", "video_url")
    urls: list[str] = []
    for key in keys:
        raw = frame.get(key)
        values = raw if isinstance(raw, list) else [raw]
        for value in values:
            url = _string(value)
            if url and url not in urls:
                urls.append(url)
    return urls


def _frame_indexes(node: ProductionCanvasSavedNode) -> set[int] | None:
    raw = node.outputs.get("frame_indexes") or node.outputs.get("queued_frame_indexes")
    if not isinstance(raw, list):
        return None
    indexes = {item for item in raw if isinstance(item, int) and item >= 0}
    return indexes or None


def _model(frame: dict[str, Any], node: ProductionCanvasSavedNode) -> str | None:
    generation = frame.get("image_gen")
    if isinstance(generation, dict):
        value = _string(generation.get("model_id"))
        if value:
            return value
    return _string(node.outputs.get("model"))


def _prompt(frame: dict[str, Any], media_type: str) -> str | None:
    key = "ai_prompt" if media_type == "image" else "i2v_motion_prompt"
    return _string(frame.get(key)) or _string(frame.get("description"))


def _candidate_lineage(
    frame: dict[str, Any], url: str, run_id: str, node_id: str
) -> dict[str, Any]:
    raw = frame.get("canvas_candidate_lineage")
    for item in raw if isinstance(raw, list) else []:
        if (
            isinstance(item, dict)
            and item.get("url") == url
            and item.get("run_id") == run_id
            and item.get("node_id") == node_id
        ):
            return item
    return {}


def list_canvas_media_candidates(
    db: Session,
    user: User,
    run_id: str,
    node_id: str,
) -> ProductionCanvasMediaCandidateList:
    owner = canvas_run_owner(db, user, run_id)
    state = load_canvas_saved_state(db, user, run_id)
    if state is None:
        raise ValueError("canvas_run_state_not_found")
    node = _review_node(state, node_id)
    script_id = node.outputs.get("script_id")
    script = load_script(db, owner, script_id if isinstance(script_id, int) else None)
    if script is None:
        raise ValueError("canvas_script_not_found")

    media_type, _ = _MEDIA_SKILLS[node.skill]
    requested_indexes = _frame_indexes(node)
    candidates = load_canvas_candidate_history(db, owner, run_id, node, media_type)
    seen = {(item.asset_id, item.frame_index) for item in candidates}
    frames = load_storyboard_frames(db, script.id)
    for frame_index, frame in enumerate(frames):
        if requested_indexes is not None and frame_index not in requested_indexes:
            continue
        for url in _candidate_urls(frame, media_type):
            lineage = _candidate_lineage(frame, url, run_id, node.id)
            candidate = materialize_canvas_candidate(
                db,
                owner,
                media_type=media_type,
                url=url,
                frame_index=frame_index,
                clip_id=_clip_id(frame),
                prompt=_prompt(frame, media_type),
                model=_model(frame, node),
                duration_seconds=frame.get("duration_seconds"),
                selected_output_id=node.selected_output_id,
                parent_candidate_id=lineage.get("parent_candidate_id"),
                branch_task_id=lineage.get("branch_task_id"),
                branch_instruction=_string(lineage.get("branch_instruction")),
            )
            key = (candidate.asset_id, frame_index)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    if media_type == "video":
        candidates.extend(
            list_timeline_video_candidates(db, node, frames, requested_indexes, seen)
        )
    remember_canvas_candidate_history(db, run_id, node, candidates)
    db.commit()
    return ProductionCanvasMediaCandidateList(
        node_id=node.id,
        selected_output_id=node.selected_output_id,
        stale_impact=(
            canvas_stale_impact_nodes(state, node.id) if node.selected_output_id else []
        ),
        candidates=candidates,
    )


def approve_canvas_media_candidate(
    db: Session,
    user: User,
    run_id: str,
    node_id: str,
    candidate_id: int,
) -> ProductionCanvasRunResponse:
    require_canvas_access(db, user, run_id, "approve")
    review = list_canvas_media_candidates(db, user, run_id, node_id)
    candidate = next(
        (item for item in review.candidates if item.asset_id == candidate_id), None
    )
    if candidate is None:
        raise ValueError("canvas_candidate_not_found")
    state = load_canvas_saved_state(db, user, run_id)
    if state is None:
        raise ValueError("canvas_run_state_not_found")
    node = _review_node(state, node_id)
    _, output_port = _MEDIA_SKILLS[node.skill]
    reviewed_at = datetime.now(timezone.utc)
    set_canvas_candidate_review(
        db,
        run_id=run_id,
        node_id=node_id,
        candidate_id=candidate.asset_id,
        review_state="approved",
        reviewed_by=user.id,
        reviewed_at=reviewed_at,
    )
    updated = node.model_copy(
        update={
            "status": "approved",
            "definition_version": node.definition_version + 1,
            "selected_output_id": candidate.asset_id,
            "selected_output_url": candidate.url,
            "selected_output_reviewed_by": user.id,
            "selected_output_reviewed_at": reviewed_at,
            "outputs": {
                **node.outputs,
                output_port: candidate.url,
                "approved_asset_id": candidate.asset_id,
                "selected_output_id": candidate.asset_id,
                "selected_output_url": candidate.url,
                "selected_output_clip_id": candidate.clip_id,
                "selected_output_reviewed_by": user.id,
                "selected_output_reviewed_at": reviewed_at.isoformat(),
            },
        }
    )
    next_state = state.model_copy(
        update={
            "nodes": [updated if item.id == node_id else item for item in state.nodes]
        }
    )
    fingerprint = canvas_node_input_fingerprint(next_state, node_id)
    next_state = next_state.model_copy(
        update={
            "nodes": [
                (
                    item.model_copy(update={"execution_input_fingerprint": fingerprint})
                    if item.id == node_id
                    else item
                )
                for item in next_state.nodes
            ]
        }
    )
    run = save_canvas_state(db, user, run_id, next_state, capability="approve")
    if run is None:
        raise ValueError("canvas_run_state_not_found")
    return run
