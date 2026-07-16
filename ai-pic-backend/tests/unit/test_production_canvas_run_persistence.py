from __future__ import annotations

import json

from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.production_canvas import (
    ProductionCanvasPlanRequest,
    ProductionCanvasSavedEdge,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasViewport,
)
from app.services.production_canvas.run_persistence import (
    attach_canvas_run,
    load_canvas_skill_run,
    persist_canvas_skill_run,
    save_canvas_client_state,
    save_canvas_state,
)
from app.services.production_canvas.run_requests import request_for_canvas_node
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


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


def test_canvas_run_can_save_and_reload_canvas_state(db_session):
    user = _user(db_session, "canvas_run_persistence_owner")
    source_task = Task(
        title="画布来源任务",
        task_type=TaskType.TEXT_GENERATION,
        status=TaskStatus.COMPLETED,
        parameters=json.dumps({}),
        user_id=user.id,
    )
    db_session.add(source_task)
    db_session.commit()
    db_session.refresh(source_task)
    request = ProductionCanvasPlanRequest(
        prompt="保存并恢复画布状态",
        task_id=source_task.id,
    )
    plan = build_canvas_skill_plan(db_session, user, request)
    assert plan.resolved_context.task_id == source_task.id
    task = persist_canvas_skill_run(db_session, user, request, plan)
    run = attach_canvas_run(plan, task)

    saved = save_canvas_state(
        db_session,
        user,
        run.run_id or "",
        ProductionCanvasSavedState(
            nodes=[
                ProductionCanvasSavedNode(
                    id="brief",
                    label="Brief",
                    title="已调整位置的 brief",
                    status="review",
                    x=88,
                    y=144,
                    width=220,
                    kind="skill_result",
                    skill="brief.compose",
                    outputs={
                        "canvas_run_id": run.run_id,
                        "task_id": source_task.id,
                    },
                ),
                ProductionCanvasSavedNode(
                    id="note-1",
                    label="便签",
                    title="人工备注",
                    status="review",
                    x=320,
                    y=260,
                    width=190,
                    kind="note",
                    detail="保留这一版分镜方向",
                ),
            ],
            viewport=ProductionCanvasViewport(x=12, y=34, zoom=0.8),
            selected_node_id="note-1",
            edges=[ProductionCanvasSavedEdge(from_node="brief", to_node="note-1")],
        ),
    )

    assert saved is not None
    assert saved.saved_state is not None
    assert saved.saved_state.selected_node_id == "note-1"

    reloaded = load_canvas_skill_run(db_session, user, run.run_id or "")

    assert reloaded is not None
    assert reloaded.run_id == run.run_id
    assert reloaded.task_id == task.id
    assert reloaded.resolved_context.task_id == source_task.id
    assert reloaded.saved_state is not None
    assert reloaded.saved_state.viewport.zoom == 0.8
    assert reloaded.saved_state.nodes[0].x == 88
    assert reloaded.saved_state.nodes[1].detail == "保留这一版分镜方向"
    assert reloaded.saved_state.edges[0].from_node == "brief"
    assert reloaded.saved_state.edges[0].to_node == "note-1"
    execute_request = request_for_canvas_node(
        reloaded,
        ProductionCanvasSavedNode(
            id="report",
            label="Report",
            title="Report",
            status="ready",
            x=0,
            y=0,
            width=200,
            kind="pipeline",
            skill="report.summarize",
        ),
    )
    assert execute_request.task_id == source_task.id


def test_canvas_run_ignores_malformed_saved_output_context(db_session):
    user = _user(db_session, "canvas_run_malformed_context_owner")
    request = ProductionCanvasPlanRequest(prompt="恢复损坏的旧画布上下文")
    plan = build_canvas_skill_plan(db_session, user, request)
    task = persist_canvas_skill_run(db_session, user, request, plan)
    run = attach_canvas_run(plan, task)

    saved = save_canvas_state(
        db_session,
        user,
        run.run_id or "",
        ProductionCanvasSavedState(
            nodes=[
                ProductionCanvasSavedNode(
                    id="legacy",
                    label="旧节点",
                    title="损坏上下文",
                    status="review",
                    x=0,
                    y=0,
                    width=200,
                    kind="note",
                    outputs={
                        "story_id": "not-an-id",
                        "episode_id": -7,
                        "timeline_version": False,
                        "clip_id": "   ",
                        "task_id": {"unexpected": "shape"},
                    },
                )
            ],
            viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
        ),
    )

    assert saved is not None
    assert saved.resolved_context.model_dump(exclude_none=True) == {}
    assert all(
        result.outputs.get("story_id") != "not-an-id" for result in saved.skill_results
    )
    reloaded = load_canvas_skill_run(db_session, user, run.run_id or "")
    assert reloaded is not None
    assert reloaded.resolved_context.model_dump(exclude_none=True) == {}


def test_canvas_run_rewrites_stale_plural_aliases_to_canonical_context(db_session):
    user = _user(db_session, "canvas_run_plural_alias_owner")
    request = ProductionCanvasPlanRequest(prompt="恢复时统一上下文别名")
    plan = build_canvas_skill_plan(db_session, user, request)
    task = persist_canvas_skill_run(db_session, user, request, plan)
    payload = json.loads(task.parameters or "{}")
    payload["resolved_context"] = {"virtual_ip_id": 85, "environment_id": 14}
    payload["skill_results"][0]["outputs"].update(
        {"virtual_ip_ids": [84], "environment_ids": [13]}
    )
    payload["saved_state"] = {
        "nodes": [
            {
                "id": "brief",
                "label": "Brief",
                "title": "Brief",
                "status": "review",
                "x": 0,
                "y": 0,
                "width": 200,
                "kind": "pipeline",
                "skill": "brief.compose",
                "outputs": {"virtual_ip_id": 85, "environment_id": 14},
            }
        ],
        "edges": [],
        "sections": [],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }
    task.parameters = json.dumps(payload)
    db_session.commit()

    reloaded = load_canvas_skill_run(db_session, user, task.business_id)

    assert reloaded is not None
    outputs = reloaded.skill_results[0].outputs
    assert outputs["virtual_ip_id"] == 85
    assert outputs["environment_id"] == 14
    assert outputs["virtual_ip_ids"] == [85]
    assert outputs["environment_ids"] == [14]


def test_stale_client_cannot_delete_a_context_only_global_node(db_session):
    user = _user(db_session, "canvas_run_deleted_context_node_owner")
    request = ProductionCanvasPlanRequest(prompt="旧客户端不能回退 Run 上下文")
    plan = build_canvas_skill_plan(db_session, user, request)
    task = persist_canvas_skill_run(db_session, user, request, plan)
    global_node = ProductionCanvasSavedNode(
        id="timeline-context",
        label="Timeline",
        title="全局 Timeline 上下文",
        status="ready",
        x=0,
        y=0,
        width=200,
        kind="pipeline",
        skill="render.timeline",
        outputs={
            "timeline_id": 501,
            "timeline_version": 2,
            "clip_id": "clip-a",
        },
    )
    scoped_video = ProductionCanvasSavedNode(
        id="video-b",
        label="Video B",
        title="分镜 B",
        status="review",
        x=240,
        y=0,
        width=200,
        kind="pipeline",
        skill="video.candidates",
        outputs={
            "script_id": 140,
            "timeline_id": 501,
            "timeline_version": 1,
            "clip_id": "clip-b",
            "frame_indexes": [1],
        },
    )
    current = save_canvas_state(
        db_session,
        user,
        task.business_id,
        ProductionCanvasSavedState(
            nodes=[global_node, scoped_video],
            viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
        ),
    )
    assert current is not None
    assert current.resolved_context.timeline_version == 2
    assert current.resolved_context.clip_id == "clip-a"

    reloaded = save_canvas_client_state(
        db_session,
        user,
        task.business_id,
        ProductionCanvasSavedState(
            nodes=[scoped_video],
            viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
        ),
    )

    assert reloaded is not None
    assert reloaded.resolved_context.timeline_id == 501
    assert reloaded.resolved_context.timeline_version == 2
    assert reloaded.resolved_context.clip_id == "clip-a"


def test_canvas_run_state_is_user_scoped(db_session):
    owner = _user(db_session, "canvas_run_scope_owner")
    other = _user(db_session, "canvas_run_scope_other")
    request = ProductionCanvasPlanRequest(prompt="只允许创建者读取")
    plan = build_canvas_skill_plan(db_session, owner, request)
    task = persist_canvas_skill_run(db_session, owner, request, plan)
    run = attach_canvas_run(plan, task)

    assert load_canvas_skill_run(db_session, other, run.run_id or "") is None
