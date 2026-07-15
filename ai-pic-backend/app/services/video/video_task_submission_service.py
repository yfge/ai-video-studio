from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.task import Task, TaskStatus
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.repositories.script_repository import ScriptRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.video_generation_task_repository import (
    VideoGenerationTaskRepository,
)
from app.services.video.video_task_dispatcher import VideoTaskDispatcher
from app.services.video.video_task_submission_helpers import (
    resolve_target_duration_seconds,
    submit_provider_task,
)
from app.services.video.video_task_submission_persistence import (
    persist_failed_video_task,
    persist_submitted_video_task,
)
from app.services.video.video_task_utils import (
    abs_url,
    build_selection_map,
    coerce_duration,
    normalize_submission_options,
    resolve_frame_urls,
    resolve_prompt,
)


class VideoTaskSubmissionService:
    def __init__(self, db, ai_manager):
        self.db = db
        self.repo = VideoGenerationTaskRepository(db)
        self.dispatcher = VideoTaskDispatcher(ai_manager)

    def submit_storyboard_video_tasks(
        self,
        *,
        task_id: int,
        script_id: int,
        frame_indexes: Optional[List[int]],
        selections: Optional[List[Dict[str, Any]]],
        options: Optional[Dict[str, Any]],
    ) -> None:
        task = self._load_task(task_id)
        frames = self._load_storyboard_frames(script_id)
        target_indexes = self._resolve_target_indexes(frame_indexes, frames)
        selection_by_index = build_selection_map(selections)
        opts = normalize_submission_options(options)

        submitted = 0
        failures: list[str] = []
        for idx in target_indexes:
            existing = self.repo.get_latest_for_task_frame(
                task_id=task.id,
                frame_index=idx,
            )
            if existing:
                submitted_one, error = self._reuse_existing_frame(existing, idx)
            else:
                submitted_one, error = self._submit_frame(
                    task,
                    script_id,
                    idx,
                    frames,
                    selection_by_index,
                    opts,
                )
            if submitted_one:
                submitted += 1
            if error:
                failures.append(error)
            self.db.commit()

        self._finalize_submission(task, submitted, failures)

    @staticmethod
    def _reuse_existing_frame(existing, frame_index: int) -> tuple[bool, str | None]:
        if existing.status in {
            VideoGenerationTaskStatus.FAILED,
            VideoGenerationTaskStatus.TIMEOUT,
        }:
            detail = existing.error_message or existing.status.value
            return False, f"frame {frame_index}: {detail}"
        return True, None

    def _load_task(self, task_id: int) -> Task:
        task = TaskRepository(self.db).get_by_id(task_id)
        if not task:
            raise RuntimeError("任务不存在")
        task.status = TaskStatus.PROCESSING
        self.db.commit()
        return task

    def _load_storyboard_frames(self, script_id: int) -> List[Dict[str, Any]]:
        script = ScriptRepository(self.db).get_by_id(script_id)
        if not script:
            raise RuntimeError("剧本不存在")
        storyboard = (script.extra_metadata or {}).get("storyboard") or {}
        frames_src = list(storyboard.get("frames") or [])
        if not frames_src:
            raise RuntimeError("未找到分镜数据")
        return [dict(fr) if isinstance(fr, dict) else {} for fr in frames_src]

    def _resolve_target_indexes(
        self, frame_indexes: Optional[List[int]], frames: List[Dict[str, Any]]
    ) -> List[int]:
        return frame_indexes or list(range(len(frames)))

    def _submit_frame(
        self,
        task: Task,
        script_id: int,
        frame_index: int,
        frames: List[Dict[str, Any]],
        selection_by_index: Dict[int, Dict[str, Any]],
        opts: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        if frame_index < 0 or frame_index >= len(frames):
            return False, None
        frame = frames[frame_index]
        selection = selection_by_index.get(frame_index) or {}
        start_url, end_url, error = resolve_frame_urls(
            frame, selection, opts["use_end_frame"]
        )
        if error:
            self._record_failure(task, script_id, frame_index, error)
            return False, f"frame {frame_index}: {error}"

        prompt_value = resolve_prompt(frame, opts.get("prompt"))
        target_duration_seconds = resolve_target_duration_seconds(frame, opts)
        request_duration_seconds = coerce_duration(target_duration_seconds)
        reference_images: list[str] | None = None
        raw_refs = frame.get("reference_images")
        if isinstance(raw_refs, list):
            reference_images = [
                abs_url(str(item))
                for item in raw_refs
                if isinstance(item, str) and item.strip()
            ] or None

        try:
            response = submit_provider_task(
                self.dispatcher,
                prompt=prompt_value,
                start_url=start_url,
                end_url=end_url,
                reference_images=reference_images,
                duration=request_duration_seconds,
                opts=opts,
            )
        except Exception as exc:
            error_message = f"视频任务提交异常: {exc}"
            self._record_failure(task, script_id, frame_index, error_message)
            return False, f"frame {frame_index}: {error_message}"
        if not response.success:
            self._record_failure(task, script_id, frame_index, response.error)
            return False, f"frame {frame_index}: {response.error}"

        provider_task_id = (response.data or {}).get("task_id")
        if not provider_task_id:
            self._record_failure(task, script_id, frame_index, "未返回任务ID")
            return False, f"frame {frame_index}: 未返回任务ID"

        provider_duration_seconds = int(
            (response.data or {}).get("duration") or request_duration_seconds
        )
        persist_submitted_video_task(
            self.repo,
            task=task,
            script_id=script_id,
            frame_index=frame_index,
            response=response,
            prompt=prompt_value,
            start_url=start_url,
            end_url=end_url,
            reference_images=reference_images,
            target_duration_seconds=target_duration_seconds,
            provider_duration_seconds=provider_duration_seconds,
            opts=opts,
        )
        return True, None

    def _finalize_submission(
        self, task: Task, submitted: int, failures: List[str]
    ) -> None:
        if submitted == 0:
            error_msg = "未生成任何视频" + (f"：{failures[0]}" if failures else "")
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            self.db.commit()
            raise RuntimeError(error_msg)
        if failures:
            task.error_message = "; ".join(failures[:5])
            self.db.commit()

    def _record_failure(
        self,
        task: Task,
        script_id: int,
        frame_index: int,
        error_message: str,
    ) -> None:
        persist_failed_video_task(
            self.repo,
            task=task,
            script_id=script_id,
            frame_index=frame_index,
            error_message=error_message,
        )
