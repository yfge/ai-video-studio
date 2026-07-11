from app.models.user import User
from app.schemas.production_canvas import ProductionCanvasRunResponse
from app.schemas.production_canvas_review import ProductionCanvasCandidateBranchRequest
from sqlalchemy.orm import Session

from .access_control import require_canvas_access
from .candidate_activity import record_canvas_candidate_activity
from .execution_persistence import save_canvas_execution_response
from .executor import execute_canvas_skill
from .run_persistence import load_canvas_skill_run
from .run_requests import request_for_canvas_node


def branch_canvas_media_candidate(
    db: Session,
    user: User,
    run_id: str,
    node_id: str,
    branch: ProductionCanvasCandidateBranchRequest,
) -> ProductionCanvasRunResponse:
    require_canvas_access(db, user, run_id, "execute")
    run = load_canvas_skill_run(db, user, run_id)
    if run is None or run.saved_state is None:
        raise ValueError("canvas_run_state_not_found")
    node = next((item for item in run.saved_state.nodes if item.id == node_id), None)
    if node is None:
        raise ValueError("canvas_node_not_found")
    if node.skill not in {"image.candidates", "video.candidates"}:
        raise ValueError("canvas_node_not_reviewable")

    request = request_for_canvas_node(run, node).model_copy(
        update={
            "branch_parent_candidate_id": branch.candidate_id,
            "branch_instruction": branch.instruction,
        }
    )
    response = execute_canvas_skill(db, user, request)
    if not save_canvas_execution_response(db, user, run_id, response):
        raise ValueError("canvas_run_state_not_found")
    record_canvas_candidate_activity(
        db, user, run_id, "candidate.branched", branch.candidate_id, branch.instruction
    )
    updated = load_canvas_skill_run(db, user, run_id)
    if updated is None:
        raise ValueError("canvas_run_state_not_found")
    return updated
