from __future__ import annotations

import json

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
from app.services.task_result_context import build_task_result_context


def _user(db, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _run(db, user: User, prompt: str):
    request = ProductionCanvasPlanRequest(prompt=prompt)
    plan = build_canvas_skill_plan(db, user, request)
    task = persist_canvas_skill_run(db, user, request, plan)
    return task, task.business_id


def _node(node_id: str, outputs: dict, *, x: int = 0) -> ProductionCanvasSavedNode:
    return ProductionCanvasSavedNode(
        id=node_id,
        label=node_id.title(),
        title=node_id.title(),
        status="review",
        x=x,
        y=0,
        width=200,
        kind="pipeline",
        skill="brief.compose" if node_id == "brief" else "storyboard.plan",
        outputs=outputs,
    )


def test_execution_persistence_drops_stale_clip_on_timeline_change(db_session):
    user = _user(db_session, "canvas_execution_lineage_owner")
    task, run_id = _run(db_session, user, "执行后切换 Timeline")
    old_context = {
        "story_id": 60,
        "episode_id": 170,
        "script_id": 140,
        "timeline_id": 501,
        "timeline_version": 7,
        "clip_id": "old-clip",
    }
    saved = save_canvas_state(
        db_session,
        user,
        run_id,
        ProductionCanvasSavedState(
            nodes=[
                _node("brief", old_context),
                _node(
                    "storyboard",
                    {
                        **old_context,
                        "selected_output_clip_id": "old-clip",
                        "placed_timeline_clip_id": "old-clip",
                    },
                    x=240,
                ),
            ],
            viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
        ),
    )
    assert saved is not None

    assert save_canvas_execution_response(
        db_session,
        user,
        run_id,
        ProductionCanvasSkillExecuteResponse(
            node_id="brief",
            input_fingerprint="a" * 64,
            resolved_context=old_context,
            skill_result=ProductionCanvasSkillResult(
                skill="brief.compose",
                label="Brief",
                status="review",
                title="Brief",
                detail="其他节点已执行",
                outputs={"render_job_id": 9000},
            ),
        ),
    )
    preserved = load_canvas_skill_run(db_session, user, run_id)
    assert preserved is not None and preserved.saved_state is not None
    brief = next(node for node in preserved.saved_state.nodes if node.id == "brief")
    assert brief.definition_version == 1
    storyboard = next(
        node for node in preserved.saved_state.nodes if node.id == "storyboard"
    )
    assert storyboard.outputs["selected_output_clip_id"] == "old-clip"
    assert storyboard.outputs["placed_timeline_clip_id"] == "old-clip"

    assert save_canvas_execution_response(
        db_session,
        user,
        run_id,
        ProductionCanvasSkillExecuteResponse(
            node_id="brief",
            input_fingerprint="b" * 64,
            resolved_context={
                "story_id": 61,
                "episode_id": 175,
                "script_id": 301,
                "timeline_id": 502,
                "timeline_version": 1,
            },
            skill_result=ProductionCanvasSkillResult(
                skill="brief.compose",
                label="Brief",
                status="review",
                title="Brief",
                detail="Timeline 已更新",
                outputs={
                    "timeline_id": 502,
                    "timeline_version": 1,
                    "render_job_id": 9001,
                },
            ),
        ),
    )
    assert saved.saved_state is not None
    reloaded = save_canvas_client_state(db_session, user, run_id, saved.saved_state)

    assert reloaded is not None and reloaded.saved_state is not None
    assert reloaded.saved_state.nodes[0].definition_version == 1
    assert reloaded.resolved_context.timeline_id == 502
    assert reloaded.resolved_context.timeline_version == 1
    assert reloaded.resolved_context.clip_id is None
    assert reloaded.resolved_context.story_id == 61
    assert reloaded.resolved_context.episode_id == 175
    assert reloaded.resolved_context.script_id == 301
    assert "clip_id" not in reloaded.saved_state.nodes[0].outputs
    assert reloaded.saved_state.nodes[0].outputs["render_job_id"] == 9001
    assert reloaded.saved_state.nodes[1].outputs["timeline_id"] == 502
    assert reloaded.saved_state.nodes[1].outputs["timeline_version"] == 1
    assert "clip_id" not in reloaded.saved_state.nodes[1].outputs
    assert "selected_output_clip_id" not in reloaded.saved_state.nodes[1].outputs
    assert "placed_timeline_clip_id" not in reloaded.saved_state.nodes[1].outputs
    assert reloaded.saved_state.nodes[1].outputs["script_id"] == 301
    db_session.refresh(task)
    task_context = build_task_result_context(
        task_id=task.id,
        parameters=json.loads(task.parameters or "{}"),
        result_file_path=task.result_file_path,
    )
    assert task_context["story_id"] == 61
    assert task_context["episode_id"] == 175
    assert task_context["script_id"] == 301
    assert task_context["timeline_id"] == 502
    assert task_context["timeline_version"] == 1
    assert "clip_id" not in task_context


def test_execution_persistence_keeps_explicit_descendant_clears(db_session):
    user = _user(db_session, "canvas_execution_clear_owner")
    task, run_id = _run(db_session, user, "回到故事层")
    saved = save_canvas_state(
        db_session,
        user,
        run_id,
        ProductionCanvasSavedState(
            nodes=[
                _node(
                    "brief",
                    {
                        "story_id": 61,
                        "episode_id": 174,
                        "script_id": 144,
                        "timeline_id": 70,
                        "timeline_version": 6,
                        "clip_id": "old-clip",
                    },
                )
            ],
            viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
        ),
    )
    assert saved is not None

    assert save_canvas_execution_response(
        db_session,
        user,
        run_id,
        ProductionCanvasSkillExecuteResponse(
            node_id="brief",
            resolved_context={
                "virtual_ip_id": None,
                "environment_id": None,
                "story_id": 61,
                "episode_id": None,
                "script_id": None,
                "timeline_id": None,
                "timeline_version": None,
                "clip_id": None,
                "task_id": None,
            },
            skill_result=ProductionCanvasSkillResult(
                skill="brief.compose",
                label="Brief",
                status="review",
                title="Brief",
                detail="只保留故事上下文",
                outputs={},
            ),
        ),
    )
    reloaded = load_canvas_skill_run(db_session, user, run_id)

    assert reloaded is not None and reloaded.saved_state is not None
    assert reloaded.resolved_context.model_dump(exclude_none=True) == {"story_id": 61}
    assert reloaded.saved_state.nodes[0].outputs["story_id"] == 61
    for key in ("episode_id", "script_id", "timeline_id", "clip_id"):
        assert key not in reloaded.saved_state.nodes[0].outputs
    db_session.refresh(task)
    task_context = build_task_result_context(
        task_id=task.id,
        parameters=json.loads(task.parameters or "{}"),
        result_file_path=task.result_file_path,
    )
    assert task_context == {"story_id": 61, "task_id": task.id}
