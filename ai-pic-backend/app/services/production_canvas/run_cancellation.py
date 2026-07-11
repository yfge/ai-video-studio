from __future__ import annotations

from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.production_canvas import ProductionCanvasRunActionResponse
from app.services.production_canvas.run_persistence import (
    load_canvas_skill_run,
    save_canvas_state,
)
from app.services.task_control_service import TaskControlService
from sqlalchemy.orm import Session


def cancel_canvas_run(
    db: Session, user: User, run_id: str
) -> ProductionCanvasRunActionResponse:
    current = load_canvas_skill_run(db, user, run_id)
    if current is None:
        raise ValueError("production_canvas_run_not_found")
    if current.saved_state is None or current.saved_state.graph_version != 2:
        raise ValueError("production_canvas_graph_not_executable")
    tasks = TaskRepository(db).list_active_for_target(
        user_id=user.id, target_business_id=run_id
    )
    service = TaskControlService(db)
    cancelled = [service.cancel_task(task.id, user).id for task in tasks]
    cancelled_ids = set(cancelled)
    nodes = []
    for node in current.saved_state.nodes:
        outputs = dict(node.outputs or {})
        task_ids = {outputs.get("task_id"), outputs.get("dispatched_task_id")}
        if cancelled_ids.intersection(task_ids):
            outputs["task_status"] = "cancelled"
            node = node.model_copy(update={"status": "cancelled", "outputs": outputs})
        nodes.append(node)
    run = save_canvas_state(
        db,
        user,
        run_id,
        current.saved_state.model_copy(update={"nodes": nodes}),
    )
    assert run is not None
    return ProductionCanvasRunActionResponse(
        action="cancel", run=run, cancelled_task_ids=cancelled
    )
