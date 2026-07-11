from datetime import datetime, timezone

from app.models.user import User
from app.schemas.production_canvas import ProductionCanvasRunResponse
from app.services.production_canvas.stale_runtime import canvas_node_input_fingerprint
from sqlalchemy.orm import Session

from .access_control import require_canvas_access
from .candidate_review import list_canvas_media_candidates
from .candidate_review_state import set_canvas_candidate_review
from .run_persistence import (
    load_canvas_saved_state,
    load_canvas_skill_run,
    save_canvas_state,
)

_OUTPUT_PORTS = {
    "image.candidates": "approved_image",
    "video.candidates": "approved_video",
}
_SELECTED_OUTPUT_KEYS = {
    "approved_asset_id",
    "selected_output_clip_id",
    "selected_output_id",
    "selected_output_reviewed_at",
    "selected_output_reviewed_by",
    "selected_output_url",
}


def reject_canvas_media_candidate(
    db: Session,
    user: User,
    run_id: str,
    node_id: str,
    candidate_id: int,
    reason: str | None,
) -> ProductionCanvasRunResponse:
    require_canvas_access(db, user, run_id, "approve")
    review = list_canvas_media_candidates(db, user, run_id, node_id)
    if not any(item.asset_id == candidate_id for item in review.candidates):
        raise ValueError("canvas_candidate_not_found")
    state = load_canvas_saved_state(db, user, run_id)
    if state is None:
        raise ValueError("canvas_run_state_not_found")
    node = next((item for item in state.nodes if item.id == node_id), None)
    if node is None:
        raise ValueError("canvas_node_not_found")
    output_port = _OUTPUT_PORTS.get(node.skill or "")
    if output_port is None:
        raise ValueError("canvas_node_not_reviewable")
    reviewed_at = datetime.now(timezone.utc)
    set_canvas_candidate_review(
        db,
        run_id=run_id,
        node_id=node_id,
        candidate_id=candidate_id,
        review_state="rejected",
        reviewed_by=user.id,
        reviewed_at=reviewed_at,
        rejection_reason=reason,
    )
    if node.selected_output_id != candidate_id:
        db.commit()
        run = load_canvas_skill_run(db, user, run_id)
        if run is None:
            raise ValueError("canvas_run_state_not_found")
        return run

    outputs = {
        key: value
        for key, value in node.outputs.items()
        if key not in _SELECTED_OUTPUT_KEYS and key != output_port
    }
    updated = node.model_copy(
        update={
            "status": "review",
            "definition_version": node.definition_version + 1,
            "outputs": outputs,
            "selected_output_id": None,
            "selected_output_url": None,
            "selected_output_reviewed_by": None,
            "selected_output_reviewed_at": None,
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
