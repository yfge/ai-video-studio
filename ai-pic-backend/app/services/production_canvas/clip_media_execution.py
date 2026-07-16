from __future__ import annotations

from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.production_canvas import (
    ProductionCanvasSkillExecuteRequest,
    ProductionCanvasSkillExecuteResponse,
    ProductionCanvasSkillResult,
)
from app.schemas.timeline import (
    TimelineClipStoryboardGenerateRequest,
    TimelineClipVideoReworkTaskRequest,
)
from app.services.production_canvas.execution_common import (
    blocked_result,
    skill_definition,
)
from app.services.production_canvas.reference_artifacts import (
    resolve_canvas_reference_artifacts,
)
from app.services.storyboard.grid_storyboard_sheet_service import (
    GridStoryboardSheetService,
)
from app.services.timeline_clip_video_rework_queue_service import (
    TimelineClipVideoReworkQueueService,
)
from sqlalchemy.orm import Session


def _retarget_task(db: Session, task_id: int, run_id: str | None):
    task = TaskRepository(db).get_by_id(task_id)
    if task is not None and run_id:
        task.target_business_id = run_id
        db.add(task)
        db.commit()
        db.refresh(task)
    return task


def _missing_clip_context(request: ProductionCanvasSkillExecuteRequest) -> list[str]:
    missing = []
    if request.timeline_id is None:
        missing.append("timeline_id")
    if request.timeline_version is None:
        missing.append("timeline_version")
    if request.clip_id is None:
        missing.append("clip_id")
    return missing


def execute_clip_storyboard_candidates(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("storyboard.candidates")
    missing = _missing_clip_context(request)
    if missing:
        return blocked_result(
            request,
            title="Clip Storyboard 等待 Timeline 分镜",
            detail="需要先绑定当前 Timeline version 与 stable clip_id。",
            required_inputs=missing,
        )
    references = resolve_canvas_reference_artifacts(
        db,
        user,
        request.reference_artifacts,
        virtual_ip_id=request.virtual_ip_id,
        environment_id=request.environment_id,
    )
    queued = GridStoryboardSheetService(db).queue_clip_sheet(
        int(request.timeline_id),
        str(request.clip_id),
        TimelineClipStoryboardGenerateRequest(
            expected_version=int(request.timeline_version),
            model=request.model or "codex:gpt-image-2",
            reference_images=references.image_urls,
            character_virtual_ip_ids=(
                [request.virtual_ip_id] if request.virtual_ip_id else None
            ),
        ),
        user,
    )
    task = _retarget_task(db, queued.task_id, request.run_id)
    task_status = task.status.value if task else queued.status
    return ProductionCanvasSkillExecuteResponse(
        task_id=queued.task_id,
        task_status=task_status,
        skill_result=ProductionCanvasSkillResult(
            skill="storyboard.candidates",
            label=skill.label if skill else "Clip Storyboard Candidates",
            status="running",
            title="已提交剪辑级故事板候选任务",
            detail="按镜头时长自动选择 2/4/6/9 格，并生成单张时序故事板。",
            outputs={
                "timeline_id": request.timeline_id,
                "timeline_version": request.timeline_version,
                "clip_id": request.clip_id,
                "dispatched_task_id": queued.task_id,
                "task_status": task_status,
                "panel_count_mode": "auto",
                "panel_count_options": [2, 4, 6, 9],
                "reference_artifacts": references.artifacts,
                "reference_image_count": len(references.image_urls),
                "unresolved_reference_artifacts": references.unresolved,
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
            reuse_targets=skill.reuse_targets if skill else [],
        ),
    )


def execute_clip_storyboard_video_candidates(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("video.candidates")
    missing = _missing_clip_context(request)
    storyboard_url = next(
        (
            item.strip()
            for item in request.reference_artifacts
            if isinstance(item, str) and item.strip()
        ),
        None,
    )
    if storyboard_url is None:
        missing.append("approved_storyboard")
    if missing:
        return blocked_result(
            request,
            title="Video Candidates 等待选用故事板",
            detail="视频候选只消费已人工选用的 clip storyboard sheet。",
            required_inputs=missing,
        )
    queued = TimelineClipVideoReworkQueueService(db).queue_video_rework(
        int(request.timeline_id),
        str(request.clip_id),
        TimelineClipVideoReworkTaskRequest(
            expected_version=int(request.timeline_version),
            prompt=None,
            model=request.model,
            duration=request.duration,
            fps=request.fps or 24,
            resolution=request.resolution or "720p",
            ratio=request.ratio,
            use_end_frame=False,
            return_last_frame=False,
            reference_mode="clip_storyboard_sheet",
            use_clip_storyboard=True,
            auto_render=False,
            operator_reviewed=True,
            reference_images=[storyboard_url],
        ),
        user,
    )
    task = _retarget_task(db, queued.task_id, request.run_id)
    task_status = task.status.value if task else queued.status
    return ProductionCanvasSkillExecuteResponse(
        task_id=queued.task_id,
        task_status=task_status,
        skill_result=ProductionCanvasSkillResult(
            skill="video.candidates",
            label=skill.label if skill else "Video Candidates",
            status="running",
            title="已提交故事板驱动的视频候选任务",
            detail="使用整张 clip storyboard sheet；不使用首帧、尾帧，也不提前渲染。",
            outputs={
                "timeline_id": request.timeline_id,
                "timeline_version": request.timeline_version,
                "clip_id": request.clip_id,
                "dispatched_task_id": queued.task_id,
                "task_status": task_status,
                "reference_mode": "clip_storyboard_sheet",
                "approved_storyboard": storyboard_url,
                "uses_start_frame": False,
                "uses_end_frame": False,
                "placement_mode": "explicit_node",
                "candidate_branching": "disabled",
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
            reuse_targets=skill.reuse_targets if skill else [],
        ),
    )
