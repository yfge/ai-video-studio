from __future__ import annotations

from app.models.user import User
from app.repositories.task_repository import TaskRepository
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
from app.services.production_canvas.reference_artifacts import (
    resolve_canvas_reference_artifacts,
)
from app.services.storyboard.storyboard_image_autogen import (
    queue_storyboard_image_generation,
)
from app.services.storyboard.video_generation_queue import (
    queue_storyboard_video_generation_task,
)
from sqlalchemy.orm import Session

from .candidate_branch_context import resolve_canvas_candidate_branch


def execute_storyboard_images(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("image.candidates")
    script = load_script(db, user, request.script_id)
    if script is None:
        return blocked_result(
            request,
            title="Image Candidates 等待剧本上下文",
            detail="需要先绑定 script_id，之后才会提交现有 STORYBOARD_IMAGE_GENERATION 任务。",
            required_inputs=["script_id"],
        )

    branch = resolve_canvas_candidate_branch(db, user, request, media_type="image")
    references = resolve_canvas_reference_artifacts(
        db,
        user,
        request.reference_artifacts,
    )
    reference_images = list(references.image_urls)
    if branch and branch.candidate.url not in reference_images:
        reference_images.append(branch.candidate.url)
    queue_result = queue_storyboard_image_generation(
        db,
        script_id=script.id,
        user_id=user.id,
        frame_indexes=(
            [branch.candidate.frame_index]
            if branch
            else request.frame_indexes if request.frame_indexes is not None else [0]
        ),
        model=request.model,
        aspect_ratio=request.aspect_ratio,
        reference_images=reference_images,
        require_reference_images=(
            request.require_reference_images
            if request.require_reference_images is not None
            else True
        ),
        prompt=branch.prompt if branch else None,
        canvas_branch=branch.metadata if branch else None,
    )
    if queue_result.child_task_id is None:
        return blocked_result(
            request,
            title="Image Candidates 等待可生成分镜",
            detail=(
                "现有分镜图片队列已检查剧本，但没有可提交的参考图分镜。"
                f" reason={queue_result.reason or 'no_eligible_frames'}"
            ),
            required_inputs=["storyboard_frames", "reference_images"],
        )

    task = TaskRepository(db).get_by_id(queue_result.child_task_id)
    if task and request.run_id:
        task.target_business_id = request.run_id
        db.add(task)
        db.commit()
        db.refresh(task)

    task_status = task.status.value if task else "pending"
    return ProductionCanvasSkillExecuteResponse(
        task_id=queue_result.child_task_id,
        task_status=task_status,
        skill_result=ProductionCanvasSkillResult(
            skill="image.candidates",
            label=skill.label if skill else "Image Candidates",
            status="running",
            title="已提交现有分镜图片候选任务",
            detail="后台已通过现有 STORYBOARD_IMAGE_GENERATION worker 执行。",
            outputs={
                "script_id": script.id,
                "episode_id": script.episode_id,
                "dispatched_task_id": queue_result.child_task_id,
                "task_status": task_status,
                "queued_frame_indexes": queue_result.queued_frame_indexes,
                "queued_frame_count": len(queue_result.queued_frame_indexes),
                "skipped_frame_indexes": queue_result.skipped_frame_indexes,
                "model": request.model,
                "aspect_ratio": request.aspect_ratio,
                "reference_artifacts": references.artifacts,
                "reference_image_count": len(reference_images),
                "unresolved_reference_artifacts": references.unresolved,
                "require_reference_images": queue_result.require_reference_images,
                **(
                    {
                        "branch_parent_candidate_id": branch.candidate.asset_id,
                        "branch_task_id": queue_result.child_task_id,
                        "branch_frame_index": branch.candidate.frame_index,
                        "branch_instruction": branch.instruction,
                    }
                    if branch
                    else {}
                ),
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
            reuse_targets=skill.reuse_targets if skill else [],
        ),
    )


def execute_storyboard_video_candidates(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
) -> ProductionCanvasSkillExecuteResponse:
    skill = skill_definition("video.candidates")
    script = load_script(db, user, request.script_id)
    if script is None:
        return blocked_result(
            request,
            title="Video Candidates 等待剧本上下文",
            detail="需要先绑定 script_id，之后才会提交现有 VIDEO_GENERATION 任务。",
            required_inputs=["script_id"],
        )

    branch = resolve_canvas_candidate_branch(db, user, request, media_type="video")
    try:
        queue_result = queue_storyboard_video_generation_task(
            db,
            user,
            script,
            prompt=branch.prompt if branch else None,
            frame_indexes=(
                [branch.candidate.frame_index]
                if branch
                else request.frame_indexes if request.frame_indexes is not None else [0]
            ),
            model=request.model,
            duration=request.duration,
            fps=request.fps,
            resolution=request.resolution,
            ratio=request.ratio,
            camera_fixed=request.camera_fixed,
            start_frame_url=None if branch else request.start_frame_url,
            target_business_id=request.run_id,
            canvas_branch=branch.metadata if branch else None,
        )
    except ValueError as exc:
        reason = str(exc)
        if reason == "no_storyboard_frames":
            return blocked_result(
                request,
                title="Video Candidates 等待分镜帧",
                detail="需要先生成 storyboard.frames，之后才会提交现有视频候选任务。",
                required_inputs=["storyboard_frames"],
            )
        if reason in {"timeline_not_found", "timeline_clip_mapping_missing"}:
            return blocked_result(
                request,
                title="Video Candidates 等待当前 Timeline clips",
                detail=(
                    "需要先执行 Timeline Skill，并确保 storyboard 支撑帧来自当前 "
                    f"Timeline 版本。 reason={reason}"
                ),
                required_inputs=["timeline_clips", "storyboard_support_frames"],
            )
        if reason == "start_frame_requires_single_frame":
            return blocked_result(
                request,
                title="Video Candidates 需要单一目标镜头",
                detail="选用图片只能绑定一个 frame index，请先在节点中指定单一媒体帧。",
                required_inputs=["frame_indexes"],
            )
        raise

    task = queue_result.task
    return ProductionCanvasSkillExecuteResponse(
        task_id=task.id,
        task_status=task.status.value,
        skill_result=ProductionCanvasSkillResult(
            skill="video.candidates",
            label=skill.label if skill else "Video Candidates",
            status="running",
            title="已提交现有分镜视频候选任务",
            detail="后台已通过现有 VIDEO_GENERATION storyboard worker 执行。",
            outputs={
                "script_id": script.id,
                "episode_id": script.episode_id,
                "dispatched_task_id": task.id,
                "task_status": task.status.value,
                "frame_count": queue_result.frame_count,
                "selected_candidate_count": queue_result.selected_candidate_count,
                "timeline_id": queue_result.timeline_id,
                "timeline_version": queue_result.timeline_version,
                "mapped_clip_count": queue_result.mapped_clip_count,
                "frame_indexes": (
                    [branch.candidate.frame_index] if branch else request.frame_indexes
                ),
                "model": request.model,
                "duration": request.duration,
                "fps": request.fps,
                "resolution": request.resolution,
                "ratio": request.ratio,
                "camera_fixed": request.camera_fixed,
                "start_frame_url": None if branch else request.start_frame_url,
                **(
                    {
                        "branch_parent_candidate_id": branch.candidate.asset_id,
                        "branch_task_id": task.id,
                        "branch_frame_index": branch.candidate.frame_index,
                        "branch_instruction": branch.instruction,
                    }
                    if branch
                    else {}
                ),
                **({"canvas_run_id": request.run_id} if request.run_id else {}),
            },
            reuse_targets=skill.reuse_targets if skill else [],
        ),
    )
