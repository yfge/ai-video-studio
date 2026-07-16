from __future__ import annotations

from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasPlanRequest,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
    ProductionCanvasViewport,
)
from app.services.production_canvas.execution_persistence import (
    _is_scoped_execution,
    save_canvas_execution_response,
)
from app.services.production_canvas.run_persistence import (
    load_canvas_skill_run,
    persist_canvas_skill_run,
    save_canvas_state,
)
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


def _user(db) -> User:
    user = User(
        username="canvas_scoped_execution_owner",
        email="canvas-scoped-execution@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _node(node_id: str, skill: str, outputs: dict, x: int):
    return ProductionCanvasSavedNode(
        id=node_id,
        label=node_id,
        title=node_id,
        status="review",
        x=x,
        y=0,
        width=220,
        kind="pipeline",
        skill=skill,
        outputs=outputs,
    )


def _execute(db, user, run_id, node_id, skill, context, outputs):
    assert save_canvas_execution_response(
        db,
        user,
        run_id,
        ProductionCanvasSkillExecuteResponse(
            node_id=node_id,
            resolved_context=context,
            skill_result=ProductionCanvasSkillResult(
                skill=skill,
                label=node_id,
                status="review",
                title=node_id,
                detail="scoped execution",
                outputs=outputs,
            ),
        ),
    )


def test_scoped_execution_is_detected_before_the_first_canvas_autosave():
    for status, outputs in (
        ("running", {"queued_frame_indexes": [0], "script_id": 140}),
        ("blocked", {"required_inputs": ["storyboard_frames"]}),
    ):
        execution = ProductionCanvasNodeExecution(
            skill_result=ProductionCanvasSkillResult(
                skill="image.candidates",
                label="Image",
                status=status,
                title="Image",
                detail=status,
                outputs=outputs,
            )
        )
        assert _is_scoped_execution(None, execution)


def test_scoped_execution_order_cannot_replace_run_timeline(db_session):
    user = _user(db_session)
    request = ProductionCanvasPlanRequest(prompt="分镜执行隔离")
    plan = build_canvas_skill_plan(db_session, user, request)
    task = persist_canvas_skill_run(db_session, user, request, plan)
    global_context = {
        "virtual_ip_id": 85,
        "environment_id": 14,
        "story_id": 61,
        "episode_id": 175,
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 1,
        "clip_id": "clip-global",
        "task_id": 700,
    }
    scoped_a = {
        "virtual_ip_id": 84,
        "environment_id": 13,
        "story_id": 60,
        "episode_id": 170,
        "script_id": 140,
        "timeline_id": 501,
        "timeline_version": 7,
        "clip_id": "clip-a",
        "task_id": 801,
    }
    scoped_b = {
        "virtual_ip_id": 86,
        "environment_id": 15,
        "story_id": 62,
        "episode_id": 176,
        "script_id": 150,
        "timeline_id": 600,
        "timeline_version": 2,
        "clip_id": "clip-b",
        "task_id": 802,
    }
    state = ProductionCanvasSavedState(
        nodes=[
            _node("render", "timeline.render", global_context, 0),
            _node(
                "image-a",
                "image.candidates",
                {
                    **scoped_a,
                    "dispatched_task_id": 801,
                    "frame_indexes": [0],
                },
                240,
            ),
            _node(
                "video-b",
                "video.candidates",
                {
                    **scoped_b,
                    "dispatched_task_id": 802,
                    "frame_indexes": [1],
                },
                480,
            ),
        ],
        viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
    )
    saved = save_canvas_state(db_session, user, task.business_id, state)
    assert saved is not None
    assert saved.resolved_context.model_dump(exclude_none=True) == global_context

    _execute(
        db_session,
        user,
        task.business_id,
        "image-a",
        "image.candidates",
        scoped_a,
        {
            **scoped_a,
            "dispatched_task_id": 801,
            "queued_frame_indexes": [0],
        },
    )
    _execute(
        db_session,
        user,
        task.business_id,
        "video-b",
        "video.candidates",
        scoped_b,
        {
            **scoped_b,
            "dispatched_task_id": 802,
            "frame_indexes": [1],
        },
    )

    run = load_canvas_skill_run(db_session, user, task.business_id)
    assert run is not None and run.saved_state is not None
    assert run.resolved_context.model_dump(exclude_none=True) == global_context
    nodes = {node.id: node for node in run.saved_state.nodes}
    for key, value in global_context.items():
        assert nodes["render"].outputs[key] == value
    for key, value in scoped_a.items():
        assert nodes["image-a"].outputs[key] == value
    for key, value in scoped_b.items():
        assert nodes["video-b"].outputs[key] == value
