from __future__ import annotations

import json

from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
    ProductionCanvasViewport,
)
from app.services.production_canvas.execution_persistence import (
    save_canvas_execution_response,
)
from app.services.production_canvas.run_persistence import (
    load_canvas_skill_run,
    persist_canvas_skill_run,
    save_canvas_client_state,
    save_canvas_state,
)
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


def test_completed_current_child_task_advances_run_context_on_autosave(db_session):
    user = User(
        username="canvas_terminal_task_owner",
        email="canvas-terminal-task@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    request = ProductionCanvasPlanRequest(prompt="异步剧本完成后继续")
    plan = build_canvas_skill_plan(db_session, user, request)
    run_task = persist_canvas_skill_run(db_session, user, request, plan)
    child = Task(
        title="剧本生成",
        task_type=TaskType.SCRIPT_GENERATION,
        status=TaskStatus.PROCESSING,
        parameters=json.dumps({"episode_id": 175}),
        user_id=user.id,
    )
    db_session.add(child)
    db_session.commit()
    state = ProductionCanvasSavedState(
        nodes=[
            ProductionCanvasSavedNode(
                id="script",
                label="Script",
                title="Script",
                status="ready",
                x=0,
                y=0,
                width=220,
                kind="pipeline",
                skill="script.generate",
                outputs={"episode_id": 175},
            )
        ],
        viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
    )
    assert save_canvas_state(db_session, user, run_task.business_id, state)
    assert save_canvas_execution_response(
        db_session,
        user,
        run_task.business_id,
        ProductionCanvasSkillExecuteResponse(
            node_id="script",
            task_id=child.id,
            task_status="pending",
            resolved_context={"episode_id": 175, "task_id": child.id},
            skill_result=ProductionCanvasSkillResult(
                skill="script.generate",
                label="Script",
                status="running",
                title="Script queued",
                detail="pending",
                outputs={
                    "episode_id": 175,
                    "dispatched_task_id": child.id,
                    "task_status": "pending",
                },
            ),
        ),
    )
    child.status = TaskStatus.COMPLETED
    child.parameters = json.dumps(
        {"resolved_context": {"episode_id": 175, "script_id": 301}}
    )
    child.result_file_path = "script:301"
    db_session.commit()
    incoming = state.model_copy(
        update={
            "nodes": [
                state.nodes[0].model_copy(
                    update={
                        "status": "review",
                        "outputs": {
                            "episode_id": 175,
                            "script_id": 301,
                            "dispatched_task_id": child.id,
                            "task_id": child.id,
                            "task_status": "completed",
                        },
                    }
                )
            ]
        }
    )

    saved = save_canvas_client_state(db_session, user, run_task.business_id, incoming)
    assert saved is not None and saved.saved_state is not None
    assert saved.resolved_context.episode_id == 175
    assert saved.resolved_context.script_id == 301
    assert saved.resolved_context.task_id == child.id
    assert saved.saved_state.nodes[0].outputs["script_id"] == 301

    reloaded = load_canvas_skill_run(db_session, user, run_task.business_id)
    assert reloaded is not None
    assert reloaded.resolved_context.script_id == 301
