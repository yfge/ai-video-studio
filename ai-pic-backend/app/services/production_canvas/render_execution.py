from __future__ import annotations

from app.models.timeline import Timeline
from app.models.user import User
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.production_canvas import (
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.schemas.timeline import RenderJobCreate, RenderJobResponse
from app.services.production_canvas.execution_common import (
    blocked_result,
    load_script,
    skill_definition,
)
from app.services.timeline_resolved_video_service import TimelineResolvedVideoService
from app.services.timeline_service import TimelineService
from sqlalchemy.orm import Session


def _current_timeline(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> Timeline | None:
    if request.timeline_id is not None:
        owner_id = None if user.is_admin or user.is_superuser else int(user.id)
        timeline = TimelineRepository(db).get_accessible(
            request.timeline_id,
            owner_id,
        )
        if timeline is None:
            return None
        if request.script_id is not None and timeline.script_id != request.script_id:
            return None
        if (
            request.timeline_version is not None
            and timeline.version != request.timeline_version
        ):
            return None
        return timeline
    script = load_script(db, user, request.script_id)
    if script is None:
        return None
    return TimelineRepository(db).get_latest_for_episode_script(
        episode_id=int(script.episode_id),
        script_id=int(script.id),
    )


def _job_outputs(job: RenderJobResponse) -> dict:
    output = job.output_asset
    output_url = output.file_url or output.file_path if output else None
    return {
        "timeline_id": job.timeline_id,
        "timeline_version": job.timeline_version,
        "render_job_id": job.id,
        "render_status": job.status,
        "render_progress": job.progress,
        "output_asset_id": job.output_asset_id,
        "output_url": output_url,
        "render_log": job.log,
    }


def _job_response(
    request: ProductionCanvasSkillExecuteRequest,
    job: RenderJobResponse,
    *,
    skill_id: str,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition(skill_id)
    succeeded = job.status == "succeeded" and bool(_job_outputs(job)["output_url"])
    active = job.status in {"queued", "running"}
    label = skill.label if skill else skill_id
    if skill_id == "timeline.export":
        title = "成片已就绪，可直接导出" if succeeded else "等待最终渲染完成"
        detail = "已读取最终成片资产。" if succeeded else "最终渲染仍在后台执行。"
    else:
        title = "最终渲染已完成" if succeeded else "已提交最终渲染任务"
        detail = (
            "成片资产已生成。" if succeeded else "后台正在按当前 Timeline 版本渲染。"
        )
    outputs = _job_outputs(job)
    if request.run_id:
        outputs["canvas_run_id"] = request.run_id
    return ProductionCanvasSkillExecuteResponse(
        skill_result=ProductionCanvasSkillResult(
            skill=skill_id,
            label=label,
            status="ready" if succeeded else "running" if active else "blocked",
            title=title,
            detail=detail,
            outputs=outputs,
            reuse_targets=skill.reuse_targets if skill else [],
        )
    )


def execute_timeline_render(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    timeline = _current_timeline(db, user, request)
    if timeline is None:
        return blocked_result(
            request,
            title="Render 等待当前 Timeline",
            detail="需要先绑定剧本并完成 Timeline Skill。",
            required_inputs=["script_id", "timeline"],
        )
    readiness = TimelineResolvedVideoService(db).list_resolved_videos(
        timeline.id,
        user,
    )
    if not readiness.ready:
        return blocked_result(
            request,
            title="Render 等待片段视频",
            detail=(
                f"当前 {readiness.video_clip_count} 个视频片段中，"
                f"缺失 {readiness.missing_clip_count} 个，"
                f"生成中 {readiness.generating_clip_count} 个。"
            ),
            required_inputs=["timeline_clip_videos"],
        )
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    service = TimelineService(db)
    payload = RenderJobCreate(
        timeline_version=timeline.version,
        render_type="final",
        preset={
            "fps": spec.get("fps") or 24,
            "resolution": spec.get("resolution") or "1080x1920",
        },
    )
    job = service.queue_render_job(timeline.id, payload, user)
    if job.status in {"failed", "cancelled"}:
        job = service.queue_render_job(
            timeline.id,
            payload.model_copy(update={"force_new_attempt": True}),
            user,
        )
    return _job_response(request, job, skill_id="timeline.render")


def execute_timeline_export(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    timeline = _current_timeline(db, user, request)
    if timeline is None:
        return blocked_result(
            request,
            title="Export 等待当前 Timeline",
            detail="需要先绑定剧本并完成 Timeline Skill。",
            required_inputs=["script_id", "timeline"],
        )
    jobs = TimelineService(db).list_render_jobs(timeline.id, user)
    job = next(
        (
            item
            for item in jobs
            if item.timeline_version == timeline.version and item.render_type == "final"
        ),
        None,
    )
    if job is None:
        return blocked_result(
            request,
            title="Export 等待最终渲染",
            detail="请先执行 Render Skill 生成当前 Timeline 版本的成片。",
            required_inputs=["final_render_job"],
        )
    return _job_response(request, job, skill_id="timeline.export")
