from __future__ import annotations

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
)
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


def test_first_late_client_put_cannot_undo_pre_autosave_execution(db_session):
    user = User(
        username="canvas_first_state_race_owner",
        email="canvas-first-state-race@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    request = ProductionCanvasPlanRequest(prompt="先执行后自动保存")
    plan = build_canvas_skill_plan(db_session, user, request)
    task = persist_canvas_skill_run(db_session, user, request, plan)
    current = {
        "story_id": 61,
        "episode_id": 175,
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 1,
    }
    assert save_canvas_execution_response(
        db_session,
        user,
        task.business_id,
        ProductionCanvasSkillExecuteResponse(
            node_id="script",
            resolved_context=current,
            skill_result=ProductionCanvasSkillResult(
                skill="script.generate",
                label="Script",
                status="review",
                title="Script generated",
                detail="completed before autosave",
                outputs=current,
            ),
        ),
    )
    stale = ProductionCanvasSavedState(
        nodes=[
            ProductionCanvasSavedNode(
                id="script",
                label="Script",
                title="Stale script",
                status="running",
                x=0,
                y=0,
                width=220,
                kind="pipeline",
                skill="script.generate",
                outputs={
                    "story_id": 60,
                    "episode_id": 170,
                    "script_id": 140,
                    "timeline_id": 501,
                    "timeline_version": 7,
                    "clip_id": "old-clip",
                },
            )
        ],
        viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
    )

    saved = save_canvas_client_state(db_session, user, task.business_id, stale)
    assert saved is not None and saved.saved_state is not None
    assert saved.resolved_context.model_dump(exclude_none=True) == current
    assert saved.saved_state.nodes[0].outputs["script_id"] == 301
    assert saved.saved_state.nodes[0].outputs["timeline_id"] == 502
    assert "clip_id" not in saved.saved_state.nodes[0].outputs

    retried = save_canvas_client_state(db_session, user, task.business_id, stale)
    assert retried is not None and retried.saved_state is not None
    assert retried.resolved_context.model_dump(exclude_none=True) == current
    assert retried.saved_state.nodes[0].outputs["script_id"] == 301
    assert retried.saved_state.nodes[0].outputs["timeline_id"] == 502
    assert "clip_id" not in retried.saved_state.nodes[0].outputs

    switched_context = {
        "story_id": 62,
        "episode_id": 176,
        "script_id": 302,
        "timeline_id": 503,
        "timeline_version": 2,
    }
    acknowledged = saved.saved_state.model_copy(
        update={
            "nodes": [
                saved.saved_state.nodes[0].model_copy(
                    update={"outputs": switched_context}
                )
            ]
        }
    )
    switched = save_canvas_client_state(
        db_session, user, task.business_id, acknowledged
    )
    assert switched is not None and switched.saved_state is not None
    assert switched.resolved_context.model_dump(exclude_none=True) == switched_context
    assert switched.saved_state.resolved_context_revision == 1

    reloaded = load_canvas_skill_run(db_session, user, task.business_id)
    assert reloaded is not None
    assert reloaded.resolved_context.model_dump(exclude_none=True) == switched_context
