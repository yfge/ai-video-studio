from __future__ import annotations

import json

from app.models.story_structure import Environment
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from app.schemas.production_canvas import (
    ProductionCanvasNodeExecution,
    ProductionCanvasPlanRequest,
    ProductionCanvasSavedEdge,
    ProductionCanvasSavedNode,
    ProductionCanvasSavedState,
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillResult,
    ProductionCanvasViewport,
)
from app.services.production_canvas.executor import execute_canvas_skill
from app.services.production_canvas.graph_runtime import apply_canvas_node_execution
from app.services.production_canvas.run_persistence import (
    attach_canvas_run,
    persist_canvas_skill_run,
    save_canvas_state,
)
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


def test_canvas_brief_and_asset_skills_execute_without_dispatcher_gap(db_session):
    user = _user(db_session, "canvas_immediate_skill_owner")
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        tags=["轻喜剧"],
        is_active=True,
    )
    environment = Environment(
        user_id=user.id,
        name="共享办公区",
        category="indoor",
        tags=["办公室"],
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()
    db_session.refresh(virtual_ip)
    db_session.refresh(environment)
    db_session.add(
        VirtualIPEnvironment(
            user_id=user.id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            environment_id=environment.id,
            environment_business_id=environment.business_id,
            usage_type="main_scene",
            is_default=True,
        )
    )
    db_session.commit()

    brief = execute_canvas_skill(
        db_session,
        user,
        ProductionCanvasSkillExecuteRequest(
            prompt="基于林妹妹做第 4 集，办公室轻喜剧",
            skill="brief.compose",
            run_id="canvas-run-immediate",
        ),
    )
    assets = execute_canvas_skill(
        db_session,
        user,
        ProductionCanvasSkillExecuteRequest(
            prompt="基于林妹妹做第 4 集，办公室轻喜剧",
            skill="asset.select",
            virtual_ip_id=virtual_ip.id,
            environment_id=environment.id,
            run_id="canvas-run-immediate",
        ),
    )

    assert brief.skill_result.status == "review"
    assert brief.skill_result.outputs["prompt"] == "基于林妹妹做第 4 集，办公室轻喜剧"
    assert "dispatcher" not in brief.skill_result.outputs.get("required_inputs", [])
    assert assets.skill_result.status == "review"
    assert assets.skill_result.outputs["virtual_ip_ids"] == [virtual_ip.id]
    assert assets.skill_result.outputs["environment_ids"] == [environment.id]
    assert "dispatcher" not in assets.skill_result.outputs.get("required_inputs", [])


def test_graph_execution_drops_stale_clip_before_downstream_resolution():
    state = ProductionCanvasSavedState(
        nodes=[
            ProductionCanvasSavedNode(
                id="timeline",
                label="Timeline",
                title="Timeline",
                status="review",
                x=0,
                y=0,
                width=200,
                kind="pipeline",
                skill="timeline.build",
                outputs={
                    "story_id": 60,
                    "episode_id": 170,
                    "script_id": 140,
                    "timeline_id": 501,
                    "timeline_version": 7,
                    "clip_id": "old-clip",
                    "provider_evidence": "keep-me",
                },
            )
        ],
        viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
    )
    updated = apply_canvas_node_execution(
        state,
        ProductionCanvasNodeExecution(
            node_id="timeline",
            resolved_context={
                "story_id": 61,
                "episode_id": 175,
                "script_id": 301,
                "timeline_id": 502,
                "timeline_version": 1,
            },
            skill_result=ProductionCanvasSkillResult(
                skill="timeline.build",
                label="Timeline",
                status="review",
                title="Timeline",
                detail="新版本",
                outputs={"timeline_id": 502, "timeline_version": 1},
            ),
        ),
    )

    assert updated.nodes[0].outputs == {
        "provider_evidence": "keep-me",
        "story_id": 61,
        "episode_id": 175,
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 1,
    }


def test_canvas_report_summarizes_run_state_without_task_context(db_session):
    user = _user(db_session, "canvas_report_run_owner")
    request = ProductionCanvasPlanRequest(prompt="汇总画布执行证据")
    plan = build_canvas_skill_plan(db_session, user, request)
    task = persist_canvas_skill_run(db_session, user, request, plan)
    run = attach_canvas_run(plan, task)
    media_task = Task(
        title="画布视频生成",
        task_type=TaskType.VIDEO_GENERATION,
        status=TaskStatus.COMPLETED,
        parameters=json.dumps(
            {"model": "minimax:video-01", "frame_indexes": [1]},
            ensure_ascii=False,
        ),
        target_business_id=run.run_id,
        result_file_path="/tmp/canvas-video.mp4",
        user_id=user.id,
    )
    db_session.add(media_task)
    db_session.commit()
    db_session.refresh(media_task)
    provider_task = VideoGenerationTask(
        task_id=media_task.id,
        script_id=None,
        frame_index=1,
        user_id=user.id,
        provider="minimax",
        provider_task_id="provider-video-1",
        model="video-01",
        model_type="image_to_video",
        result=json.dumps(
            {
                "provider_used": "minimax",
                "model_used": "video-01",
                "usage": {"credits": 2},
                "cost": {"currency": "CNY", "amount": 1.2},
            },
            ensure_ascii=False,
        ),
        generation_metadata={"provider": "minimax", "model": "video-01"},
        status=VideoGenerationTaskStatus.SUCCEEDED,
    )
    db_session.add(provider_task)
    db_session.commit()
    db_session.refresh(provider_task)
    save_canvas_state(
        db_session,
        user,
        run.run_id or "",
        ProductionCanvasSavedState(
            nodes=[
                ProductionCanvasSavedNode(
                    id="skill-script",
                    label="Script Skill",
                    title="已提交剧本任务",
                    status="running",
                    x=100,
                    y=120,
                    width=220,
                    kind="skill_result",
                    skill="script.generate",
                    outputs={
                        "dispatched_task_id": media_task.id,
                        "task_status": "completed",
                    },
                ),
                ProductionCanvasSavedNode(
                    id="note-1",
                    label="便签",
                    title="需要人工确认镜头风格",
                    status="review",
                    x=360,
                    y=160,
                    width=190,
                    kind="note",
                ),
            ],
            viewport=ProductionCanvasViewport(x=0, y=0, zoom=1),
            selected_node_id="note-1",
            edges=[
                ProductionCanvasSavedEdge(from_node="skill-script", to_node="note-1")
            ],
        ),
    )

    summary = execute_canvas_skill(
        db_session,
        user,
        ProductionCanvasSkillExecuteRequest(
            prompt="汇总画布执行证据",
            skill="report.summarize",
            run_id=run.run_id,
        ),
    )

    assert summary.skill_result.status == "review"
    assert summary.task_id == task.id
    assert summary.skill_result.outputs["report_source"] == "production_canvas_run"
    assert summary.skill_result.outputs["node_count"] == 2
    assert summary.skill_result.outputs["edge_count"] == 1
    assert summary.skill_result.outputs["status_counts"] == {"running": 1, "review": 1}
    assert summary.skill_result.outputs["execution_task_ids"] == [media_task.id]
    assert summary.skill_result.outputs["provider_counts"] == {"minimax": 1}
    assert summary.skill_result.outputs["model_counts"] == {"video-01": 1}
    assert summary.skill_result.outputs["usage_totals"] == {"credits": 2}
    lineage = summary.skill_result.outputs["task_lineage"][0]
    assert lineage["task_id"] == media_task.id
    assert lineage["task_type"] == "video_generation"
    assert lineage["task_status"] == "completed"
    assert lineage["requested_model"] == "minimax:video-01"
    assert lineage["requested_provider"] == "minimax"
    assert lineage["frame_indexes"] == [1]
    assert lineage["result_file_path"] == "/tmp/canvas-video.mp4"
    provider_lineage = lineage["provider_tasks"][0]
    assert provider_lineage["video_generation_task_id"] == provider_task.id
    assert provider_lineage["provider"] == "minimax"
    assert provider_lineage["provider_task_id"] == "provider-video-1"
    assert provider_lineage["model"] == "video-01"
    assert provider_lineage["model_type"] == "image_to_video"
    assert provider_lineage["status"] == "succeeded"
    assert provider_lineage["frame_index"] == 1
    assert provider_lineage["usage"] == {"credits": 2}
    assert provider_lineage["cost"] == {"currency": "CNY", "amount": 1.2}
    assert summary.skill_result.outputs["selected_node_id"] == "note-1"
