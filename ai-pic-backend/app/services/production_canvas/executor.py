from __future__ import annotations

from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.production_canvas import (
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.services.production_canvas.execution_common import (
    blocked_result,
    load_script,
    skill_definition,
)
from app.services.production_canvas.media_execution import (
    execute_report_summary,
    execute_storyboard_images,
    execute_storyboard_video_candidates,
)
from app.services.script.generation_queue import queue_script_generation_task
from app.services.script.timeline_pipeline_queue import queue_timeline_pipeline_task
from app.services.storyboard.generation_queue import queue_storyboard_generation_task
from sqlalchemy.orm import Session


def _execute_script_generation(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("script.generate")
    if request.episode_id is None:
        return blocked_result(
            request,
            title="Script Skill 等待剧集上下文",
            detail="需要先绑定 episode_id，之后才会提交现有 SCRIPT_GENERATION 任务。",
            required_inputs=["episode_id"],
        )

    script_request = ScriptGenerationRequest(
        episode_id=request.episode_id,
        generation_mode="production",
        auto_timeline_pipeline=True,
        additional_requirements=request.prompt,
    )
    task = queue_script_generation_task(
        db,
        user,
        script_request,
        title=f"生产画布执行 Script Skill - 剧集{request.episode_id}",
        description="Production canvas script.generate skill dispatch",
        prompt=request.prompt,
        target_business_id=request.run_id,
    )
    return _running_response(
        skill_id="script.generate",
        label=skill.label if skill else "Script Skill",
        title="已提交现有剧本生成任务",
        detail="后台已通过现有 SCRIPT_GENERATION Celery worker 执行。",
        task=task,
        outputs={"episode_id": request.episode_id},
        reuse_targets=skill.reuse_targets if skill else [],
        canvas_run_id=request.run_id,
    )


def _execute_storyboard_generation(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("storyboard.plan")
    script = load_script(db, user, request.script_id)
    if script is None:
        return blocked_result(
            request,
            title="Storyboard Skill 等待剧本上下文",
            detail="需要先绑定 script_id，之后才会提交现有 STORYBOARD_GENERATION 任务。",
            required_inputs=["script_id"],
        )

    task = queue_storyboard_generation_task(
        db,
        user,
        script,
        title=f"生产画布执行 Storyboard Skill - 剧本{script.id}",
        description="Production canvas storyboard.plan skill dispatch",
        prompt=request.prompt,
        target_business_id=request.run_id,
    )
    return _running_response(
        skill_id="storyboard.plan",
        label=skill.label if skill else "Storyboard Skill",
        title="已提交现有分镜生成任务",
        detail="后台已通过现有 STORYBOARD_GENERATION Celery worker 执行。",
        task=task,
        outputs={"script_id": script.id, "episode_id": script.episode_id},
        reuse_targets=skill.reuse_targets if skill else [],
        canvas_run_id=request.run_id,
    )


def _execute_timeline_pipeline(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("timeline.assemble")
    script = load_script(db, user, request.script_id)
    if script is None:
        return blocked_result(
            request,
            title="Timeline Skill 等待剧本上下文",
            detail="需要先绑定 script_id，之后才会提交现有 TIMELINE_PIPELINE 任务。",
            required_inputs=["script_id"],
        )

    task = queue_timeline_pipeline_task(
        db,
        user,
        script,
        title=f"生产画布执行 Timeline Skill - 剧本{script.id}",
        description="Production canvas timeline.assemble skill dispatch",
        prompt=request.prompt,
        target_business_id=request.run_id,
    )
    return _running_response(
        skill_id="timeline.assemble",
        label=skill.label if skill else "Timeline Skill",
        title="已提交现有时间线流水线任务",
        detail="后台已通过现有 TIMELINE_PIPELINE Celery worker 执行。",
        task=task,
        outputs={"script_id": script.id, "episode_id": script.episode_id},
        reuse_targets=skill.reuse_targets if skill else [],
        canvas_run_id=request.run_id,
    )


def _running_response(
    *,
    skill_id: str,
    label: str,
    title: str,
    detail: str,
    task,
    outputs: dict,
    reuse_targets: list,
    canvas_run_id: str | None,
) -> ProductionCanvasSkillExecuteResponse:
    return ProductionCanvasSkillExecuteResponse(
        task_id=task.id,
        task_status=task.status.value,
        skill_result=ProductionCanvasSkillResult(
            skill=skill_id,
            label=label,
            status="running",
            title=title,
            detail=detail,
            outputs={
                **outputs,
                "dispatched_task_id": task.id,
                "task_status": task.status.value,
                **({"canvas_run_id": canvas_run_id} if canvas_run_id else {}),
            },
            reuse_targets=reuse_targets,
        ),
    )


def execute_canvas_skill(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    if request.skill == "script.generate":
        return _execute_script_generation(db, user, request)
    if request.skill == "storyboard.plan":
        return _execute_storyboard_generation(db, user, request)
    if request.skill == "image.candidates":
        return execute_storyboard_images(db, user, request)
    if request.skill == "video.candidates":
        return execute_storyboard_video_candidates(db, user, request)
    if request.skill == "timeline.assemble":
        return _execute_timeline_pipeline(db, user, request)
    if request.skill == "report.summarize":
        return execute_report_summary(db, user, request)

    return blocked_result(
        request,
        title=f"{request.skill} 暂未接入自动执行",
        detail="当前 Skill 已登记后台复用目标，但还没有接入明确的任务派发器。",
        required_inputs=["dispatcher"],
    )
